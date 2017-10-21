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

import urllib.request
import json
import requests
import socket

ETCD_BASE = "http://etcd-client.default.svc.cluster.local:2379/v2/keys/dynamic/otp-travelsearch-qa"
# ETCD_BASE = "http://localhost:2379/v2/keys/dynamic/otp-travelsearch-qa"
HUBOT_ENDPOINT = "http://hubot/hubot/say/"
# HUBOT_ENDPOINT = "http://localhost:8079/hubot/say/"
FAILED_PERCENTAGE_THRESHOLD = 5
DISABLE_HUBOT_NOTIFICATION = False
FAILED_PERCENTAGE_KEY = "failedPercentage"

def getValue(key):
    url = ETCD_BASE + "/" + key
    try:
        print("Getting value from key '{}' from etcd".format(key))
        response = requests.get(ETCD_BASE + "/" + key)
        jsonResponse = response.json()
        value = jsonResponse["node"]["value"]
        print("Got value '{}' from etcd".format(value))
        return value
    except Exception as e:
        print("Error getting value from key {} on url {}".format(key, url))
        print(e)
        raise e
        return None

def putValue(key, value):
    data = {"value" : value}
    print("Putting value {} for key {}".format(value, key))
    response = requests.put(ETCD_BASE + "/" + key, data=data)
    print(response)

def notifyHubot(message, icon):
    messageObject = {"source": socket.gethostname(), "icon": icon, "message": message}
    print("Nofifying hubot with message: {}".format(message))
    if(not DISABLE_HUBOT_NOTIFICATION):
        response = requests.post(HUBOT_ENDPOINT, json=messageObject)
        print("Response from notifying hubot: {}".format(response))
    else:
        print("Hubot disabled for testing")

def readAndReplace(key, value):
    previousValue = getValue(key)
    putValue(key, value)
    return previousValue

def notifyIfNecesarry(report):
    failedPercentage = report[FAILED_PERCENTAGE_KEY]
    lastfailedPercentage = float(readAndReplace(FAILED_PERCENTAGE_KEY, failedPercentage))
    if(lastfailedPercentage == None):
        print("No last valued. Just putting new {} value to etcd".format(FAILED_PERCENTAGE_KEY))
        return

    diff = abs(lastfailedPercentage - failedPercentage)
    print("Diff: {}".format(diff))

    if(failedPercentage > lastfailedPercentage and diff >= FAILED_PERCENTAGE_THRESHOLD):
        message = "Failed percentage has increased from {}% to {}% since last test execution. Threshold is: {}".format(lastfailedPercentage, failedPercentage, FAILED_PERCENTAGE_THRESHOLD)
        notifyHubot(message, ':disappointed:')
    elif(lastfailedPercentage > failedPercentage and diff >= FAILED_PERCENTAGE_THRESHOLD):
        message = "Improvement. Percentage of failed tests decreased from {}% to {}% since last test execution. Threshold is: {}".format(lastfailedPercentage, failedPercentage, FAILED_PERCENTAGE_THRESHOLD);
        notifyHubot(message, ':champagne:')
