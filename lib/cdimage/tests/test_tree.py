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

"""Unit tests for cdimage.tree."""

from __future__ import print_function

__metaclass__ = type

import os
from textwrap import dedent

from cdimage.config import all_series, Config, Series
from cdimage import osextras
from cdimage.tests.helpers import TestCase, touch
from cdimage.tree import DailyTree, DailyTreePublisher, SimpleTree, Tree


class TestTree(TestCase):
    def setUp(self):
        super(TestTree, self).setUp()
        self.use_temp_dir()
        self.config = Config(read=False)
        self.tree = Tree(self.config, self.temp_dir)

    def test_path_to_project(self):
        self.assertEqual("kubuntu", self.tree.path_to_project("kubuntu/foo"))
        self.assertEqual("ubuntu", self.tree.path_to_project("foo"))
        self.assertEqual("ubuntu", self.tree.path_to_project("ubuntu/foo/bar"))

    def test_manifest_file_allowed_passes_good_extensions(self):
        paths = [
            os.path.join(self.temp_dir, name)
            for name in (
                "foo.iso", "foo.img", "foo.img.gz",
                "foo.tar.gz", "foo.tar.xz",
                )]
        for path in paths:
            touch(path)
            self.assertTrue(self.tree.manifest_file_allowed(path))

    def test_manifest_file_allowed_fails_bad_extensions(self):
        paths = [
            os.path.join(self.temp_dir, name)
            for name in ("foo.txt", "foo")]
        for path in paths:
            touch(path)
            self.assertFalse(self.tree.manifest_file_allowed(path))

    def test_manifest_file_allowed_fails_directories(self):
        path = os.path.join(self.temp_dir, "dir.iso")
        os.mkdir(path)
        self.assertFalse(self.tree.manifest_file_allowed(path))


class TestDailyTree(TestCase):
    def setUp(self):
        super(TestDailyTree, self).setUp()
        self.use_temp_dir()
        self.config = Config(read=False)
        self.tree = DailyTree(self.config, self.temp_dir)

    def test_default_directory(self):
        self.config.root = self.temp_dir
        self.assertEqual(
            os.path.join(self.temp_dir, "www", "full"),
            DailyTree(self.config).directory)

    def test_name_to_series(self):
        self.assertEqual(
            "warty", self.tree.name_to_series("warty-install-i386.iso"))
        self.assertRaises(ValueError, self.tree.name_to_series, "README")

    def test_path_to_manifest(self):
        iso = "kubuntu/hoary-install-i386.iso"
        iso_path = os.path.join(self.temp_dir, iso)
        os.makedirs(os.path.dirname(iso_path))
        touch(iso_path)
        self.assertEqual(
            "kubuntu\thoary\t/%s\t0" % iso, self.tree.path_to_manifest(iso))

    def test_manifest_files_includes_current(self):
        daily = os.path.join(self.temp_dir, "daily")
        os.makedirs(os.path.join(daily, "20120806"))
        os.symlink("20120806", os.path.join(daily, "current"))
        touch(os.path.join(daily, "20120806", "warty-install-i386.iso"))
        self.assertEqual(
            ["daily/current/warty-install-i386.iso"],
            list(self.tree.manifest_files()))

    def test_manifest(self):
        daily = os.path.join(self.temp_dir, "daily")
        os.makedirs(os.path.join(daily, "20120806"))
        os.symlink("20120806", os.path.join(daily, "current"))
        touch(os.path.join(daily, "20120806", "hoary-install-i386.iso"))
        daily_live = os.path.join(self.temp_dir, "daily-live")
        os.makedirs(os.path.join(daily_live, "20120806"))
        os.symlink("20120806", os.path.join(daily_live, "current"))
        touch(os.path.join(daily_live, "20120806", "hoary-live-i386.iso"))
        self.assertEqual([
            "ubuntu\thoary\t/daily-live/current/hoary-live-i386.iso\t0",
            "ubuntu\thoary\t/daily/current/hoary-install-i386.iso\t0",
            ], self.tree.manifest())


