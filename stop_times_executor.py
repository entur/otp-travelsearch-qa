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

from datetime import datetime
import time
import json

STOP_ID_KEY = "stopPlaceId"

QUERY = """
       query StopPage($id:String!,$startTime:Long!) {
        station(id:$id) {
            ...F1
        }
    }
    fragment F0 on Stoptime {
        realtimeState,
        realtimeDeparture,
        scheduledDeparture,
    }
    fragment F1 on Stop {
        stoptimesWithoutPatterns(
            startTime:$startTime,
            timeRange:43200,
            numberOfDepartures:10
        ) {...F0},
        id
    }
    """

class StopTimesExecutor:

    def __init__(self, client, graphite_reporter, hour, minute):
        self.client = client
        self.graphite_reporter = graphite_reporter
        self.hour = hour
        self.minute = minute


    def run_stop_times_searches(self, stops):

        test_start_time = time.time()
        count = 0
        success_count = 0
        failed_searches = []


        for stop in stops:
            count += 1

            try:
                print("Executing stop times request {}: {}".format(count, stop))
                start_time = int(time.mktime(datetime.now().replace(hour=self.hour, minute=self.minute).timetuple()))

                variables = {
                    "startTime": start_time,
                    "id": stop[STOP_ID_KEY]
                }

                result = self.client.execute(QUERY, variables)
                json_response = json.loads(result)

                if not json_response["data"]["station"]["stoptimesWithoutPatterns"]:
                    failed_searches.append({"search": stop, "otpQuery": QUERY, "otpVariables": variables, "response": result})
                else:
                    success_count += 1
            except TypeError as exception:
                fail_message = str(exception)
                failed_searches.append({"search": stop, "otpQuery": QUERY, "otpVariables": variables, "failMessage": fail_message, "response": fail_message})

            except Exception as exception:
                fail_message = str(exception)
                print("caught exception: " + fail_message)
                result = str(exception.read())
                failed_searches.append({"search": stop, "otpQuery": QUERY, "otpVariables": variables, "failMessage": fail_message, "response": result})

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

        return report

