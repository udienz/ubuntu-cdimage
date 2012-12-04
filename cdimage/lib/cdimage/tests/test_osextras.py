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

"""Unit tests for cdimage.osextras."""

import errno
import os
try:
    from test.support import EnvironmentVarGuard
except ImportError:
    from test.test_support import EnvironmentVarGuard

from cdimage import osextras
from cdimage.tests.helpers import TestCase, touch


class TestOSExtras(TestCase):
    def setUp(self):
        super(TestOSExtras, self).setUp()
        self.use_temp_dir()

    def test_ensuredir_previously_missing(self):
        new_dir = os.path.join(self.temp_dir, "dir")
        osextras.ensuredir(new_dir)
        self.assertTrue(os.path.isdir(new_dir))

    def test_ensuredir_previously_present(self):
        new_dir = os.path.join(self.temp_dir, "dir")
        os.mkdir(new_dir)
        osextras.ensuredir(new_dir)
        self.assertTrue(os.path.isdir(new_dir))

    def test_mkemptydir_previously_missing(self):
        new_dir = os.path.join(self.temp_dir, "dir")
        osextras.mkemptydir(new_dir)
        self.assertTrue(os.path.isdir(new_dir))
        self.assertEqual([], os.listdir(new_dir))

    def test_mkemptydir_previously_populated(self):
        new_dir = os.path.join(self.temp_dir, "dir")
        os.mkdir(new_dir)
        touch(os.path.join(new_dir, "file"))
        osextras.mkemptydir(new_dir)
        self.assertTrue(os.path.isdir(new_dir))
        self.assertEqual([], os.listdir(new_dir))

    def test_listdir_directory_present(self):
        new_dir = os.path.join(self.temp_dir, "dir")
        os.mkdir(new_dir)
        touch(os.path.join(new_dir, "file"))
        self.assertEqual(["file"], osextras.listdir_force(new_dir))

    def test_listdir_directory_missing(self):
        new_dir = os.path.join(self.temp_dir, "dir")
        self.assertEqual([], osextras.listdir_force(new_dir))

    def test_unlink_file_present(self):
        path = os.path.join(self.temp_dir, "file")
        touch(path)
        osextras.unlink_force(path)
        self.assertFalse(os.path.exists(path))

    def test_unlink_file_missing(self):
        path = os.path.join(self.temp_dir, "file")
        osextras.unlink_force(path)
        self.assertFalse(os.path.exists(path))

    def test_find_on_path_missing_environment(self):
        with EnvironmentVarGuard() as env:
            env.pop("PATH", None)
            self.assertFalse(osextras.find_on_path("ls"))

    def test_find_on_path_present_executable(self):
        bin_dir = os.path.join(self.temp_dir, "bin")
        os.mkdir(bin_dir)
        program = os.path.join(bin_dir, "program")
        touch(program)
        os.chmod(program, 0o755)
        with EnvironmentVarGuard() as env:
            env["PATH"] = bin_dir
            self.assertTrue(osextras.find_on_path("program"))

    def test_find_on_path_present_not_executable(self):
        bin_dir = os.path.join(self.temp_dir, "bin")
        os.mkdir(bin_dir)
        program = os.path.join(bin_dir, "program")
        touch(program)
        with EnvironmentVarGuard() as env:
            env["PATH"] = bin_dir
            self.assertFalse(osextras.find_on_path("program"))

    def test_waitpid_retry(self):
        class Completed(Exception):
            pass

        waitpid_called = [False]

        def mock_waitpid(*args):
            if not waitpid_called[0]:
                waitpid_called[0] = True
                raise OSError(errno.EINTR, "")
            else:
                raise Completed

        real_waitpid = os.waitpid
        os.waitpid = mock_waitpid
        try:
            self.assertRaises(Completed, osextras.waitpid_retry, -1, 0)
        finally:
            os.waitpid = real_waitpid

    def test_run_bounded_runs(self):
        self.use_temp_dir()
        sentinel = os.path.join(self.temp_dir, "foo")
        osextras.run_bounded(3600, ["touch", sentinel])
        self.assertTrue(os.path.exists(sentinel))

    def test_run_bounded_finite(self):
        osextras.run_bounded(1, ["sh", "-c", "while :; do sleep 3600; done"])
