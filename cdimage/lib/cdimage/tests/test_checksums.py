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

"""Unit tests for cdimage.checksums."""

from __future__ import print_function

__metaclass__ = type

import hashlib
import os
import shutil
import subprocess
import time
from textwrap import dedent

from cdimage.checksums import (
    apply_sed,
    ChecksumFile,
    ChecksumFileSet,
    checksum_directory,
    MetalinkChecksumFileSet,
    metalink_checksum_directory,
    )
from cdimage.config import Config
from cdimage.tests.helpers import TestCase, touch


class TestApplySed(TestCase):
    def test_apply_sed(self):
        self.assertEqual("aabce", apply_sed("abcde", "s/bcd/abc/"))


class TestChecksumFile(TestCase):
    def setUp(self):
        super(TestChecksumFile, self).setUp()
        self.config = Config(read=False)
        self.use_temp_dir()

    def test_read(self):
        with open(os.path.join(self.temp_dir, "MD5SUMS"), "w") as md5sums:
            print(dedent("""\
                checksum  one-path
                checksum *another-path
                """), file=md5sums)
        checksum_file = ChecksumFile(
            self.config, self.temp_dir, "MD5SUMS", hashlib.md5)
        checksum_file.read()
        self.assertEqual(
            {"one-path": "checksum", "another-path": "checksum"},
            checksum_file.entries)

    def test_read_missing(self):
        checksum_file = ChecksumFile(
            self.config, self.temp_dir, "MD5SUMS", hashlib.md5)
        checksum_file.read()
        self.assertEqual({}, checksum_file.entries)

    def test_checksum_small_file(self):
        entry_path = os.path.join(self.temp_dir, "entry")
        data = "test\n"
        with open(entry_path, "w") as entry:
            print(data, end="", file=entry)
        checksum_file = ChecksumFile(
            self.config, self.temp_dir, "MD5SUMS", hashlib.md5)
        self.assertEqual(
            hashlib.md5(data).hexdigest(), checksum_file.checksum(entry_path))

    def test_checksum_large_file(self):
        entry_path = os.path.join(self.temp_dir, "entry")
        data = "a" * 1048576
        with open(entry_path, "w") as entry:
            print(data, end="", file=entry)
        checksum_file = ChecksumFile(
            self.config, self.temp_dir, "SHA1SUMS", hashlib.sha1)
        self.assertEqual(
            hashlib.sha1(data).hexdigest(), checksum_file.checksum(entry_path))

    def test_add(self):
        entry_path = os.path.join(self.temp_dir, "entry")
        data = "test\n"
        with open(entry_path, "w") as entry:
            print(data, end="", file=entry)
        checksum_file = ChecksumFile(
            self.config, self.temp_dir, "MD5SUMS", hashlib.md5)
        checksum_file.add("entry")
        self.assertEqual(
            {"entry": hashlib.md5(data).hexdigest()}, checksum_file.entries)

    def test_add_existing(self):
        # Attempting to add an existing file has no effect.  (Use .remove()
        # first to overwrite an existing checksum.)
        entry_path = os.path.join(self.temp_dir, "entry")
        data = "test\n"
        with open(entry_path, "w") as entry:
            print(data, end="", file=entry)
        checksum_file = ChecksumFile(
            self.config, self.temp_dir, "MD5SUMS", hashlib.md5)
        checksum_file.entries["entry"] = ""
        checksum_file.add("entry")
        self.assertEqual("", checksum_file.entries["entry"])

    def test_remove(self):
        checksum_file = ChecksumFile(
            self.config, self.temp_dir, "MD5SUMS", hashlib.md5)
        checksum_file.entries["entry"] = "checksum"
        checksum_file.remove("entry")
        self.assertEqual({}, checksum_file.entries)

    def test_merge_takes_valid_checksums(self):
        old_dir = os.path.join(self.temp_dir, "old")
        os.mkdir(old_dir)
        touch(os.path.join(self.temp_dir, "entry"))
        with open(os.path.join(old_dir, "MD5SUMS"), "w") as old_md5sums:
            print("checksum *entry", file=old_md5sums)
        checksum_file = ChecksumFile(
            self.config, self.temp_dir, "MD5SUMS", hashlib.md5)
        checksum_file.merge([old_dir], "entry", ["entry"])
        self.assertEqual({"entry": "checksum"}, checksum_file.entries)

    def test_merge_ignores_stale_checksums(self):
        old_dir = os.path.join(self.temp_dir, "old")
        os.mkdir(old_dir)
        with open(os.path.join(old_dir, "MD5SUMS"), "w") as old_md5sums:
            print("checksum *entry", file=old_md5sums)
        entry_path = os.path.join(self.temp_dir, "entry")
        touch(entry_path)
        next_minute = time.time() + 60
        os.utime(entry_path, (next_minute, next_minute))
        checksum_file = ChecksumFile(
            self.config, self.temp_dir, "MD5SUMS", hashlib.md5)
        checksum_file.merge([old_dir], "entry", ["entry"])
        self.assertEqual({}, checksum_file.entries)

    def test_merge_takes_other_names(self):
        old_dir = os.path.join(self.temp_dir, "old")
        os.mkdir(old_dir)
        touch(os.path.join(self.temp_dir, "entry"))
        with open(os.path.join(old_dir, "MD5SUMS"), "w") as old_md5sums:
            print("checksum *other-entry", file=old_md5sums)
        checksum_file = ChecksumFile(
            self.config, self.temp_dir, "MD5SUMS", hashlib.md5)
        checksum_file.merge([old_dir], "entry", ["other-entry"])
        self.assertEqual({"entry": "checksum"}, checksum_file.entries)

    def test_write(self):
        checksum_file = ChecksumFile(
            self.config, self.temp_dir, "MD5SUMS", hashlib.md5, sign=False)
        for name in "1", "2":
            entry_path = os.path.join(self.temp_dir, name)
            with open(entry_path, "w") as entry:
                print(name, end="", file=entry)
            checksum_file.add(name)
        checksum_file.write()
        with open(checksum_file.path) as md5sums:
            self.assertEqual(dedent("""\
                %s *1
                %s *2
                """) %
                (hashlib.md5("1").hexdigest(), hashlib.md5("2").hexdigest()),
                md5sums.read())
        self.assertEqual(
            0,
            subprocess.call(
                ["md5sum", "-c", "--status", "MD5SUMS"], cwd=self.temp_dir))

    def test_context_manager(self):
        for name in "1", "2":
            entry_path = os.path.join(self.temp_dir, name)
            with open(entry_path, "w") as entry:
                print(name, end="", file=entry)
        md5sums_path = os.path.join(self.temp_dir, "MD5SUMS")
        with open(md5sums_path, "w") as md5sums:
            subprocess.call(
                ["md5sum", "-b", "1", "2"], stdout=md5sums, cwd=self.temp_dir)
        with ChecksumFile(
            self.config, self.temp_dir, "MD5SUMS", hashlib.md5,
            sign=False) as checksum_file:
            self.assertEqual(["1", "2"], sorted(checksum_file.entries))
            checksum_file.remove("1")
        with open(md5sums_path) as md5sums:
            self.assertEqual(
                "%s *2\n" % hashlib.md5("2").hexdigest(), md5sums.read())


