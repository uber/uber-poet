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

import os
import unittest

from uberpoet.cpulogger import CPULog


class TestCPULogger(unittest.TestCase):

    def test_cpu_convert(self):
        test_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'cpu_log.txt')
        with open(test_path, 'r') as log:
            out = [CPULog(line) for line in log]
        chrome_out = [i.chrome_trace() for i in out]
        first_time = 1535510161

        self.assertEqual(len(out), 10)
        self.assertEqual(len(chrome_out), 10)
        self.assertEqual(chrome_out[0]['ts'], first_time * CPULog.EPOCH_MULT)
        self.assertEqual(out[0].epoch, first_time)
