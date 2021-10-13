FROM python:3.7

RUN addgroup appuser && adduser --disabled-password --gecos '' appuser --ingroup appuser

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . .
RUN chown -R appuser:appuser /usr/src/app

# From https://cloud.google.com/sdk/downloads
RUN curl https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-173.0.0-linux-x86_64.tar.gz -o google-cloud-sdk-173.0.0-linux-x86_64.tar.gz \
   && echo "8b8f900e23c24be808f59fc3233ff0d763adcca9fd9e07d9ba3c8977701001a3 google-cloud-sdk-173.0.0-linux-x86_64.tar.gz" | sha256sum --quiet -c - \
   && tar xzf google-cloud-sdk-173.0.0-linux-x86_64.tar.gz

RUN pip install datetime google-cloud-storage prometheus_client google-cloud-logging

RUN chmod a+x run.sh

USER appuser

CMD [ "/usr/src/app/run.sh" ]