class TestChecksumFileSet(TestCase):
    def setUp(self):
        super(TestChecksumFileSet, self).setUp()
        self.config = Config(read=False)
        self.use_temp_dir()
        self.files_and_commands = {
            "MD5SUMS": "md5sum",
            "SHA1SUMS": "sha1sum",
            "SHA256SUMS": "sha256sum",
            }
        self.cls = ChecksumFileSet

    def create_checksum_files(self, names, directory=None):
        if directory is None:
            directory = self.temp_dir
        for base, command in self.files_and_commands.items():
            with open(os.path.join(directory, base), "w") as f:
                subprocess.call(
                    [command, "-b"] + names, stdout=f, cwd=directory)

    def assertChecksumsEqual(self, entry_data, checksum_files):
        expected = {
            "MD5SUMS": dict(
                (k, hashlib.md5(v).hexdigest())
                for k, v in entry_data.items()),
            "SHA1SUMS": dict(
                (k, hashlib.sha1(v).hexdigest())
                for k, v in entry_data.items()),
            "SHA256SUMS": dict(
                (k, hashlib.sha256(v).hexdigest())
                for k, v in entry_data.items()),
            }
        observed = dict(
            (cf.name, cf.entries) for cf in checksum_files.checksum_files)
        self.assertEqual(expected, observed)

    def test_read(self):
        entry_path = os.path.join(self.temp_dir, "entry")
        with open(entry_path, "w") as entry:
            print("data", end="", file=entry)
        self.create_checksum_files(["entry"])
        for base, command in self.files_and_commands.items():
            with open(os.path.join(self.temp_dir, base), "w") as f:
                subprocess.call(
                    [command, "-b", "entry"], stdout=f, cwd=self.temp_dir)
        checksum_files = self.cls(self.config, self.temp_dir)
        checksum_files.read()
        self.assertChecksumsEqual({"entry": "data"}, checksum_files)

    def test_add(self):
        entry_path = os.path.join(self.temp_dir, "entry")
        data = "test\n"
        with open(entry_path, "w") as entry:
            print(data, end="", file=entry)
        checksum_files = self.cls(self.config, self.temp_dir)
        checksum_files.add("entry")
        self.assertChecksumsEqual({"entry": "test\n"}, checksum_files)

    def test_remove(self):
        entry_path = os.path.join(self.temp_dir, "entry")
        data = "test\n"
        with open(entry_path, "w") as entry:
            print(data, end="", file=entry)
        self.create_checksum_files(["entry"])
        checksum_files = self.cls(self.config, self.temp_dir)
        checksum_files.read()
        checksum_files.remove("entry")
        self.assertChecksumsEqual({}, checksum_files)

    def test_merge(self):
        old_dir = os.path.join(self.temp_dir, "old")
        os.mkdir(old_dir)
        entry_path = os.path.join(self.temp_dir, "entry")
        with open(entry_path, "w") as entry:
            print("data", end="", file=entry)
        shutil.copy(entry_path, os.path.join(old_dir, "entry"))
        self.create_checksum_files(["entry"], directory=old_dir)
        checksum_files = self.cls(self.config, self.temp_dir)
        checksum_files.merge([old_dir], "entry", ["entry"])
        self.assertChecksumsEqual({"entry": "data"}, checksum_files)

    def test_want_image(self):
        checksum_files = self.cls(self.config, self.temp_dir)
        self.assertTrue(checksum_files.want_image("foo.iso"))
        self.assertFalse(checksum_files.want_image("foo.list"))
        self.assertTrue(checksum_files.want_image("foo.squashfs"))

    def test_merge_all(self):
        old_dir = os.path.join(self.temp_dir, "old")
        os.mkdir(old_dir)
        old_iso_hppa_path = os.path.join(self.temp_dir, "old", "foo-hppa.raw")
        with open(old_iso_hppa_path, "w") as old_iso_hppa:
            print("foo-hppa.raw", end="", file=old_iso_hppa)
        old_iso_i386_path = os.path.join(self.temp_dir, "old", "foo-i386.raw")
        with open(old_iso_i386_path, "w") as old_iso_i386:
            print("foo-i386.raw", end="", file=old_iso_i386)
        self.create_checksum_files(
            ["foo-hppa.raw", "foo-i386.raw"], directory=old_dir)
        iso_amd64_path = os.path.join(self.temp_dir, "foo-amd64.iso")
        with open(iso_amd64_path, "w") as iso_amd64:
            print("foo-amd64.iso", end="", file=iso_amd64)
        touch(os.path.join(self.temp_dir, "foo-amd64.list"))
        shutil.copy(
            old_iso_hppa_path, os.path.join(self.temp_dir, "foo-hppa.iso"))
        shutil.copy(
            old_iso_i386_path, os.path.join(self.temp_dir, "foo-i386.iso"))
        checksum_files = self.cls(self.config, self.temp_dir)
        checksum_files.merge_all([old_dir], map_expr=r"s/\.iso$/.raw/")
        self.assertChecksumsEqual({
            "foo-amd64.iso": "foo-amd64.iso",
            "foo-hppa.iso": "foo-hppa.raw",
            "foo-i386.iso": "foo-i386.raw",
            }, checksum_files)

    def test_write(self):
        checksum_files = self.cls(
            self.config, self.temp_dir, sign=False)
        for name in "1", "2":
            entry_path = os.path.join(self.temp_dir, name)
            with open(entry_path, "w") as entry:
                print(name, end="", file=entry)
            checksum_files.add(name)
        checksum_files.write()
        for cf in checksum_files.checksum_files:
            self.assertEqual(
                0,
                subprocess.call(
                    [self.files_and_commands[cf.name], "-c", "--status",
                     cf.name], cwd=self.temp_dir))

    def test_context_manager(self):
        for name in "1", "2":
            entry_path = os.path.join(self.temp_dir, name)
            with open(entry_path, "w") as entry:
                print(name, end="", file=entry)
        self.create_checksum_files(["1", "2"])
        with self.cls(
            self.config, self.temp_dir, sign=False) as checksum_files:
            self.assertChecksumsEqual({"1": "1", "2": "2"}, checksum_files)
            checksum_files.remove("1")
        with open(os.path.join(self.temp_dir, "MD5SUMS")) as md5sums:
            self.assertEqual(
                "%s *2\n" % hashlib.md5("2").hexdigest(), md5sums.read())
        with open(os.path.join(self.temp_dir, "SHA1SUMS")) as sha1sums:
            self.assertEqual(
                "%s *2\n" % hashlib.sha1("2").hexdigest(), sha1sums.read())
        with open(os.path.join(self.temp_dir, "SHA256SUMS")) as sha256sums:
            self.assertEqual(
                "%s *2\n" % hashlib.sha256("2").hexdigest(), sha256sums.read())

    def test_checksum_directory(self):
        old_dir = os.path.join(self.temp_dir, "old")
        os.mkdir(old_dir)
        old_iso_hppa_path = os.path.join(self.temp_dir, "old", "foo-hppa.raw")
        with open(old_iso_hppa_path, "w") as old_iso_hppa:
            print("foo-hppa.raw", end="", file=old_iso_hppa)
        old_iso_i386_path = os.path.join(self.temp_dir, "old", "foo-i386.raw")
        with open(old_iso_i386_path, "w") as old_iso_i386:
            print("foo-i386.raw", end="", file=old_iso_i386)
        self.create_checksum_files(
            ["foo-hppa.raw", "foo-i386.raw"], directory=old_dir)
        iso_amd64_path = os.path.join(self.temp_dir, "foo-amd64.iso")
        with open(iso_amd64_path, "w") as iso_amd64:
            print("foo-amd64.iso", end="", file=iso_amd64)
        touch(os.path.join(self.temp_dir, "foo-amd64.list"))
        shutil.copy(
            old_iso_hppa_path, os.path.join(self.temp_dir, "foo-hppa.iso"))
        shutil.copy(
            old_iso_i386_path, os.path.join(self.temp_dir, "foo-i386.iso"))
        checksum_directory(
            self.config, self.temp_dir, old_directories=[old_dir],
            map_expr=r"s/\.iso$/.raw/")
        with open(os.path.join(self.temp_dir, "MD5SUMS")) as md5sums:
            digests = (
                hashlib.md5("foo-amd64.iso").hexdigest(),
                hashlib.md5("foo-hppa.raw").hexdigest(),
                hashlib.md5("foo-i386.raw").hexdigest(),
                )
            self.assertEqual(dedent("""\
                %s *foo-amd64.iso
                %s *foo-hppa.iso
                %s *foo-i386.iso
                """) % digests, md5sums.read())

