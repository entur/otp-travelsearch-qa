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

import travelsearch
import reportdao
import csvloader

from graphitereporter import GraphiteReporter
from graphqlclient import GraphQLClient

usage = "usage: {} csvfile [uploadgcp(true|false)]".format(sys.argv[0])

graphitereporter = GraphiteReporter()

if 'graphql_endpoint' not in os.environ:
    graphqlendpoint = 'https://api.entur.org/journeyplanner/1.1/index/graphql'
else:
    graphqlendpoint = os.environ["graphql_endpoint"]

client = GraphQLClient(graphqlendpoint)

TIME = "06:00"

def round_two_decimals(value):
    return round(value, 2)


def run(csv_file, upload_gcp):
    travel_searches = csvloader.load_csv(csv_file)

    print("loaded {number_of_searches} searches from file".format (number_of_searches=len(travel_searches)))

    count = 0
    success_count = 0
    failed = 0
    failed_searches = []

    start_time = time.time()

    for travel_search in travel_searches:
        count += 1
        date = time.strftime("%y-%m-%d")

        query = travelsearch.create_query(travel_search, date, time)
        try:
            print("Executing search {}: {} -> {} ".format(count, travel_search["fromPlace"], travel_search["toPlace"]))
            result = client.execute(query)
            json_response = json.loads(result)

            if not json_response["data"]["plan"]["itineraries"]:
                failed_searches.append({"search": travel_search, "otpquery": query, "response": result})
            else:
                success_count += 1
        except Exception as exception:
            fail_message = str(exception)
            print("caught exception: " + fail_message)
            result = str(exception.read())
            print("adding failmessage and reponse to report {}: {}".format(fail_message, result))

            failed_searches.append({"search": travel_search, "otpquery": query, "fail_message": fail_message, "response": result})

    spent = round_two_decimals(time.time() - start_time)
    average = round_two_decimals(spent / count)
    failed_count = len(failed_searches)
    failed_percentage = failed_count / count * 100

    report = {
        "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "failedPercentage": failed_percentage,
        "numberOfSearches": count,
        "secondsTotal": spent,
        "secondsAverage": average,
        "successCount": success_count,
        "failedCount": failed_count,
        "failedSearches": failed_searches
    }

    graphitereporter.report_to_graphite([
        ('search.count', count),
        ('search.success.count', success_count),
        ('search.seconds.total', spent),
        ('search.seconds.average', average),
        ('search.failed.count', failed_count)
    ])

    json_report = json.dumps(report)
    filename = reportdao.save_json_report(json_report)

    if (upload_gcp):
        gcpuploader.upload_blob(os.environ["bucket_name"], filename, os.environ["destination_blob_name"])
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
