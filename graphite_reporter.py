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

import graphitesend
import os


class GraphiteReporter:
    def __init__(self):
        if ('GRAPHITE_REPORT_HOST' in os.environ):
            self.graphite = graphitesend.init(prefix='app',
                                              system_name='otp-travelsearch-qa',
                                              graphite_server=os.environ["GRAPHITE_REPORT_HOST"],
                                              timeout_in_seconds=15)
            print("Initiated graphite send")
        else:
            print("GRAPHITE_REPORT_HOST not set")
            self.graphite = None

    def report_to_graphite(self, list_of_metrics):
        if self.graphite:
            print("Sending list of metrics: {}".format(list_of_metrics))
            self.graphite.send_list(list_of_metrics)
