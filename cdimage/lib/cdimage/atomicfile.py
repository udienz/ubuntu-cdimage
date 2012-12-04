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

"""Atomic writing of files."""

__metaclass__ = type

import codecs
import io
import os
import sys


class AtomicFile:
    """Facilitate atomic writing of files.  Forces UTF-8 encoding."""

    def __init__(self, filename):
        self.filename = filename
        if sys.version_info[0] < 3:
            self.fd = codecs.open(
                '%s.new' % self.filename, 'w', 'UTF-8', 'replace')
        else:
            # io.open is available from Python 2.6, but we only use it with
            # Python 3 because it raises exceptions when passed bytes.
            self.fd = io.open(
                '%s.new' % self.filename, mode='w',
                encoding='UTF-8', errors='replace')

    def __enter__(self):
        return self.fd

    def __exit__(self, exc_type, unused_exc_value, unused_exc_tb):
        self.fd.close()
        if exc_type is None:
            os.rename('%s.new' % self.filename, self.filename)

    # Not really necessary, but reduces pychecker confusion.
    def write(self, s):
        self.fd.write(s)
