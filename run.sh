#!/bin/bash

: ${ENDPOINTS_FILE="endpoints.csv"}
: ${STOP_TIMES_FILE="stop_times.csv"}

export GRAPHITE_REPORT_HOST=${GRAPHITE_REPORT_HOST="graphite"}

python ./graphql_test.py ${ENDPOINTS_FILE} ${STOP_TIMES_FILE}

echo "Deleting my own pod $(hostname)"
curl --write-out '%{http_code}' --silent --output /dev/null -XDELETE "http://babylon/services/local/deployment/pod?name=$(hostname)"

echo "done"
