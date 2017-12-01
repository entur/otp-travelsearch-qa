#!/bin/bash

: ${ENDPOINTS_FILE="endpoints.csv"}

export NOTIFY_HUBOT=${NOTIFY_HUBOT="True"}
export GRAPHITE_REPORT_HOST=${GRAPHITE_REPORT_HOST="graphite"}

python ./graphqltest.py ${ENDPOINTS_FILE}

echo "Deleting my own pod $(hostname)"
curl --write-out '%{http_code}' --silent --output /dev/null -XDELETE "http://babylon/services/local/deployment/pod?name=$(hostname)"

echo "done"
