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
import logging

log = logging.getLogger(__name__)

def save_json_report(json_report):
    log.info("Saving json report")

    file_name = "/usr/src/app/test-report-{}.json".format(int(round(time.time() * 1000)))
    text_file = open(file_name, "w")
    text_file.write(json_report)
    text_file.close()
    log.info("Saved {}".format(file_name))
    return file_name
