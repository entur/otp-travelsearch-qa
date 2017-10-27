#!/bin/bash

: ${ENDPOINTS_FILE="endpoints.csv"}
: ${UPLOAD_GCP="True"}
export NOTIFY_HUBOT=${NOTIFY_HUBOT="True"}

python ./graphqltest.py ${ENDPOINTS_FILE} ${UPLOAD_GCP}

echo "Deleting my own pod $(hostname)"
curl --write-out '%{http_code}' --silent --output /dev/null -XDELETE "http://babylon/babylon/api/pod?name=$(hostname)"

echo "done"
