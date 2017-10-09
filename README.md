# otp-travelsearch-qa
Simple test tool for OTP travel searches

Reads CSV on the format:
`name,fromPlace,toPlace`

Uses the OTP GraphQL endpoint.

Produces json report or html report.

Prepare:
* Install python
* pip-install simplejson json2html graphqlclient csv
* Run `python graphqltest.py`
* Report produced: Report.html
