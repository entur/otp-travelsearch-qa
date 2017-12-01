# Licensed under the EUPL, Version 1.2 or – as soon they will be approved by
# the European Commission - subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
#
#   https://joinup.ec.europa.eu/software/page/eupl
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and
# limitations under the Licence.

import datetime
import json
import os
import sys
import time

import csvloader
import gcpuploader
import hubotnotifier
import reportdao
from graphitereporter import GraphiteReporter
from graphqlclient import GraphQLClient
from stoptimesexecutor import StopTimesExecutor
from travelsearchexecutor import TravelSearchExecutor

HOUR = 6
MINUTE = 0
TIME = "06:00"
USAGE = "usage: {} csvfile [uploadgcp(true|false)]".format(sys.argv[0])

GRAPHQL_ENDPOINT_ENV = "GRAPHQL_ENDPOINT"
STOP_TIMES_FILE_ENV = "STOP_TIMES_FILE"
NOTIFY_HUBOT_ENV = "NOTIFY_HUBOT"
BUCKET_NAME_ENV = "BUCKET_NAME"
DESTINATION_BLOB_NAME_ENV = "DESTINATION_BLOB_NAME"

DEFAULT_GRAPHQL_ENDPOINT = "https://api.entur.org/journeyplanner/1.1/index/graphql"
DEFAULT_STOP_TIMES_FILE = "stops.csv"


def get_env(key, default_value):
    if key not in os.environ:
        return default_value
    else:
        return os.environ[key]


def env_is_true(key):
    if key in os.environ and bool(os.environ[key] is True):
        print("Got " + key + ": True")
        return True
    return False


def round_two_decimals(value):
    return round(value, 2)


def run(travel_search_file, stop_times_file, upload_gcp):
    stops = csvloader.load_csv(stop_times_file)
    print("loaded {number_of_searches} stops from file".format(number_of_searches=len(stops)))
    travel_searches = csvloader.load_csv(travel_search_file)
    print("loaded {number_of_searches} searches from file".format(number_of_searches=len(travel_searches)))

    report = {
        "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "stopTimes": stop_times_executor.run_stop_times_searches(stops),
        "travelSearch": travel_search_executor.run_travel_searches(travel_searches, TIME)
    }

    json_report = json.dumps(report)
    filename = reportdao.save_json_report(json_report)

    if (upload_gcp):
        gcpuploader.upload_blob(os.environ[BUCKET_NAME_ENV], filename, os.environ[DESTINATION_BLOB_NAME_ENV])
        # only notify hubot if uploaded to gcp

    if env_is_true(NOTIFY_HUBOT_ENV):
        print("notify hubot?: " + os.environ[NOTIFY_HUBOT_ENV])
        hubotnotifier.notify_if_necessary(report)


if len(sys.argv) == 1:
    print(USAGE)
    sys.exit(1)

travel_search_file = sys.argv[1]

if len(sys.argv) == 3:
    upload_gcp = sys.argv[2] == 'True'
else:
    upload_gcp = False

graphite_reporter = GraphiteReporter()

graphql_endpoint = get_env(GRAPHQL_ENDPOINT_ENV, DEFAULT_GRAPHQL_ENDPOINT)
stop_times_file = get_env(STOP_TIMES_FILE_ENV, DEFAULT_STOP_TIMES_FILE)

client = GraphQLClient(graphql_endpoint)

travel_search_executor = TravelSearchExecutor(client, graphite_reporter)
stop_times_executor = StopTimesExecutor(client, graphite_reporter, HOUR, MINUTE)

if upload_gcp:
    if (BUCKET_NAME_ENV not in os.environ or DESTINATION_BLOB_NAME_ENV not in os.environ):
        raise ValueError("Environment variables required: BUCKET_NAME and DESTINATION_BLOB_NAME")

run(travel_search_file, stop_times_file, upload_gcp)
