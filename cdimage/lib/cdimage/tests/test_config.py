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

"""Unit tests for cdimage.config."""

from __future__ import print_function

__metaclass__ = type

import os
from textwrap import dedent
try:
    from test.support import EnvironmentVarGuard
except ImportError:
    from test.test_support import EnvironmentVarGuard

from cdimage.config import all_series, Config, Series
from cdimage.tests.helpers import TestCase


class TestSeries(TestCase):
    def test_find_by_name(self):
        series = Series.find_by_name("hoary")
        self.assertEqual(("hoary", "5.04", "Hoary Hedgehog"), tuple(series))

    def test_find_by_version(self):
        series = Series.find_by_version("5.04")
        self.assertEqual(("hoary", "5.04", "Hoary Hedgehog"), tuple(series))

    def test_latest(self):
        self.assertTrue(Series.latest().is_latest)

    def test_str(self):
        series = Series.find_by_name("warty")
        self.assertEqual("warty", str(series))

    def test_is_latest(self):
        self.assertFalse(all_series[0].is_latest)
        self.assertTrue(all_series[-1].is_latest)

    def test_compare(self):
        series = Series.find_by_name("hoary")

        self.assertLess(series, "breezy")
        self.assertLessEqual(series, "hoary")
        self.assertLessEqual(series, "breezy")
        self.assertEqual(series, "hoary")
        self.assertNotEqual(series, "warty")
        self.assertNotEqual(series, "breezy")
        self.assertGreaterEqual(series, "warty")
        self.assertGreaterEqual(series, "hoary")
        self.assertGreater(series, "warty")

        self.assertLess(series, Series.find_by_name("breezy"))
        self.assertLessEqual(series, Series.find_by_name("hoary"))
        self.assertLessEqual(series, Series.find_by_name("breezy"))
        self.assertEqual(series, Series.find_by_name("hoary"))
        self.assertNotEqual(series, Series.find_by_name("warty"))
        self.assertNotEqual(series, Series.find_by_name("breezy"))
        self.assertGreaterEqual(series, Series.find_by_name("warty"))
        self.assertGreaterEqual(series, Series.find_by_name("hoary"))
        self.assertGreater(series, Series.find_by_name("warty"))


class TestConfig(TestCase):
    def test_default_root(self):
        with EnvironmentVarGuard() as env:
            env.pop("CDIMAGE_ROOT", None)
            config = Config(read=False)
            self.assertEqual("/srv/cdimage.ubuntu.com", config.root)

    def test_root_from_environment(self):
        with EnvironmentVarGuard() as env:
            env["CDIMAGE_ROOT"] = "/path"
            config = Config(read=False)
            self.assertEqual("/path", config.root)

    def test_default_values(self):
        config = Config(read=False)
        self.assertEqual("", config["PROJECT"])

    def test_read_shell(self):
        self.use_temp_dir()
        with EnvironmentVarGuard() as env:
            env["CDIMAGE_ROOT"] = self.temp_dir
            os.mkdir(os.path.join(self.temp_dir, "etc"))
            with open(os.path.join(self.temp_dir, "etc", "config"), "w") as f:
                print(dedent("""\
                    #! /bin/sh
                    PROJECT=ubuntu
                    CAPPROJECT=Ubuntu
                    """), file=f)
            config = Config()
            self.assertEqual("ubuntu", config["PROJECT"])
            self.assertEqual("Ubuntu", config["CAPPROJECT"])

    def test_missing_config(self):
        # Even if etc/config is missing, Config still reads values from the
        # environment.  This makes it easier to experiment locally.
        self.use_temp_dir()
        with EnvironmentVarGuard() as env:
            env["CDIMAGE_ROOT"] = self.temp_dir
            env["PROJECT"] = "kubuntu"
            config = Config()
            self.assertEqual("kubuntu", config["PROJECT"])

    def test_series(self):
        config = Config(read=False)
        config["DIST"] = Series.find_by_name("warty")
        self.assertEqual("warty", config.series)

    def test_arches(self):
        config = Config(read=False)
        self.assertEqual([], config.arches)
        config["ARCHES"] = "i386"
        self.assertEqual(["i386"], config.arches)
        config["ARCHES"] = "amd64 i386"
        self.assertEqual(["amd64", "i386"], config.arches)
