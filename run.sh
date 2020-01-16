#!/bin/bash

echo "Sleeping for 10 seconds..."

sleep 10s

python ./graphql_test.py ${ENDPOINTS_FILE} ${STOP_TIMES_FILE}

echo "done"
