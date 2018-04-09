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
    def __init__(self, client, graphite_reporter, travel_search_date):
        self.client = client
        self.graphite_reporter = graphite_reporter
        self.travel_search_date = travel_search_date

    def run_stop_times_searches(self, stops):

        test_start_time = time.time()
        count = 0
        success_count = 0
        failed_searches = []

        for stop in stops:
            count += 1

            try:
                print("Executing stop times request {}: {}".format(count, stop))


                variables = {
                    "startTime": self.travel_search_date,
                    "id": stop[STOP_ID_KEY]
                }

                result = self.client.execute(QUERY, variables)
                json_response = json.loads(result)

                if not json_response["data"]["stopPlace"]["estimatedCalls"]:
                    failed_searches.append(
                        {"search": stop, "otpQuery": QUERY, "otpVariables": variables, "response": result})
                else:
                    success_count += 1
            except TypeError as exception:
                fail_message = str(exception)
                failed_searches.append(
                    {"search": stop, "otpQuery": QUERY, "otpVariables": variables, "failMessage": fail_message,
                     "response": fail_message})

            except GraphQLException as exception:
                print("caught exception: " + exception.message)

                failed_searches.append(
                    {"search": stop, "otpQuery": QUERY, "otpVariables": variables, "failMessage": exception.message,
                     "response": exception.body})

        spent = round(time.time() - test_start_time, 2)
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
            ('stop.time.count', count),
            ('stop.time.success.count', success_count),
            ('stop.time.seconds.total', spent),
            ('stop.time.seconds.average', average),
            ('stop.time.failed.count', failed_count)
        ])

        return report