class TestDailyTreePublisher(TestCase):
    def setUp(self):
        super(TestDailyTreePublisher, self).setUp()
        self.use_temp_dir()
        self.config = Config(read=False)
        self.config.root = self.temp_dir
        self.config["DIST"] = Series.latest()

    def make_publisher(self, project, image_type, **kwargs):
        self.config["PROJECT"] = project
        self.tree = DailyTree(self.config)
        publisher = DailyTreePublisher(self.tree, image_type, **kwargs)
        osextras.ensuredir(publisher.image_output)
        osextras.ensuredir(publisher.britney_report)
        osextras.ensuredir(publisher.full_tree)
        return publisher

    def test_image_output(self):
        self.config["DIST"] = Series.find_by_name("hoary")
        self.assertEqual(
            os.path.join(
                self.config.root, "scratch", "kubuntu", "hoary", "daily",
                "debian-cd"),
            self.make_publisher("kubuntu", "daily").image_output)

    def test_britney_report(self):
        self.assertEqual(
            os.path.join(
                self.config.root, "britney", "report", "kubuntu", "daily"),
            self.make_publisher("kubuntu", "daily").britney_report)

    def test_full_tree(self):
        self.assertEqual(
            os.path.join(self.config.root, "www", "full"),
            self.make_publisher("ubuntu", "daily").full_tree)
        self.assertEqual(
            os.path.join(self.config.root, "www", "full", "kubuntu"),
            self.make_publisher("kubuntu", "daily").full_tree)

    def test_image_type_dir(self):
        publisher = self.make_publisher("ubuntu", "daily-live")
        self.assertEqual("daily-live", publisher.image_type_dir)
        self.config["DIST"] = Series.find_by_name("hoary")
        self.assertEqual(
            os.path.join("hoary", "daily-live"), publisher.image_type_dir)

    def test_publish_base(self):
        self.assertEqual(
            os.path.join(
                self.config.root, "www", "full", "kubuntu", "daily-live"),
            self.make_publisher("kubuntu", "daily-live").publish_base)
        self.config["DIST"] = Series.find_by_name("hoary")
        self.assertEqual(
            os.path.join(
                self.config.root, "www", "full",
                "kubuntu", "hoary", "daily-live"),
            self.make_publisher("kubuntu", "daily-live").publish_base)

    def test_metalink_dirs(self):
        basedir = os.path.join(self.config.root, "www", "full")
        date = "20120912"
        publisher = self.make_publisher("ubuntu", "daily-live")
        self.assertEqual(
            (basedir, os.path.join("daily-live", date)),
            publisher.metalink_dirs(date))
        self.config["DIST"] = Series.find_by_name("hoary")
        self.assertEqual(
            (basedir, os.path.join("hoary", "daily-live", date)),
            publisher.metalink_dirs(date))
        publisher = self.make_publisher("kubuntu", "daily-live")
        self.config["DIST"] = Series.latest()
        self.assertEqual(
            (basedir, os.path.join("kubuntu", "daily-live", date)),
            publisher.metalink_dirs(date))
        self.config["DIST"] = Series.find_by_name("hoary")
        self.assertEqual(
            (basedir, os.path.join("kubuntu", "hoary", "daily-live", date)),
            publisher.metalink_dirs(date))

    def test_publish_type(self):
        for image_type, project, dist, publish_type in (
            ("daily-preinstalled", "ubuntu-netbook", "precise",
             "preinstalled-netbook"),
            ("daily-preinstalled", "ubuntu-headless", "precise",
             "preinstalled-headless"),
            ("daily-preinstalled", "ubuntu-server", "precise",
             "preinstalled-server"),
            ("daily-preinstalled", "ubuntu", "precise",
             "preinstalled-desktop"),
            ("daily-live", "edubuntu", "edgy", "live"),
            ("daily-live", "edubuntu", "feisty", "desktop"),
            ("daily-live", "kubuntu-netbook", "lucid", "netbook"),
            ("daily-live", "ubuntu-mid", "lucid", "mid"),
            ("daily-live", "ubuntu-moblin-remix", "lucid", "moblin-remix"),
            ("daily-live", "ubuntu-netbook", "hardy", "netbook"),
            ("daily-live", "ubuntu-server", "hardy", "live"),
            ("daily-live", "ubuntu", "breezy", "live"),
            ("daily-live", "ubuntu", "dapper", "desktop"),
            ("ports_dvd", "ubuntu", "hardy", "dvd"),
            ("dvd", "kubuntu", "hardy", "dvd"),
            ("daily", "edubuntu", "edgy", "install"),
            ("daily", "edubuntu", "feisty", "server"),
            ("daily", "edubuntu", "gutsy", "server"),
            ("daily", "edubuntu", "hardy", "addon"),
            ("daily", "jeos", "hardy", "jeos"),
            ("daily", "ubuntu-core", "precise", "core"),
            ("daily", "ubuntu-server", "breezy", "install"),
            ("daily", "ubuntu-server", "dapper", "server"),
            ("daily", "ubuntu", "breezy", "install"),
            ("daily", "ubuntu", "dapper", "alternate"),
            ):
            self.config["DIST"] = Series.find_by_name(dist)
            publisher = self.make_publisher(project, image_type)
            self.assertEqual(publish_type, publisher.publish_type)

    def test_size_limit(self):
        for project, dist, image_type, size_limit in (
            ("edubuntu", None, "daily-preinstalled", 4700372992),
            ("edubuntu", None, "dvd", 4700372992),
            ("ubuntustudio", None, "dvd", 4700372992),
            ("ubuntu-mid", None, "daily-live", 1073741824),
            ("ubuntu-moblin-remix", None, "daily-live", 1073741824),
            ("kubuntu-active", None, "daily-live", 1073741824),
            ("kubuntu", None, "daily-live", 1000000000),
            ("ubuntu", None, "dvd", 4700372992),
            ("ubuntu", "precise", "daily-live", 736665600),
            ("ubuntu", "quantal", "daily-live", 801000000),
            ):
            if dist is not None:
                self.config["DIST"] = Series.find_by_name(dist)
            publisher = self.make_publisher(project, image_type)
            self.assertEqual(size_limit, publisher.size_limit)

    def test_size_limit_extension(self):
        publisher = self.make_publisher("ubuntu", "daily")
        self.assertEqual(
            1024 * 1024 * 1024, publisher.size_limit_extension("img"))
        self.assertEqual(
            1024 * 1024 * 1024, publisher.size_limit_extension("tar.gz"))
        self.assertEqual(
            publisher.size_limit, publisher.size_limit_extension("iso"))

    def test_size_limit_extension_edubuntu(self):
        # size_limit_extension has special-casing for Edubuntu.
        publisher = self.make_publisher("edubuntu", "daily")
        self.assertEqual(
            publisher.size_limit, publisher.size_limit_extension("img"))
        self.assertEqual(
            publisher.size_limit, publisher.size_limit_extension("tar.gz"))
        self.assertEqual(
            publisher.size_limit, publisher.size_limit_extension("iso"))

    def test_new_publish_dir_honours_no_copy(self):
        self.config["CDIMAGE_NOCOPY"] = "1"
        publisher = self.make_publisher("ubuntu", "daily")
        publish_current = os.path.join(publisher.publish_base, "current")
        osextras.ensuredir(publish_current)
        touch(os.path.join(
            publish_current, "%s-alternate-i386.iso" % self.config.series))
        publisher.new_publish_dir("20120807")
        self.assertEqual(
            [], os.listdir(os.path.join(publisher.publish_base, "20120807")))

    def test_new_publish_dir_copies_same_series(self):
        publisher = self.make_publisher("ubuntu", "daily")
        publish_current = os.path.join(publisher.publish_base, "current")
        osextras.ensuredir(publish_current)
        image = "%s-alternate-i386.iso" % self.config.series
        touch(os.path.join(publish_current, image))
        publisher.new_publish_dir("20120807")
        self.assertEqual(
            [image],
            os.listdir(os.path.join(publisher.publish_base, "20120807")))

    def test_new_publish_dir_skips_different_series(self):
        publisher = self.make_publisher("ubuntu", "daily")
        publish_current = os.path.join(publisher.publish_base, "current")
        osextras.ensuredir(publish_current)
        image = "warty-alternate-i386.iso"
        touch(os.path.join(publish_current, image))
        publisher.new_publish_dir("20120807")
        self.assertEqual(
            [], os.listdir(os.path.join(publisher.publish_base, "20120807")))

    def test_jigdo_ports_powerpc(self):
        publisher = self.make_publisher("ubuntu", "daily")
        for series in all_series[:5]:
            publisher.config["DIST"] = series
            self.assertFalse(publisher.jigdo_ports("powerpc"))
        for series in all_series[5:]:
            publisher.config["DIST"] = series
            self.assertTrue(publisher.jigdo_ports("powerpc"))

    def test_jigdo_ports_sparc(self):
        publisher = self.make_publisher("ubuntu", "daily")
        for series in all_series[:3] + all_series[7:]:
            publisher.config["DIST"] = series
            self.assertTrue(publisher.jigdo_ports("sparc"))
        for series in all_series[3:7]:
            publisher.config["DIST"] = series
            self.assertFalse(publisher.jigdo_ports("sparc"))

    def test_jigdo_ports(self):
        publisher = self.make_publisher("ubuntu", "daily")
        for arch in ("amd64", "i386"):
            self.assertFalse(publisher.jigdo_ports(arch))
        for arch in ("armel", "armhf", "hppa", "ia64", "lpia"):
            self.assertTrue(publisher.jigdo_ports(arch))

    def test_replace_jigdo_mirror(self):
        jigdo_path = os.path.join(self.temp_dir, "jigdo")
        with open(jigdo_path, "w") as jigdo:
            print("[Servers]", file=jigdo)
            print("Debian=http://archive.ubuntu.com/ubuntu/ --try-last",
                  file=jigdo)
        publisher = self.make_publisher("ubuntu", "daily")
        publisher.replace_jigdo_mirror(
            jigdo_path, "http://archive.ubuntu.com/ubuntu/",
            "http://ports.ubuntu.com/ubuntu-ports")
        with open(jigdo_path) as jigdo:
            self.assertEqual(dedent("""\
                [Servers]
                Debian=http://ports.ubuntu.com/ubuntu-ports --try-last
                """), jigdo.read())

    def test_publish_binary(self):
        publisher = self.make_publisher(
            "ubuntu", "daily-live", try_zsyncmake=False)
        source_dir = os.path.join(publisher.image_output, "i386")
        os.mkdir(source_dir)
        touch(os.path.join(
            source_dir, "%s-desktop-i386.raw" % self.config.series))
        touch(os.path.join(
            source_dir, "%s-desktop-i386.list" % self.config.series))
        touch(os.path.join(
            source_dir, "%s-desktop-i386.manifest" % self.config.series))
        self.capture_logging()
        list(publisher.publish_binary("desktop", "i386", "20120807"))
        self.assertLogEqual([
            "Publishing i386 ...",
            "Unknown file type 'empty'; assuming .iso",
            "Publishing i386 live manifest ...",
            ])
        target_dir = os.path.join(publisher.publish_base, "20120807")
        self.assertEqual([], os.listdir(source_dir))
        self.assertEqual([
            "%s-desktop-i386.iso" % self.config.series,
            "%s-desktop-i386.list" % self.config.series,
            "%s-desktop-i386.manifest" % self.config.series,
            ], sorted(os.listdir(target_dir)))

    def test_publish_source(self):
        publisher = self.make_publisher(
            "ubuntu", "daily-live", try_zsyncmake=False)
        source_dir = os.path.join(publisher.image_output, "src")
        os.mkdir(source_dir)
        touch(os.path.join(source_dir, "%s-src-1.raw" % self.config.series))
        touch(os.path.join(source_dir, "%s-src-1.list" % self.config.series))
        touch(os.path.join(source_dir, "%s-src-1.jigdo" % self.config.series))
        touch(os.path.join(
            source_dir, "%s-src-1.template" % self.config.series))
        touch(os.path.join(source_dir, "%s-src-2.raw" % self.config.series))
        touch(os.path.join(source_dir, "%s-src-2.list" % self.config.series))
        touch(os.path.join(source_dir, "%s-src-2.jigdo" % self.config.series))
        touch(os.path.join(
            source_dir, "%s-src-2.template" % self.config.series))
        self.capture_logging()
        list(publisher.publish_source("20120807"))
        self.assertLogEqual([
            "Publishing source 1 ...",
            "Publishing source 1 jigdo ...",
            "Publishing source 2 ...",
            "Publishing source 2 jigdo ...",
            ])
        target_dir = os.path.join(publisher.publish_base, "20120807", "source")
        self.assertEqual([], os.listdir(source_dir))
        self.assertEqual([
            "%s-src-1.iso" % self.config.series,
            "%s-src-1.jigdo" % self.config.series,
            "%s-src-1.list" % self.config.series,
            "%s-src-1.template" % self.config.series,
            "%s-src-2.iso" % self.config.series,
            "%s-src-2.jigdo" % self.config.series,
            "%s-src-2.list" % self.config.series,
            "%s-src-2.template" % self.config.series,
            ], sorted(os.listdir(target_dir)))

    def test_publish(self):
        self.config["ARCHES"] = "i386"
        self.config["CDIMAGE_INSTALL_BASE"] = "1"
        publisher = self.make_publisher(
            "ubuntu", "daily-live", try_zsyncmake=False)
        source_dir = os.path.join(publisher.image_output, "i386")
        os.mkdir(source_dir)
        touch(os.path.join(
            source_dir, "%s-desktop-i386.raw" % self.config.series))
        touch(os.path.join(
            source_dir, "%s-desktop-i386.list" % self.config.series))
        touch(os.path.join(
            source_dir, "%s-desktop-i386.manifest" % self.config.series))
        touch(os.path.join(
            publisher.britney_report, "%s_probs.html" % self.config.series))
        # TODO: until make-web-indices is converted to Python
        bin_dir = os.path.join(self.config.root, "bin")
        os.mkdir(bin_dir)
        os.symlink("/bin/true", os.path.join(bin_dir, "make-web-indices"))
        os.symlink("/bin/true", os.path.join(bin_dir, "make-metalink"))
        os.symlink("/bin/true", os.path.join(bin_dir, "post-qa"))
        os.mkdir(os.path.join(self.config.root, "etc"))
        self.capture_logging()
        publisher.publish("20120807")
        self.assertLogEqual([
            "Publishing i386 ...",
            "Unknown file type 'empty'; assuming .iso",
            "Publishing i386 live manifest ...",
            "No keys found; not signing images.",
            "No keys found; not signing images.",
            ])
        target_dir = os.path.join(publisher.publish_base, "20120807")
        self.assertEqual([], os.listdir(source_dir))
        self.assertEqual(sorted([
            "MD5SUMS",
            "SHA1SUMS",
            "SHA256SUMS",
            "%s-desktop-i386.iso" % self.config.series,
            "%s-desktop-i386.list" % self.config.series,
            "%s-desktop-i386.manifest" % self.config.series,
            "report.html",
            ]), sorted(os.listdir(target_dir)))


