from six.moves import urllib
import json



class GraphQLClient:
    HEADERS = {'Accept': 'application/json',
           'Content-Type': 'application/json'}



    def __init__(self, endpoint):
        self.endpoint = endpoint

    def execute(self, query, variables=None):
        return self._send(query, variables)

    def _send(self, query, variables):
        data = {'query': query, 'variables': variables}

        req = urllib.request.Request(self.endpoint, json.dumps(data).encode('utf-8'), self.HEADERS)

        try:
            response = urllib.request.urlopen(req)
            return response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            raise e
