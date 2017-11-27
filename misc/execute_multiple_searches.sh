#!/bin/bash

echo "start "
date
for i in {1..4}
do
  python graphqltest.py endpoints.csv
  echo "----------------"
done
echo "waiting"
# wait
date
echo "done "
