import subprocess
import os
import sys
from tempfile import TemporaryFile


class CPULog(object):
    EPOCH_MULT = 1000000

    def __init__(self, line=None):
        self.epoch = None
        self.sys = None
        self.user = None
        self.idle = None
        if line:
            self.parse_line(line)

    def parse_line(self, line):
        def percent_to_num(raw):
            return float(raw[:-1])*0.01

        line = str(line)
        items = line.split(" ")
        # filter out null chars that sometimes showup
        epoch_str = items[0].translate(None, '\x00')

        self.epoch = int(epoch_str)
        self.user = percent_to_num(items[3])
        self.sys = percent_to_num(items[5])
        self.idle = percent_to_num(items[7])

    def chrome_trace(self):
        return {"name": "cpu", "ph": "C", "pid": 1, "ts": self.chrome_epoch, "args":
                {"user": self.user, "sys": self.sys, "idle": self.idle}}

    @property
    def chrome_epoch(self):
        return self.epoch * CPULog.EPOCH_MULT

    def chrome_epoch_in_range(self, min_ts, max_ts):
        return self.chrome_epoch >= min_ts and self.chrome_epoch <= max_ts

    @staticmethod
    def find_timestamp_range(traces):
        min_ts = sys.maxint
        max_ts = -1
        for trace in traces:
            ts = trace['ts']
            if ts < min_ts:
                min_ts = ts
            elif ts > max_ts:
                max_ts = ts
        return min_ts, max_ts

    @staticmethod
    def apply_log_to_trace(log_list, traces):
        min_ts, max_ts = CPULog.find_timestamp_range(traces)
        traces_in_range = [i.chrome_trace() for i in log_list
                           if i.chrome_epoch_in_range(min_ts, max_ts)]
        return traces + traces_in_range


class CPULogger(object):

    def __init__(self):
        self.process = None
        self.output = TemporaryFile()

    def __del__(self):
        self.output.close()

    def start(self):
        self.stop()
        script_path = os.path.join(os.path.dirname(__file__), "resources", "cpu_log.sh")
        # MAJOR TODO deal with this still executing when the python program is killed
        self.process = subprocess.Popen([script_path], stdout=self.output)

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None

    def process_log(self):
        self.stop()
        self.output.seek(0)
        out = [CPULog(line) for line in self.output]
        self.output.close()
        self.output = TemporaryFile()
        return out
