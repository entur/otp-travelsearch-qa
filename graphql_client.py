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
import os

from six.moves import urllib
from graphql_exception import GraphQLException


class GraphQLClient:
    HEADERS = {'Accept': 'application/json',
               'Content-Type': 'application/json',
               'User-Agent': 'otp-travelsearch-qa',
               'ET-Client-Name': 'otp-travelsearch-qa',
               'ET-Client-ID': os.environ.get('HOSTNAME','')}

    print("Will use these headers: {}".format(HEADERS))

    CONNECT_TIMEOUT_SECONDS = 45

    def __init__(self, endpoint):
        self.endpoint = endpoint

    def execute(self, query, variables=None):
        return self._send(query, variables)

    def _send(self, query, variables):
        data = {'query': query, 'variables': variables}

        req = urllib.request.Request(self.endpoint, json.dumps(data).encode('utf-8'), self.HEADERS)

        try:
            response = urllib.request.urlopen(req, timeout=self.CONNECT_TIMEOUT_SECONDS)
            return response.read().decode('utf-8')
        except Exception as e:
            graphql_exception = GraphQLException(str(e), '')
            raise graphql_exception
        except urllib.error.HTTPError as e:
            # In case of HTTPError, we want to read the response
            graphql_exception = GraphQLException(str(e), e.read().decode('utf-8'))
            raise graphql_exception
