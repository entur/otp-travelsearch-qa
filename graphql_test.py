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

import csv_loader
import gcp_uploader
import hubot_notifier
import report_dao
import time
from graphite_reporter import GraphiteReporter
from graphql_client import GraphQLClient
from stop_times_executor import StopTimesExecutor
from travel_search_executor import TravelSearchExecutor

HOUR = 6
MINUTE = 0
TIME = "06:00"
USAGE = "usage: {} endpoints_file [stoppoints_file]".format(sys.argv[0])

GRAPHQL_ENDPOINT_ENV = "GRAPHQL_ENDPOINT"
STOP_TIMES_FILE_ENV = "STOP_TIMES_FILE"
NOTIFY_HUBOT_ENV = "NOTIFY_HUBOT"
BUCKET_NAME_ENV = "BUCKET_NAME"
DESTINATION_BLOB_NAME_ENV = "DESTINATION_BLOB_NAME"
TRAVEL_SEARCH_DATE_TIME = "TRAVEL_SEARCH_DATE_TIME"

DEFAULT_GRAPHQL_ENDPOINT = "https://api.entur.io/journey-planner/v2/graphql"
DEFAULT_TRAVEL_SEARCH_DATE_TIME = datetime.datetime.today().replace(hour=6, minute=0, second=0).strftime('%Y-%m-%dT%H:%M:%S')


def get_env(key, default_value):
    if key not in os.environ:
        return default_value
    else:
        return os.environ[key]


def env_is_true(key):
    if key in os.environ and bool(os.environ[key]):
        print("Got " + key + ": True")
        return True
    return False


def get_arg(index):
    if not args_has_index(index):
        print("Could not find required argument at index {}".format(index))
        print(USAGE)
        sys.exit(1)

    return sys.argv[index]


def args_has_index(index):
    return len(sys.argv) > index


def get_arg_default_value(index, default_value):
    if args_has_index(index):
        return sys.argv[index]
    return default_value


def run(travel_search_date):
    report = {
        "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "travel_search_date": travel_search_date,
    }

    if stop_times_file is not None:
        stops = csv_loader.load_csv(stop_times_file)
        print("loaded {number_of_searches} stops from file".format(number_of_searches=len(stops)))
        report["stopTimes"] = stop_times_executor.run_stop_times_searches(stops)

    travel_searches = csv_loader.load_csv(travel_search_file)
    print("loaded {number_of_searches} searches from file".format(number_of_searches=len(travel_searches)))
    print("Running searches against endpoint " + graphql_endpoint)
    report["travelSearch"] = travel_search_executor.run_travel_searches(travel_searches, travel_search_date)

    json_report = json.dumps(report)
    filename = report_dao.save_json_report(json_report)

    if upload_gcp:
        gcp_uploader.upload_blob(os.environ[BUCKET_NAME_ENV], filename, os.environ[DESTINATION_BLOB_NAME_ENV])
        # Consider using constructor for gcp uploader
        gcp_uploader.remove_old_files(os.environ[BUCKET_NAME_ENV], os.environ[DESTINATION_BLOB_NAME_ENV])

    if env_is_true(NOTIFY_HUBOT_ENV):
        hubot_notifier.notify_if_necessary(report)


# required
travel_search_file = get_arg(1)

# optional
stop_times_file = get_arg_default_value(2, None)

graphite_reporter = GraphiteReporter()

graphql_endpoint = get_env(GRAPHQL_ENDPOINT_ENV, DEFAULT_GRAPHQL_ENDPOINT)

client = GraphQLClient(graphql_endpoint)

travel_search_date = get_env(TRAVEL_SEARCH_DATE_TIME, DEFAULT_TRAVEL_SEARCH_DATE_TIME)
print("Using datetime: " + travel_search_date)

travel_search_executor = TravelSearchExecutor(client, graphite_reporter)
stop_times_executor = StopTimesExecutor(client, graphite_reporter, travel_search_date)

if BUCKET_NAME_ENV not in os.environ or DESTINATION_BLOB_NAME_ENV not in os.environ:
    print("Environment variables not set: BUCKET_NAME and DESTINATION_BLOB_NAME. Will not upload reports to gcp")
    upload_gcp = False
else:
    upload_gcp = True

run(travel_search_date)
