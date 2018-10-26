# otp-travelsearch-qa [![CircleCI](https://circleci.com/gh/entur/otp-travelsearch-qa/tree/master.svg?style=svg)](https://circleci.com/gh/entur/otp-travelsearch-qa/tree/master)
Simple test tool for OTP travel searches

Reads endpoints.csv and runs OTP travelsearches sequentially using the graphql endpoint.
It produces json reports.

## Optional features
* Upload reports to gcp (Google cloud storage)
* Notify Hubot if failed percentage has changed
* Send stats to Graphite

## Prepare:
* Install python
* `pip install datetime google.cloud graphitesend`

## Run
```
python graphql_test.py endpoints.csv
```

## Run and upload to gcp
```
BUCKET_NAME=<bucket_name> DESTINATION_BLOB_NAME="<destination_blob_name" python ./graphql_test.py endpoints.csv True
```

## Run and notify Hubot if necesarry
Requires access to etcd to be able to read and update last value
```
NOTIFY_HUBOT=True python ./graphql_test.py endpoints.csv
```

## Run and send metrics to Graphite
```
GRAPHITE_REPORT_HOST="<graphite>" python ./graphql_test.py endpoints.csv
```

## Viewing reports
See https://github.com/entur/otp-travelsearch-ui


## Why not use a test framework?
This python script is run as a kubernetes job. Why not use a test framework or SaaS solution?
Because: we had specific requirements for travel search testing, and could not at the time find a faster solution than writing and maintaining this ourself. Some of these requirements:

### Test report format
The test reports does have a very specific format, that allows us to control the view in https://github.com/entur/otp-travelsearch-ui
* It makes it easy to group reports by location or time usage
* Show the metrics we actually want
* Link straight to shamash (GraphiQL) with the query that failed or was slow

### Control our headers
Send ET-Client-Name to identify calls from this script.

### Sending metrics to Graphite/Grafana
This script updates graphite
![Grafana](images/grafana)

### Postman Collection and Monitor
We have spent quite some time trying to migrate this test suite to Postman Collection and Monitor.
To make it work with Postman, quite some workarounds had to be made because of GraphQL and reading and iterating from csv files.
And when it finally was set up and running with monitor, it turned out extremely expensive because of the number of requests per month. So we had to turn it off. It could have been executed with Newman, but then the impression was that a kubernetes pod was required, so it would not have been a Saas solution anyway


## TODO
* Separate folder for py files
* Verify syntax of python scripts with CI
* Do some testing to increase quality
* Use a document database to store reports? Must be a suitable solution for otp-travelsearch-ui
* Do more checks on the results from OpenTripPlanner