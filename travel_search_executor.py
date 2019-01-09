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

import json
import time
from graphql_exception import GraphQLException


class TravelSearchExecutor:
    def __init__(self, client, graphite_reporter):
        self.client = client
        self.graphite_reporter = graphite_reporter

    def create_query(self, search, dateTime):
        if 'raptorRange' in search and 'raptorDays' in search:
            return """
                {{
                  trip(from: {{place: "{fromPlace}"}}, to: {{place: "{toPlace}"}}, dateTime: "{dateTime}", 
                  raptorSearchRange:{raptorRange}, raptorSearchDays:{raptorDays}) {{
                    tripPatterns {{
                      startTime
                      duration
                      walkDistance
                      legs {{
                        fromPlace {{
                          name
                          vertexType
                        }}
                        toPlace {{
                          name
                          vertexType
                        }}
                      }}
                    }}
                    messageEnums
                    messageStrings
                  }}
                }}
                """.format(fromPlace=search["fromPlace"], toPlace=search["toPlace"], dateTime=dateTime,
                           raptorRange=search["raptorRange"], raptorDays=search["raptorDays"])
        else:
            return """
            {{
              trip(from: {{place: "{fromPlace}"}}, to: {{place: "{toPlace}"}}, dateTime: "{dateTime}") {{
                tripPatterns {{
                  startTime
                  duration
                  walkDistance
                  legs {{
                    fromPlace {{
                      name
                      vertexType
                    }}
                    toPlace {{
                      name
                      vertexType
                    }}
                  }}
                }}
                messageEnums
                messageStrings
              }}
            }}
            """.format(fromPlace=search["fromPlace"], toPlace=search["toPlace"], dateTime=dateTime)

    def run_travel_searches(self, travel_searches, dateTime):

        count = 0
        success_count = 0
        failed_searches = []
        successful_searches = []
        start_time_all_tests = time.time()

        for travel_search in travel_searches:
            count += 1

            query = self.create_query(travel_search, dateTime)
            start_time = time.time()
            try:
                print("Executing search {}: {} -> {} ".format(count, travel_search["fromPlace"],
                                                              travel_search["toPlace"]), flush=True)

                result = self.client.execute(query)
                time_spent = round(time.time() - start_time, 2)

                json_response = json.loads(result)

                if not json_response["data"]["trip"]["tripPatterns"]:
                    failed_searches.append({"search": travel_search, "otpquery": query, "response": result, "executionTime": time_spent})
                else:
                    success_count += 1
                    successful_searches.append({"search": travel_search, "otpquery": query, "response": result, "executionTime": time_spent})
            except GraphQLException as exception:
                print("adding failMessage and response to report '{}': '{}'".format(exception.message, exception.body))

                time_spent = round(time.time() - start_time, 2)
                failed_searches.append(
                    {"search": travel_search, "otpQuery": query, "failMessage": exception.message, "response": exception.body, "executionTime": time_spent})

            self.graphite_reporter.report_to_graphite([
                ('search.seconds.each', time_spent)
            ])

        total_time_spent = round(time.time() - start_time_all_tests, 2)
        failed_count = len(failed_searches)
        failed_percentage = failed_count / count * 100
        average = round(total_time_spent / count, 2)

        report = {
            "failedPercentage": failed_percentage,
            "numberOfSearches": count,
            "successCount": success_count,
            "successfulSearches": successful_searches,
            "failedCount": failed_count,
            "failedSearches": failed_searches,
            "secondsAverage": average,
            "secondsTotal": total_time_spent
        }

        self.graphite_reporter.report_to_graphite([
            ('search.count', count),
            ('search.success.count', success_count),
            ('search.seconds.total', total_time_spent),
            ('search.seconds.average', average),
            ('search.failed.count', failed_count)
        ])

        return report