class TestMetalinkChecksumFileSet(TestChecksumFileSet):
    def setUp(self):
        super(TestMetalinkChecksumFileSet, self).setUp()
        self.files_and_commands = {
            "MD5SUMS-metalink": "md5sum",
            }
        self.cls = MetalinkChecksumFileSet

    def assertChecksumsEqual(self, entry_data, checksum_files):
        expected = {
            "MD5SUMS-metalink": dict(
                (k, hashlib.md5(v).hexdigest())
                for k, v in entry_data.items()),
            }
        observed = dict(
            (cf.name, cf.entries) for cf in checksum_files.checksum_files)
        self.assertEqual(expected, observed)

    def test_want_image(self):
        checksum_files = self.cls(self.config, self.temp_dir)
        self.assertTrue(checksum_files.want_image("foo.metalink"))
        self.assertFalse(checksum_files.want_image("foo.iso"))

    def test_merge_all(self):
        old_dir = os.path.join(self.temp_dir, "old")
        os.mkdir(old_dir)
        old_iso_i386_path = os.path.join(self.temp_dir, "old", "foo-i386.iso")
        with open(old_iso_i386_path, "w") as old_iso_i386:
            print("foo-i386.iso", end="", file=old_iso_i386)
        old_metalink_i386_path = os.path.join(
            self.temp_dir, "old", "foo-i386.metalink")
        with open(old_metalink_i386_path, "w") as old_metalink_i386:
            print("foo-i386.metalink", end="", file=old_metalink_i386)
        self.create_checksum_files(
            ["foo-i386.metalink"], directory=old_dir)
        metalink_amd64_path = os.path.join(self.temp_dir, "foo-amd64.metalink")
        with open(metalink_amd64_path, "w") as metalink_amd64:
            print("foo-amd64.metalink", end="", file=metalink_amd64)
        touch(os.path.join(self.temp_dir, "foo-amd64.list"))
        shutil.copy(
            old_metalink_i386_path,
            os.path.join(self.temp_dir, "foo-i386.metalink"))
        checksum_files = self.cls(self.config, self.temp_dir)
        checksum_files.merge_all([old_dir])
        self.assertChecksumsEqual({
            "foo-amd64.metalink": "foo-amd64.metalink",
            "foo-i386.metalink": "foo-i386.metalink",
            }, checksum_files)

    def test_context_manager(self):
        for name in "1", "2":
            entry_path = os.path.join(self.temp_dir, name)
            with open(entry_path, "w") as entry:
                print(name, end="", file=entry)
        self.create_checksum_files(["1", "2"])
        with self.cls(
            self.config, self.temp_dir, sign=False) as checksum_files:
            self.assertChecksumsEqual({"1": "1", "2": "2"}, checksum_files)
            checksum_files.remove("1")
        with open(os.path.join(self.temp_dir, "MD5SUMS-metalink")) as md5sums:
            self.assertEqual(
                "%s *2\n" % hashlib.md5("2").hexdigest(), md5sums.read())

    def test_checksum_directory(self):
        old_dir = os.path.join(self.temp_dir, "old")
        os.mkdir(old_dir)
        old_iso_i386_path = os.path.join(self.temp_dir, "old", "foo-i386.iso")
        with open(old_iso_i386_path, "w") as old_iso_i386:
            print("foo-i386.iso", end="", file=old_iso_i386)
        old_metalink_i386_path = os.path.join(
            self.temp_dir, "old", "foo-i386.metalink")
        with open(old_metalink_i386_path, "w") as old_metalink_i386:
            print("foo-i386.metalink", end="", file=old_metalink_i386)
        self.create_checksum_files(
            ["foo-i386.metalink"], directory=old_dir)
        metalink_amd64_path = os.path.join(self.temp_dir, "foo-amd64.metalink")
        with open(metalink_amd64_path, "w") as metalink_amd64:
            print("foo-amd64.metalink", end="", file=metalink_amd64)
        touch(os.path.join(self.temp_dir, "foo-amd64.list"))
        shutil.copy(
            old_metalink_i386_path,
            os.path.join(self.temp_dir, "foo-i386.metalink"))
        metalink_checksum_directory(
            self.config, self.temp_dir, old_directories=[old_dir])
        with open(os.path.join(self.temp_dir, "MD5SUMS-metalink")) as md5sums:
            digests = (
                hashlib.md5("foo-amd64.metalink").hexdigest(),
                hashlib.md5("foo-i386.metalink").hexdigest(),
                )
            self.assertEqual(dedent("""\
                %s *foo-amd64.metalink
                %s *foo-i386.metalink
                """) % digests, md5sums.read())
