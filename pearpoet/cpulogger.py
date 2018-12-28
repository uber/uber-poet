#  Copyright (c) 2018 Uber Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import subprocess
import sys
from tempfile import TemporaryFile


class CPULog(object):
    """An object representation of a CPU state log"""
    EPOCH_MULT = 1000000

    def __init__(self, line=None):
        self.epoch = None
        self.sys = None
        self.user = None
        self.idle = None
        if line:
            self.parse_line(line)

    def parse_line(self, line):
        """Parses a top CPU log string into data for this object"""

        def percent_to_num(raw):
            return float(raw[:-1]) * 0.01

        line = str(line)
        items = line.split(" ")
        # filter out null chars that sometimes showup
        epoch_str = items[0].translate(None, '\x00')

        self.epoch = int(epoch_str)
        self.user = percent_to_num(items[3])
        self.sys = percent_to_num(items[5])
        self.idle = percent_to_num(items[7])

    def chrome_trace(self):
        """Returns the chrome trace json representation of the the object"""
        return {
            "name": "cpu",
            "ph": "C",
            "pid": 1,
            "ts": self.chrome_epoch,
            "args": {
                "user": self.user,
                "sys": self.sys,
                "idle": self.idle
            }
        }

    @property
    def chrome_epoch(self):
        """Turns the internal epoch represenation into the time unit that chrome traces expect"""
        return self.epoch * CPULog.EPOCH_MULT

    def chrome_epoch_in_range(self, min_ts, max_ts):
        """Returns true if this object is within the specified time range"""
        return min_ts <= self.chrome_epoch <= max_ts

    @staticmethod
    def find_timestamp_range(traces):
        """
        Finds the minimum and maximum times of items inside a chrome trace list,
        so the CPU log won't add CPU items outside of it's range.
        """
        min_ts = sys.maxsize
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
        """Adds CPU items to a chrome trace"""
        min_ts, max_ts = CPULog.find_timestamp_range(traces)
        traces_in_range = [i.chrome_trace() for i in log_list if i.chrome_epoch_in_range(min_ts, max_ts)]
        return traces + traces_in_range


# TODO Use psutil instead of top bash script to fix app killing issues?
class CPULogger(object):
    """
    This class uses the top command under the hood to continiously log system cpu
    utilization on the current system.
    """

    def __init__(self):
        self.process = None
        self.output = TemporaryFile()

    def __del__(self):
        self.output.close()

    def start(self):
        """Starts the CPU logger"""
        self.stop()
        logging.warning('You will probably have to call `sudo killall top` to'
                        ' kill the CPU monitor after this python script finishes execution.')
        script_path = os.path.join(os.path.dirname(__file__), "resources", "cpu_log.sh")
        self.process = subprocess.Popen([script_path], stdout=self.output)

    def stop(self):
        """
        Should stop the CPU logger.

        MAJOR
        TODO doesn't do anything, either because top runs as root and thus you need
             to be root to kill it or some process group thing we are not doing properly
             self.process.kill() doesnt work either.
        """
        if self.process:
            self.process.terminate()
            self.process = None

    def kill(self):
        """
        Attempts to use sudo to kill the dangling CPU monitor.  Currently doesn't seem to work,
        you need to kill the top process outside of the python process.
        """
        self.stop()
        command = ['sudo', 'killall', 'top']
        logging.warning('Killing dangling CPU monitor with sudo. Command: `%s`', ' '.join(command))
        try:
            subprocess.check_call(command)
        except subprocess.CalledProcessError:
            logging.info("Error killing top command")

    def process_log(self):
        """Stops the CPU logger and converts the internal CPU log strings into a list of CPULog objects."""
        self.stop()
        self.output.seek(0)
        out = [CPULog(line) for line in self.output]
        self.output.close()
        self.output = TemporaryFile()
        return out
