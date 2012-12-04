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

"""Unit tests for cdimage.mirror."""

__metaclass__ = type

import os

from cdimage.mirror import find_mirror
from cdimage.config import Config, Series
from cdimage.tests.helpers import TestCase


# This only needs to go up as far as the series find_mirror cares about.
all_series = [
    "warty",
    "hoary",
    "breezy",
    "dapper",
    "edgy",
    "feisty",
    "gutsy",
    "hardy",
    ]


class TestChecksumFile(TestCase):
    def assertMirrorEqual(self, base, arch, series):
        config = Config(read=False)
        config["DIST"] = Series.find_by_name(series)
        self.assertEqual(
            os.path.join(config.root, base), find_mirror(config, arch))

    def test_amd64(self):
        for series in all_series:
            self.assertMirrorEqual("ftp", "amd64", series)

    def test_armel(self):
        for series in all_series:
            self.assertMirrorEqual("ftp", "armel", series)

    def test_hppa(self):
        for series in all_series:
            self.assertMirrorEqual("ftp", "hppa", series)

    def test_i386(self):
        for series in all_series:
            self.assertMirrorEqual("ftp", "i386", series)

    def test_lpia(self):
        for series in all_series:
            self.assertMirrorEqual("ftp", "lpia", series)

    def test_powerpc(self):
        for series in all_series:
            self.assertMirrorEqual("ftp", "powerpc", series)

    def test_sparc(self):
        for series in all_series:
            self.assertMirrorEqual("ftp", "sparc", series)
