import logging
import unittest
from connection_manager import _parse_log_level

# NOTE: It isn't immediately clear how to test tornado application, but the
# code is almost trivial, so we'll trust in the correctness of the tornado lib
# and leave it untested for now. https://www.tornadoweb.org/en/stable/testing.html
# provides some hints should we choose to revisit later


class ConnectionManagerTestCase(unittest.TestCase):
    def test_parse_log_level(self):
        strs = ["NotSet", "Debug", "InFo", "Warn", "eRRor", "CRITICAL"]
        ints = [
            logging.NOTSET,
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        ]
        self.assertTrue(all(_parse_log_level(s) == i for s, i in zip(strs, ints)))
        with self.assertRaises(ValueError):
            _parse_log_level("asdf")
