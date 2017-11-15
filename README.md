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

## Viewing reports
See https://github.com/entur/otp-travelsearch-ui
