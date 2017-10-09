from graphqlclient import GraphQLClient
import time
import json
import datetime
from json2html import *
import csv

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

def createHtmlReport(jsonReport) :
    print("creating html report")
    htmlReport = json2html.convert(json = jsonReport)

    html="""
    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0-beta/css/bootstrap.min.css" integrity="sha384-/Y6pD6FV/Vv2HJnA6t+vslU6fwYXjCFtcEpHbNJ0lyAFsXTsjBbfaDjzALeQsN6M" crossorigin="anonymous">
    </head>
    <body>
        {content}
    </body>
    </html>
    """.format(content=htmlReport)

    htmlFooter="</body></footer>"

    text_file = open("Report.html", "w")
    text_file.write(html)
    text_file.close()

def loadCsv() :
    with open('endpoints_custom_entur_from_to.csv') as file:
        searches = [{k: v for k, v in row.items()}
            for row in csv.DictReader(file, skipinitialspace=True)]
        print(searches)
        return searches

def run():

    searches = loadCsv()

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

            if not jsonResponse["data"]["plan"]["itineraries"]:
                failedSearches.append({"search": search, "otpQuery": query, "response": result})
        except Exception as exception:
            print((exception))
            print('')
            failedSearches.append({"search": search, "otpQuery": query, "expection": exception})


    spent = time.time()-time1
    average=spent/count
    failedCount=len(failedSearches)
    failedPercentage=failedCount/count

    report = {
        "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "failedPercentage": "{:.1%}".format(failedPercentage),
        "numberOfSearches": count,
        "secondsTotal": spent,
        "secondsAverage": average,
        "failedCount": failedCount,
        "failedSearches": failedSearches
    }

    jsonReport = json.dumps(report)
    createHtmlReport(jsonReport)

run()
