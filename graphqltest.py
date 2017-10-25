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

from graphqlclient import GraphQLClient
import time
import json
import datetime
import csv
import sys
import os
import gcpuploader
import hubotnotifier

USAGE = "Usage: {} csvFile [uploadGcp(true|false)]".format(sys.argv[0])

client = GraphQLClient('https://api.entur.org/journeyplanner/1.1/index/graphql')

def createQuery(search) :
    return """
    {{
      plan(fromPlace: "{fromPlace}", toPlace: "{toPlace}") {{
        itineraries {{

          startTime
          duration
          walkDistance
          legs {{
            from {{
              name
              vertexType
            }}
            to {{
              name
              vertexType
            }}
          }}
        }}
      }}
    }}
    """.format(fromPlace=search["fromPlace"], toPlace=search["toPlace"])

def saveJsonReport(jsonReport) :
    print("Saving json report")

    fileName = "test-report-{}.json".format(int(round(time.time() * 1000)))
    text_file = open(fileName, "w")
    text_file.write(jsonReport)
    text_file.close()
    print("Saved {}".format(fileName))
    return fileName

def loadCsv(csvFile) :
    with open(csvFile) as file:
        searches = [{k: v for k, v in row.items()}
            for row in csv.DictReader(file, skipinitialspace=True, delimiter=';')]
        return searches

def run(csvFile, uploadGcp):

    searches = loadCsv(csvFile)

    print("loaded {numberOfSearches} searches from file".format(numberOfSearches=len(searches)))

    count = 0
    failed = 0
    failedSearches=[]

    time1 = time.time()

    for search in searches:
        count += 1
        query = createQuery(search)
        try:
            result = client.execute(query)
            jsonResponse = json.loads(result)
            print("Executing search {}: {} -> {} ".format(count, search["fromPlace"], search["toPlace"]))

            if not jsonResponse["data"]["plan"]["itineraries"]:
                failedSearches.append({"search": search, "otpQuery": query, "response": result})
        except Exception as exception:
            print(exception)
            failedSearches.append({"search": search, "otpQuery": query, "expection": str(exception)})


    spent = time.time()-time1
    average=spent/count
    failedCount=len(failedSearches)
    failedPercentage=failedCount/count*100

    report = {
        "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "failedPercentage": failedPercentage,
        "numberOfSearches": count,
        "secondsTotal": spent,
        "secondsAverage": average,
        "failedCount": failedCount,
        "failedSearches": failedSearches
    }

    jsonReport = json.dumps(report)
    fileName = saveJsonReport(jsonReport)

    if(uploadGcp):
        gcpuploader.uploadBlob(os.environ["BUCKET_NAME"], fileName, os.environ["DESTINATION_BLOB_NAME"])
        # Only notify hubot if uploaded to gcp
        hubotnotifier.notifyIfNecesarry(report)

if(len(sys.argv) == 1):
    print(USAGE)
    sys.exit(1)

csvFile=sys.argv[1]

if(len(sys.argv) == 3):
    uploadGcp=sys.argv[2] == 'True'
else:
    uploadGcp = False;

if(uploadGcp):
    if('BUCKET_NAME' not in os.environ or 'DESTINATION_BLOB_NAME' not in os.environ):
        raise ValueError("Environment variables required: BUCKET_NAME and DESTINATION_BLOB_NAME")



run(csvFile, uploadGcp)
