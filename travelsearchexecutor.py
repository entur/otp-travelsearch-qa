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

import time
import json

class TravelSearchExecutor:
    def __init__(self, client, graphite_reporter):
        self.client = client
        self.graphite_reporter = graphite_reporter

    def create_query(self, search, date, time):
        return """
        {{
          plan(fromPlace: "{fromPlace}", toPlace: "{toPlace}", date: "{date}" time: "{time}") {{
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
            messageEnums
            messageStrings
          }}
        }}
        """.format(fromPlace=search["fromPlace"], toPlace=search["toPlace"], date=date, time=time)

    def run_travel_searches(self, travel_searches):

        count = 0
        success_count = 0
        failed_searches = []
        start_time = time.time()
        date = time.strftime("%y-%m-%d")

        for travel_search in travel_searches:
            count += 1

            query = self.create_query(travel_search, date, time)
            try:
                print("Executing search {}: {} -> {} ".format(count, travel_search["fromPlace"], travel_search["toPlace"]))
                result = self.client.execute(query)
                json_response = json.loads(result)

                if not json_response["data"]["plan"]["itineraries"]:
                    failed_searches.append({"search": travel_search, "otpquery": query, "response": result})
                else:
                    success_count += 1
            except Exception as exception:
                fail_message = str(exception)
                print("caught exception: " + fail_message)
                result = str(exception.read())
                print("adding failMessage and response to report {}: {}".format(fail_message, result))

                failed_searches.append({"search": travel_search, "otpQuery": query, "failMessage": fail_message, "response": result})


        spent = round(time.time() - start_time, 2)
        failed_count = len(failed_searches)
        failed_percentage = failed_count / count * 100
        average = round(spent / count, 2)

        report = {
            "failedPercentage": failed_percentage,
            "numberOfSearches": count,
            "successCount": success_count,
            "failedCount": failed_count,
            "failedSearches": failed_searches,
            "secondsAverage": average,
            "secondsTotal": spent
        }

        self.graphite_reporter.report_to_graphite([
            ('search.count', count),
            ('search.success.count', success_count),
            ('search.seconds.total', spent),
            ('search.seconds.average', average),
            ('search.failed.count', failed_count)
        ])


        return report