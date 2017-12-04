currentDate=$1
finalDate=$2
while [ $currentDate != $finalDate ]; do
  echo "Searching on date " $currentDate
  TRAVEL_SEARCH_DATE=$currentDate python graphql_test.py endpoints.csv
  currentDate=$(date -I -d "$currentDate + 1 day")
done