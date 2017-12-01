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

import requests
import socket

ETCD_BASE = "http://etcd-client.default.svc.cluster.local:2379/v2/keys/dynamic/otp-travelsearch-qa"
# ETCD_BASE = "http://localhost:2379/v2/keys/dynamic/otp-travelsearch-qa"
HUBOT_ENDPOINT = "http://hubot/hubot/say/"
# HUBOT_ENDPOINT = "http://localhost:8079/hubot/say/"
FAILED_PERCENTAGE_THRESHOLD = 1
DISABLE_HUBOT_NOTIFICATION = False
FAILED_PERCENTAGE_KEY = "failedPercentage"


def get_value(key):
    url = ETCD_BASE + "/" + key
    try:
        print("Getting value from key '{}' from etcd".format(key))
        response = requests.get(ETCD_BASE + "/" + key)
        json_response = response.json()
        value = json_response["node"]["value"]
        print("Got value '{}' from etcd".format(value))
        return value
    except Exception as e:
        print("Error getting value from key {} on url {}".format(key, url))
        print(e)
        return "0"


def put_value(key, value):
    data = {"value": value}
    print("Putting value {} for key {}".format(value, key))
    response = requests.put(ETCD_BASE + "/" + key, data=data)
    print(response)


def notify_hubot(message, icon):
    message_object = {"source": socket.gethostname(), "icon": icon, "message": message}
    print("Nofifying hubot with message: {}".format(message))
    if (not DISABLE_HUBOT_NOTIFICATION):
        response = requests.post(HUBOT_ENDPOINT, json=message_object)
        print("Response from notifying hubot: {}".format(response))
    else:
        print("Hubot disabled for testing")


def read_and_replace(key, value):
    previous_value = get_value(key)
    put_value(key, value)
    return previous_value


def notify_if_necessary(report):
    travel_search_report = report["travelSearch"]
    failed_percentage = travel_search_report[FAILED_PERCENTAGE_KEY]

    lastfailed_percentage = float(read_and_replace(FAILED_PERCENTAGE_KEY, failed_percentage))
    if lastfailed_percentage is None:
        print("No last valued. Just putting new {} value to etcd".format(FAILED_PERCENTAGE_KEY))
        return

    diff = abs(lastfailed_percentage - failed_percentage)
    print("Diff: {}".format(diff))

    if failed_percentage > lastfailed_percentage and diff >= FAILED_PERCENTAGE_THRESHOLD:
        message = "Failed percentage has increased from {:.2f} to {:.2f} since last test execution. Threshold is: {}".format(
            lastfailed_percentage, failed_percentage, FAILED_PERCENTAGE_THRESHOLD)
        notify_hubot(message, ':disappointed:')
    elif lastfailed_percentage > failed_percentage and diff >= FAILED_PERCENTAGE_THRESHOLD:
        message = "Improvement. Percentage of failed tests decreased from {:.2f} to {:.2f} since last test execution. Threshold is: {}".format(
            lastfailed_percentage, failed_percentage, FAILED_PERCENTAGE_THRESHOLD);
        notify_hubot(message, ':champagne:')
