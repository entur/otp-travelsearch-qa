# Licensed under the EUPL, Version 1.2 or – as soon they will be approved by
# the European Commission - subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
#
#   https://joinup.ec.europa.eu/software/page/eupl
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and
# limitations under the Licence.

import os
from prometheus_client import CollectorRegistry, Counter, Histogram, pushadd_to_gateway

class PrometheusReporter:
    def __init__(self):
      self.search_registry = CollectorRegistry()
      self.stop_times_registry = CollectorRegistry()

      self.search_count = Counter('otp_travelsearch_qa_search_count', 'Total travel search requests', ['operator'], registry=self.search_registry)
      self.search_success_count = Counter('otp_travelsearch_qa_search_success_count', 'Total successful travel search requests', ['operator'], registry=self.search_registry)
      self.search_failed_count = Counter('otp_travelsearch_qa_search_failed_count', 'Total failed travel search requests', ['operator'], registry=self.search_registry)
      self.search_seconds_each = Histogram('otp_travelsearch_qa_search_seconds_each', 'Request time of each search', ['operator'], registry=self.search_registry)
      self.search_seconds_total = Histogram('otp_travelsearch_qa_search_seconds_total', 'Total request time', registry=self.search_registry)
      self.search_seconds_average = Histogram('otp_travelsearch_qa_search_seconds_average', 'Average request time', registry=self.search_registry)

      self.stop_time_count = Counter('otp_travelsearch_qa_stop_time_count', 'Total stop times requests', ['operator'], registry=self.stop_times_registry)
      self.stop_time_success_count = Counter('otp_travelsearch_qa_stop_time_success_count', 'Total successful stop times requests', ['operator'], registry=self.stop_times_registry)
      self.stop_time_failed_count = Counter('otp_travelsearch_qa_stop_time_failed_count', 'Total failed stop times requests', ['operator'], registry=self.stop_times_registry)
      self.stop_time_seconds_total = Histogram('otp_travelsearch_qa_stop_time_seconds_total', 'Total request time', registry=self.stop_times_registry)
      self.stop_time_seconds_average = Histogram('otp_travelsearch_qa_stop_time_seconds_average', 'Average request time', registry=self.stop_times_registry)

    def report_travel_search(self, operator, success, time_spent):
      self.search_count.labels(operator=operator).inc()
      if success:
        self.search_success_count.labels(operator=operator).inc()
      else:
        self.search_failed_count.labels(operator=operator).inc()
      self.search_seconds_each.labels(operator=operator).observe(time_spent)

    def report_travel_search_request_durations(self, total, average):
      self.search_seconds_total.observe(total)
      self.search_seconds_average.observe(average)

    def report_stop_time(self, operator, success):
      self.stop_time_count.labels(operator=operator).inc()
      if success:
        self.stop_time_success_count.labels(operator=operator).inc()
      else:
        self.stop_time_failed_count.labels(operator=operator).inc()

    def report_stop_time_request_durations(self, total, average):
      self.stop_time_seconds_total.observe(total)
      self.stop_time_seconds_average.observe(average)

    def push_search_to_gateway(self):
      if 'PROMETHEUS_PUSH_GATEWAY' in os.environ:
        print('Pushing search metrics to prometheus')
        pushadd_to_gateway(os.environ['PROMETHEUS_PUSH_GATEWAY'], job='otp-travelsearch-qa', registry=self.search_registry)

    def push_stop_times_to_gateway(self):
      if 'PROMETHEUS_PUSH_GATEWAY' in os.environ:
        print('Pushing stop times metrics to prometheus')
        pushadd_to_gateway(os.environ['PROMETHEUS_PUSH_GATEWAY'], job='otp-travelsearch-qa', registry=self.stop_times_registry)