class TestSimpleTree(TestCase):
    def setUp(self):
        super(TestSimpleTree, self).setUp()
        self.use_temp_dir()
        self.config = Config(read=False)
        self.tree = SimpleTree(self.config, self.temp_dir)

    def test_default_directory(self):
        self.config.root = self.temp_dir
        self.assertEqual(
            os.path.join(self.temp_dir, "www", "simple"),
            SimpleTree(self.config).directory)

    def test_name_to_series(self):
        self.assertEqual(
            "warty", self.tree.name_to_series("ubuntu-4.10-install-i386.iso"))
        self.assertRaises(ValueError, self.tree.name_to_series, "foo-bar.iso")

    def test_path_to_manifest(self):
        iso = "kubuntu/.pool/kubuntu-5.04-install-i386.iso"
        iso_path = os.path.join(self.temp_dir, iso)
        os.makedirs(os.path.dirname(iso_path))
        touch(iso_path)
        self.assertEqual(
            "kubuntu\thoary\t/%s\t0" % iso, self.tree.path_to_manifest(iso))

    def test_manifest_files_prefers_non_pool(self):
        pool = os.path.join(self.temp_dir, ".pool")
        os.mkdir(pool)
        touch(os.path.join(pool, "ubuntu-4.10-install-i386.iso"))
        dist = os.path.join(self.temp_dir, "warty")
        os.mkdir(dist)
        os.symlink(
            os.path.join(os.pardir, ".pool", "ubuntu-4.10-install-i386.iso"),
            os.path.join(dist, "ubuntu-4.10-install-i386.iso"))
        self.assertEqual(
            ["warty/ubuntu-4.10-install-i386.iso"],
            list(self.tree.manifest_files()))

    def test_manifest_files_includes_non_duplicates_in_pool(self):
        pool = os.path.join(self.temp_dir, ".pool")
        os.mkdir(pool)
        touch(os.path.join(pool, "ubuntu-4.10-install-i386.iso"))
        touch(os.path.join(pool, "ubuntu-4.10-install-amd64.iso"))
        dist = os.path.join(self.temp_dir, "warty")
        os.mkdir(dist)
        os.symlink(
            os.path.join(os.pardir, ".pool", "ubuntu-4.10-install-i386.iso"),
            os.path.join(dist, "ubuntu-4.10-install-i386.iso"))
        self.assertEqual([
            "warty/ubuntu-4.10-install-i386.iso",
            ".pool/ubuntu-4.10-install-amd64.iso",
            ], list(self.tree.manifest_files()))

    def test_manifest(self):
        pool = os.path.join(self.temp_dir, "kubuntu", ".pool")
        os.makedirs(pool)
        touch(os.path.join(pool, "kubuntu-5.04-install-i386.iso"))
        touch(os.path.join(pool, "kubuntu-5.04-live-i386.iso"))
        dist = os.path.join(self.temp_dir, "kubuntu", "hoary")
        os.makedirs(dist)
        os.symlink(
            os.path.join(os.pardir, ".pool", "kubuntu-5.04-install-i386.iso"),
            os.path.join(dist, "kubuntu-5.04-install-i386.iso"))
        os.symlink(
            os.path.join(os.pardir, ".pool", "kubuntu-5.04-live-i386.iso"),
            os.path.join(dist, "kubuntu-5.04-live-i386.iso"))
        self.assertEqual([
            "kubuntu\thoary\t/kubuntu/hoary/kubuntu-5.04-install-i386.iso\t0",
            "kubuntu\thoary\t/kubuntu/hoary/kubuntu-5.04-live-i386.iso\t0",
            ], self.tree.manifest())
