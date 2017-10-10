#!/bin/bash

${ENDPOINTS_FILE="endpoints"}
${UPLOAD_GCP="True"}

python ./graphqltest.py ${ENDPOINTS_FILE} ${UPLOAD_GCP}

echo "Deleting my own pod $(hostname)"
curl -XDELETE "http://babylon/babylon/api/pod?name=$(hostname)"
