import graphitesend
import os

class GraphiteReporter:
    def __init__(self):
        if('GRAPHITE_REPORT_HOST' in os.environ):
            self.graphite = graphitesend.init(prefix='app',
                system_name='otp-travelsearch-qa',
                graphite_server=os.environ["GRAPHITE_REPORT_HOST"],
                timeout_in_seconds=15)
            print("Initiated graphite send")
        else:
            print("GRAPHITE_REPORT_HOST not set")
            self.graphite = None

    def reportToGraphite(self, listOfMetrics):
        if self.graphite:
            print("Sending list of metrics: {}".format(listOfMetrics))
            self.graphite.send_list(listOfMetrics)
