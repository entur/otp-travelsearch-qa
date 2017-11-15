# otp-travelsearch-qa
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
python graphqltest.py endpoints.csv
```

## Run and upload to gcp
```
BUCKET_NAME=<bucket_name> DESTINATION_BLOB_NAME="<destination_blob_name" python ./graphqltest.py endpoints.csv True
```

## Run and notify Hubot if necesarry
Requires access to etcd to be able to read and update last value
```
NOTIFY_HUBOT=True python ./graphqltest.py endpoints.csv
```

## Run and send metrics to Graphite
```
GRAPHITE_REPORT_HOST="<graphite>" python ./graphqltest.py endpoints.csv
```

## Viewing reports
See https://github.com/entur/otp-travelsearch-ui
