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

import gcpuploader
import hubotnotifier


import reportdao
import csvloader

from graphitereporter import GraphiteReporter
from graphqlclient import GraphQLClient
from travelsearchexecutor import TravelSearchExecutor
from stoptimesexecutor import StopTimesExecutor

HOUR=6
MINUTE=0
TIME = "06:00"

usage = "usage: {} csvfile [uploadgcp(true|false)]".format(sys.argv[0])

graphite_reporter = GraphiteReporter()

if 'graphql_endpoint' not in os.environ:
    graphqlendpoint = 'https://api.entur.org/journeyplanner/1.1/index/graphql'
else:
    graphqlendpoint = os.environ["graphql_endpoint"]

client = GraphQLClient(graphqlendpoint)

travel_search_executor = TravelSearchExecutor(client, graphite_reporter)
stop_times_executor = StopTimesExecutor(client, graphite_reporter, HOUR, MINUTE)



def round_two_decimals(value):
    return round(value, 2)


def run(csv_file, upload_gcp):


    stops = csvloader.load_csv("stops.csv")
    print("loaded {number_of_searches} stops from file".format (number_of_searches=len(stops)))


    report = {
        "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    report["stopTimes"] = stop_times_executor.run_stop_times_searches(stops)

    travel_searches = csvloader.load_csv(csv_file)
    print("loaded {number_of_searches} searches from file".format (number_of_searches=len(travel_searches)))
    travel_search_report = travel_search_executor.run_travel_searches(travel_searches)
    report["travelSearch"] = travel_search_report

    # graphite_reporter.report_to_graphite([
    #     ('search.count', count),
    #     ('search.success.count', success_count),
    #     ('search.seconds.total', spent),
    #     ('search.seconds.average', average),
    #     ('search.failed.count', failed_count)
    # ])

    json_report = json.dumps(report)
    filename = reportdao.save_json_report(json_report)

    if (upload_gcp):
        gcpuploader.upload_blob(os.environ["BUCKET_NAME"], filename, os.environ["DESTINATION_BLOB_NAME"])
        # only notify hubot if uploaded to gcp

    if 'NOTIFY_HUBOT' in os.environ and bool(os.environ["NOTIFY_HUBOT"]) is True:
        print("notify hubot?: " + os.environ["NOTIFY_HUBOT"])
        hubotnotifier.notify_if_necessary(report)


if len(sys.argv) == 1:
    print(usage)
    sys.exit(1)

csv_file = sys.argv[1]

if len(sys.argv) == 3:
    upload_gcp = sys.argv[2] == 'True'
else:
    upload_gcp = False

if upload_gcp:
    if ('BUCKET_NAME' not in os.environ or 'DESTINATION_BLOB_NAME' not in os.environ):
        raise ValueError("Environment variables required: BUCKET_NAME and DESTINATION_BLOB_NAME")

run(csv_file, upload_gcp)
