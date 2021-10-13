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
from datetime import datetime

from graphql_exception import GraphQLException

import logging

STOP_ID_KEY = "stopPlaceId"

QUERY = """
        query StopPage($id: String!, $startTime: DateTime!) {

          stopPlace(id: $id) {
            ...F1
          }
        }

        fragment F0 on EstimatedCall {
          realtimeState
          expectedDepartureTime
          actualDepartureTime
        }

        fragment F1 on StopPlace {
          estimatedCalls(startTime: $startTime, timeRange: 43200, numberOfDepartures: 10) {
            ...F0
          }
          id
        }
    """


class StopTimesExecutor:
    def __init__(self, client, prometheus_reporter, travel_search_date):
        self.client = client
        self.prometheus_reporter = prometheus_reporter
        self.travel_search_date = travel_search_date
        self.log = logging.getLogger(__file__)

    def run_stop_times_searches(self, stops):

        test_start_time = time.time()
        count = 0
        success_count = 0
        failed_searches = []
        successful_search_times = []

        for stop in stops:
            count += 1

            operator = stop["description"]

            start_time = time.time()

            try:
                self.log.info("Executing stop times request {}: {}".format(count, stop))


                variables = {
                    "startTime": self.travel_search_date,
                    "id": stop[STOP_ID_KEY]
                }

                result = self.client.execute(QUERY, variables)

                raw_time_spent = time.time() - start_time

                json_response = json.loads(result)

                if not json_response["data"]["stopPlace"]["estimatedCalls"]:
                    failed_searches.append(
                        {"search": stop, "otpQuery": QUERY, "otpVariables": variables, "response": result})
                    self.prometheus_reporter.report_stop_time(operator=operator, success=False)
                else:
                    success_count += 1
                    successful_search_times.append(raw_time_spent)
                    self.prometheus_reporter.report_stop_time(operator=operator, success=True)
            except GraphQLException as exception:
                self.log.info("caught exception: " + exception.message)

                failed_searches.append(
                    {"search": stop, "otpQuery": QUERY, "otpVariables": variables, "failMessage": exception.message,
                     "response": exception.body})
                self.prometheus_reporter.report_stop_time(operator=operator, success=False)
            except Exception as exception:
                fail_message = str(exception)
                failed_searches.append(
                    {"search": stop, "otpQuery": QUERY, "otpVariables": variables, "failMessage": fail_message,
                     "response": fail_message})
                self.prometheus_reporter.report_stop_time(operator=operator, success=False)

        spent = round(time.time() - test_start_time, 2)
        failed_count = len(failed_searches)
        failed_percentage = failed_count / count * 100

        if len(successful_search_times) != 0:
            average = round(sum(successful_search_times) / len(successful_search_times), 2)
        else:
            average = 0
        average_old = round(spent / count, 2)

        self.log.info('Average execution time successful stop time searches: ' + str(average))
        self.log.info('Average execution time all stop time searches: ' + str(average_old))

        report = {
            "failedPercentage": failed_percentage,
            "numberOfSearches": count,
            "successCount": success_count,
            "failedCount": failed_count,
            "failedSearches": failed_searches,
            "secondsAverage": average,
            "secondsTotal": spent
        }

        self.prometheus_reporter.report_stop_time_request_durations(spent, average)
        self.prometheus_reporter.push_stop_times_to_gateway()

        return report
