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
import logging



class TravelSearchExecutor:
    def __init__(self, client, prometheus_reporter):
        self.client = client
        self.prometheus_reporter = prometheus_reporter
        self.log = logging.getLogger(__file__)

    def create_query(self, search, dateTime):
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
        successful_search_times = []
        start_time_all_tests = time.time()

        for travel_search in travel_searches:
            count += 1

            operator = travel_search["description"]

            query = self.create_query(travel_search, dateTime)
            start_time = time.time()

            try:
                self.log.info("Executing search {}: {} -> {} ".format(count, travel_search["fromPlace"],
                                                              travel_search["toPlace"]))

                result = self.client.execute(query)

                raw_time_spent = time.time() - start_time
                time_spent = round(raw_time_spent, 2)

                json_response = json.loads(result)

                if not json_response["data"]["trip"]["tripPatterns"]:
                    failed_searches.append({"search": travel_search, "otpquery": query, "response": result, "executionTime": time_spent})
                    self.prometheus_reporter.report_travel_search(operator=operator, success=False, time_spent=time_spent)
                else:
                    success_count += 1
                    successful_searches.append({"search": travel_search, "otpquery": query, "response": result, "executionTime": time_spent})
                    successful_search_times.append(raw_time_spent)
                    self.prometheus_reporter.report_travel_search(operator=operator, success=True, time_spent=time_spent)
            except GraphQLException as exception:
                self.log.info("adding failMessage and response to report '{}': '{}'".format(exception.message, exception.body))

                time_spent = round(time.time() - start_time, 2)
                failed_searches.append(
                    {"search": travel_search, "otpQuery": query, "failMessage": exception.message, "response": exception.body, "executionTime": time_spent})
                self.prometheus_reporter.report_travel_search(operator=operator, success=False, time_spent=time_spent)
            except Exception as exception:
                self.log.warn("encountered unhandled exception: '{}'".format(exception))

        total_time_spent = round(time.time() - start_time_all_tests, 2)
        failed_count = len(failed_searches)
        failed_percentage = failed_count / count * 100

        average = round(sum(successful_search_times) / len(successful_search_times), 2)
        average_old = round(total_time_spent / count, 2)

        self.log.info('Average execution time successful searches: ' + str(average))
        self.log.info('Average execution time all searches: ' + str(average_old))

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

        self.prometheus_reporter.report_travel_search_request_durations(total_time_spent, average)
        self.prometheus_reporter.push_search_to_gateway()

        return report
