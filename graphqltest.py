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

import csv
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

USAGE = "Usage: {} csvFile [uploadGcp(true|false)]".format(sys.argv[0])

graphiteReporter = GraphiteReporter()

if 'GRAPHQL_ENDPOINT' not in os.environ:
    graphqlEndpoint = 'https://api.entur.org/journeyplanner/1.1/index/graphql'
else:
    graphqlEndpoint = os.environ["GRAPHQL_ENDPOINT"]

client = GraphQLClient(graphqlEndpoint)

TIME = "06:00"

def roundTwoDecimals(value):
    return round(value, 2)


def run(csvFile, uploadGcp):
    searches = csvloader.loadCsv(csvFile)

    print("loaded {numberOfSearches} searches from file".format(numberOfSearches=len(searches)))

    count = 0
    successCount = 0
    failed = 0
    failedSearches = []

    time1 = time.time()

    for search in searches:
        count += 1
        date = time.strftime("%Y-%m-%d")

        query = travelsearch.createQuery(search, date, TIME)
        try:
            print("Executing search {}: {} -> {} ".format(count, search["fromPlace"], search["toPlace"]))
            result = client.execute(query)
            jsonResponse = json.loads(result)

            if not jsonResponse["data"]["plan"]["itineraries"]:
                failedSearches.append({"search": search, "otpQuery": query, "response": result})
            else:
                successCount += 1
        except Exception as exception:
            failMessage = str(exception)
            print("Caught exception: " + failMessage)
            result = str(exception.read())
            print("Adding failmessage and reponse to report {}: {}".format(failMessage, result))

            failedSearches.append({"search": search, "otpQuery": query, "failMessage": failMessage, "response": result})

    spent = roundTwoDecimals(time.time() - time1)
    average = roundTwoDecimals(spent / count)
    failedCount = len(failedSearches)
    failedPercentage = failedCount / count * 100

    report = {
        "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "failedPercentage": failedPercentage,
        "numberOfSearches": count,
        "secondsTotal": spent,
        "secondsAverage": average,
        "successCount": successCount,
        "failedCount": failedCount,
        "failedSearches": failedSearches
    }

    graphiteReporter.reportToGraphite([
        ('search.count', count),
        ('search.success.count', successCount),
        ('search.seconds.total', spent),
        ('search.seconds.average', average),
        ('search.failed.count', failedCount)
    ])

    jsonReport = json.dumps(report)
    fileName = reportdao.saveJsonReport(jsonReport)

    if (uploadGcp):
        gcpuploader.uploadBlob(os.environ["BUCKET_NAME"], fileName, os.environ["DESTINATION_BLOB_NAME"])
        # Only notify hubot if uploaded to gcp

    if 'NOTIFY_HUBOT' in os.environ and bool(os.environ["NOTIFY_HUBOT"]) is True:
        print("notify hubot?: " + os.environ["NOTIFY_HUBOT"])
        hubotnotifier.notifyIfNecesarry(report)


if len(sys.argv) == 1:
    print(USAGE)
    sys.exit(1)

csvFile = sys.argv[1]

if len(sys.argv) == 3:
    uploadGcp = sys.argv[2] == 'True'
else:
    uploadGcp = False;

if uploadGcp:
    if ('BUCKET_NAME' not in os.environ or 'DESTINATION_BLOB_NAME' not in os.environ):
        raise ValueError("Environment variables required: BUCKET_NAME and DESTINATION_BLOB_NAME")

run(csvFile, uploadGcp)
