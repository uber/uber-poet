import unittest
import os
from pearpoet.cpulogger import CPULog


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
