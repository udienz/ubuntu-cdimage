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

"""Unit tests for cdimage.build_id."""

import os
try:
    from test.support import EnvironmentVarGuard
except ImportError:
    from test.test_support import EnvironmentVarGuard

from cdimage.build_id import next_build_id
from cdimage.config import Config, Series
from cdimage.tests.helpers import TestCase


class TestNextBuildId(TestCase):
    def test_increment(self):
        self.use_temp_dir()
        with EnvironmentVarGuard() as env:
            env["CDIMAGE_ROOT"] = self.temp_dir
            os.mkdir(os.path.join(self.temp_dir, "etc"))
            config = Config(read=False)
            config["PROJECT"] = "ubuntu"
            config["DIST"] = Series.find_by_name("warty")
            config["DATE"] = "20120806"
            stamp = os.path.join(
                config.root, "etc",
                ".next-build-suffix-ubuntu-warty-daily-live")
            self.assertFalse(os.path.exists(stamp))
            self.assertEqual("20120806", next_build_id(config, "daily-live"))
            with open(stamp) as stamp_file:
                self.assertEqual("20120806:1\n", stamp_file.read())
            self.assertEqual("20120806.1", next_build_id(config, "daily-live"))
            with open(stamp) as stamp_file:
                self.assertEqual("20120806:2\n", stamp_file.read())
