FROM python:3.7.16-alpine3.17

RUN apk update && apk upgrade && apk add --no-cache \
   curl \
   tar \
   bash \
   tini

RUN addgroup appuser && adduser --disabled-password --gecos '' appuser --ingroup appuser

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . .
RUN chown -R appuser:appuser /usr/src/app

# From https://cloud.google.com/sdk/downloads
RUN curl https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-173.0.0-linux-x86_64.tar.gz -o google-cloud-sdk-173.0.0-linux-x86_64.tar.gz \
   && echo "8b8f900e23c24be808f59fc3233ff0d763adcca9fd9e07d9ba3c8977701001a3  google-cloud-sdk-173.0.0-linux-x86_64.tar.gz" | sha256sum -csw - \
   && tar xzf google-cloud-sdk-173.0.0-linux-x86_64.tar.gz

RUN pip install -r requirements.txt

RUN chmod a+x run.sh

USER appuser

CMD [ "/sbin/tini", "--", "/usr/src/app/run.sh" ]