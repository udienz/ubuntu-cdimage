#! /usr/bin/python

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

"""Unit tests for cdimage.atomicfile."""

__metaclass__ = type

import os

from cdimage.atomicfile import AtomicFile
from cdimage.tests.helpers import TestCase


class TestAtomicFile(TestCase):
    def test_creates_file(self):
        """AtomicFile creates the named file with the requested contents."""
        self.use_temp_dir()
        foo = os.path.join(self.temp_dir, "foo")
        with AtomicFile(foo) as test:
            test.write("string")
        with open(foo) as handle:
            self.assertEqual("string", handle.read())

    def test_removes_dot_new(self):
        """AtomicFile does not leave .new files lying around."""
        self.use_temp_dir()
        foo = os.path.join(self.temp_dir, "foo")
        with AtomicFile(foo):
            pass
        self.assertFalse(os.path.exists("%s.new" % foo))
