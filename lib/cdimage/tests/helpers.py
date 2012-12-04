# Copyright (C) 2012 Canonical Ltd.
# Author: Colin Watson <cjwatson@ubuntu.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Testing helpers."""

__metaclass__ = type

from logging.handlers import BufferingHandler
import shutil
import tempfile
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cdimage.log import logger


class UnlimitedBufferHandler(BufferingHandler):
    """A buffering handler that never flushes any records."""

    def __init__(self):
        BufferingHandler.__init__(self, 0)

    def shouldFlush(self, record):
        return False


class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.temp_dir = None

    def use_temp_dir(self):
        if self.temp_dir is not None:
            return
        self.temp_dir = tempfile.mkdtemp(prefix="cdimage")
        self.addCleanup(shutil.rmtree, self.temp_dir)

    def capture_logging(self):
        self.handler = UnlimitedBufferHandler()
        logger.handlers = []
        logger.addHandler(self.handler)
        logger.propagate = False

    def assertLogEqual(self, expected):
        self.assertEqual(
            expected, [record.getMessage() for record in self.handler.buffer])


def touch(path):
    with open(path, "a"):
        pass
