#!/bin/bash

export GRAPHITE_REPORT_HOST=${GRAPHITE_REPORT_HOST="graphite"}

python ./graphql_test.py ${ENDPOINTS_FILE} ${STOP_TIMES_FILE}

echo "done"
