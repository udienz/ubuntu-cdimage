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

"""Unit tests for cdimage.livefs."""

__metaclass__ = type

from cdimage.config import Config, Series
from cdimage.livefs import (
    flavours,
    live_builder,
    live_item_paths,
    live_project,
    livecd_base,
    NoLiveItem,
    split_arch,
    )
from cdimage.tests.helpers import TestCase


# This only needs to go up as far as the series livecd_base cares about.
all_series = [
    "warty",
    "hoary",
    "breezy",
    "dapper",
    "edgy",
    "feisty",
    "gutsy",
    "hardy",
    "intrepid",
    "jaunty",
    "karmic",
    "lucid",
    "maverick",
    "natty",
    "oneiric",
    "precise",
    "quantal",
    "raring",
    ]


class TestSplitArch(TestCase):
    def test_amd64(self):
        self.assertEqual(("amd64", ""), split_arch("amd64"))

    def test_amd64_mac(self):
        self.assertEqual(("amd64", ""), split_arch("amd64+mac"))

    def test_armhf_omap4(self):
        self.assertEqual(("armhf", "omap4"), split_arch("armhf+omap4"))

    def test_i386(self):
        self.assertEqual(("i386", ""), split_arch("i386"))


class TestLiveProject(TestCase):
    def assertProjectEqual(self, expected, project, series, **kwargs):
        config = Config(read=False)
        config["PROJECT"] = project
        config["DIST"] = Series.find_by_name(series)
        for key, value in kwargs.items():
            config[key.upper()] = value
        self.assertEqual(expected, live_project(config))

    def test_project_livecd_base(self):
        self.assertProjectEqual("base", "livecd-base", "dapper")

    def test_project_tocd3_1(self):
        self.assertProjectEqual("tocd", "tocd3.1", "breezy")

    def test_ubuntu_dvd(self):
        for series in all_series[:7]:
            self.assertProjectEqual(
                "ubuntu", "ubuntu", series, cdimage_dvd="1")
        for series in all_series[7:]:
            self.assertProjectEqual(
                "ubuntu-dvd", "ubuntu", series, cdimage_dvd="1")

    def test_kubuntu_dvd(self):
        for series in all_series[:7]:
            self.assertProjectEqual(
                "kubuntu", "kubuntu", series, cdimage_dvd="1")
        for series in all_series[7:]:
            self.assertProjectEqual(
                "kubuntu-dvd", "kubuntu", series, cdimage_dvd="1")

    def test_edubuntu_dvd(self):
        for series in all_series[:10]:
            self.assertProjectEqual(
                "edubuntu", "edubuntu", series, cdimage_dvd="1")
        for series in all_series[10:]:
            self.assertProjectEqual(
                "edubuntu-dvd", "edubuntu", series, cdimage_dvd="1")

    def test_ubuntustudio_dvd(self):
        for series in all_series[:15]:
            self.assertProjectEqual(
                "ubuntustudio", "ubuntustudio", series, cdimage_dvd="1")
        for series in all_series[15:]:
            self.assertProjectEqual(
                "ubuntustudio-dvd", "ubuntustudio", series, cdimage_dvd="1")


class TestLiveBuilder(TestCase):
    def assertBuilderEqual(self, expected, arch, series, project=None):
        config = Config(read=False)
        config["DIST"] = Series.find_by_name(series)
        if project is not None:
            config["PROJECT"] = project
        self.assertEqual(expected, live_builder(config, arch))

    def test_amd64(self):
        for series in all_series:
            self.assertBuilderEqual("kapok.buildd", "amd64", series)

    def test_armel(self):
        for series in all_series:
            self.assertBuilderEqual("annonaceae.buildd", "armel", series)

    def test_armhf(self):
        for series in all_series:
            self.assertBuilderEqual(
                "celbalrai.buildd", "armhf+omap4", series, project="ubuntu")
            self.assertBuilderEqual(
                "celbalrai.buildd", "armhf+omap", series, project="ubuntu")
            self.assertBuilderEqual(
                "celbalrai.buildd", "armhf+mx5", series, project="ubuntu")
            self.assertBuilderEqual(
                "celbalrai.buildd", "armhf+omap4", series,
                project="ubuntu-server")
            self.assertBuilderEqual(
                "celbalrai.buildd", "armhf+omap", series,
                project="ubuntu-server")
            self.assertBuilderEqual(
                "celbalrai.buildd", "armhf+somethingelse", series)

    def test_hppa(self):
        for series in all_series:
            self.assertBuilderEqual("castilla.buildd", "hppa", series)

    def test_i386(self):
        for series in all_series:
            self.assertBuilderEqual("cardamom.buildd", "i386", series)

    def test_ia64(self):
        for series in all_series:
            self.assertBuilderEqual("weddell.buildd", "ia64", series)

    def test_lpia(self):
        for series in all_series[:8]:
            self.assertBuilderEqual("cardamom.buildd", "lpia", series)
        for series in all_series[8:]:
            self.assertBuilderEqual("concordia.buildd", "lpia", series)

    def test_powerpc(self):
        for series in all_series:
            self.assertBuilderEqual("royal.buildd", "powerpc", series)

    def test_sparc(self):
        for series in all_series:
            self.assertBuilderEqual("vivies.buildd", "sparc", series)


class TestLiveCDBase(TestCase):
    def assertBaseEqual(self, expected, arch, project, series, **kwargs):
        config = Config(read=False)
        config["PROJECT"] = project
        config["DIST"] = Series.find_by_name(series)
        for key, value in kwargs.items():
            config[key.upper()] = value
        self.assertEqual(expected, livecd_base(config, arch))

    def base(self, builder, project, series):
        return "http://%s/~buildd/LiveCD/%s/%s/current" % (
            builder, series, project)

    def test_livecd_base_override(self):
        self.assertBaseEqual(
            "ftp://blah", "amd64", "ubuntu", "dapper",
            livecd_base="ftp://blah")

    def test_livecd_override(self):
        self.assertBaseEqual(
            "ftp://blah/quantal/ubuntu/current", "i386", "ubuntu", "quantal",
            livecd="ftp://blah")

    def test_subproject(self):
        for series in all_series:
            self.assertBaseEqual(
                self.base("cardamom.buildd", "ubuntu-wubi", series),
                "i386", "ubuntu", series, subproject="wubi")

    def test_no_subarch(self):
        for series in all_series:
            self.assertBaseEqual(
                self.base("cardamom.buildd", "ubuntu", series),
                "i386", "ubuntu", series)

    def test_subarch(self):
        self.assertBaseEqual(
            self.base("royal.buildd", "ubuntu-ps3", "gutsy"),
            "powerpc+ps3", "ubuntu", "gutsy")
        self.assertBaseEqual(
            self.base("annonaceae.buildd", "ubuntu-server-omap", "oneiric"),
            "armel+omap", "ubuntu-server", "oneiric")

    def test_ubuntu_defaults_locale(self):
        for series in all_series:
            self.assertBaseEqual(
                self.base("cardamom.buildd", "ubuntu-zh_CN", series),
                "i386", "ubuntu", series, ubuntu_defaults_locale="zh_CN")


class TestFlavours(TestCase):
    def assertFlavoursEqual(self, expected, arch, project, series):
        config = Config(read=False)
        config["PROJECT"] = project
        config["DIST"] = Series.find_by_name(series)
        self.assertEqual(expected.split(), flavours(config, arch))

    def test_amd64(self):
        for series in all_series[:4]:
            self.assertFlavoursEqual(
                "amd64-generic", "amd64", "ubuntu", series)
        for series in all_series[4:]:
            self.assertFlavoursEqual(
                "generic", "amd64", "ubuntu", series)
        for series in all_series[15:]:
            self.assertFlavoursEqual(
                "lowlatency", "amd64", "ubuntustudio", series)

    def test_armel(self):
        self.assertFlavoursEqual("imx51", "armel+imx51", "ubuntu", "jaunty")
        self.assertFlavoursEqual("imx51", "armel+omap", "ubuntu", "jaunty")
        for series in all_series[10:]:
            self.assertFlavoursEqual(
                "linaro-lt-mx5", "armel+mx5", "ubuntu", series)
            self.assertFlavoursEqual("omap", "armel+omap", "ubuntu", series)

    def test_armhf(self):
        for series in all_series:
            self.assertFlavoursEqual(
                "linaro-lt-mx5", "armhf+mx5", "ubuntu", series)
            self.assertFlavoursEqual("omap4", "armhf+omap4", "ubuntu", series)

    def test_hppa(self):
        for series in all_series:
            self.assertFlavoursEqual("hppa32 hppa64", "hppa", "ubuntu", series)

    def test_i386(self):
        for series in all_series[:4]:
            self.assertFlavoursEqual("i386", "i386", "ubuntu", series)
        for series in all_series[4:15] + all_series[17:]:
            self.assertFlavoursEqual("generic", "i386", "ubuntu", series)
        self.assertFlavoursEqual("generic-pae", "i386", "ubuntu", "precise")
        for series in all_series[4:]:
            self.assertFlavoursEqual("generic", "i386", "xubuntu", series)
            self.assertFlavoursEqual("generic", "i386", "lubuntu", series)
        self.assertFlavoursEqual(
            "lowlatency-pae", "i386", "ubuntustudio", "precise")
        for series in all_series[16:]:
            self.assertFlavoursEqual(
                "lowlatency", "i386", "ubuntustudio", series)

    def test_ia64(self):
        for series in all_series[:4]:
            self.assertFlavoursEqual(
                "itanium-smp mckinley-smp", "ia64", "ubuntu", series)
        for series in all_series[4:10]:
            self.assertFlavoursEqual(
                "itanium mckinley", "ia64", "ubuntu", series)
        for series in all_series[10:]:
            self.assertFlavoursEqual("ia64", "ia64", "ubuntu", series)

    def test_lpia(self):
        for series in all_series:
            self.assertFlavoursEqual("lpia", "lpia", "ubuntu", series)

    def test_powerpc(self):
        for series in all_series[:15]:
            self.assertFlavoursEqual(
                "powerpc powerpc64-smp", "powerpc", "ubuntu", series)
        for series in all_series[15:]:
            self.assertFlavoursEqual(
                "powerpc-smp powerpc64-smp", "powerpc", "ubuntu", series)
        self.assertFlavoursEqual("cell", "powerpc+ps3", "ubuntu", "gutsy")
        for series in all_series[7:15]:
            self.assertFlavoursEqual(
                "powerpc powerpc64-smp", "powerpc+ps3", "ubuntu", "hardy")
        for series in all_series[15:]:
            self.assertFlavoursEqual(
                "powerpc-smp powerpc64-smp", "powerpc+ps3", "ubuntu", series)

    def test_sparc(self):
        for series in all_series:
            self.assertFlavoursEqual("sparc64", "sparc", "ubuntu", series)


class TestLiveItemPaths(TestCase):
    def assertPathsEqual(self, expected, arch, item, project, series):
        config = Config(read=False)
        config["PROJECT"] = project
        config["DIST"] = Series.find_by_name(series)
        self.assertEqual(expected, list(live_item_paths(config, arch, item)))

    def assertNoPaths(self, arch, item, project, series):
        config = Config(read=False)
        config["PROJECT"] = project
        config["DIST"] = Series.find_by_name(series)
        self.assertRaises(
            NoLiveItem, next, live_item_paths(config, arch, item))

    def test_tocd3_fallback(self):
        for item in ("cloop", "manifest"):
            self.assertPathsEqual(
                ["/home/cjwatson/tocd3/livecd.tocd3.%s" % item],
                "i386", item, "tocd3", "hoary")

    def test_ubuntu_breezy_fallback(self):
        for item in ("cloop", "manifest"):
            for arch in ("amd64", "i386", "powerpc"):
                self.assertPathsEqual(
                    ["/home/cjwatson/breezy-live/ubuntu/livecd.%s.%s" %
                     (arch, item)],
                    arch, item, "ubuntu", "breezy")

    def test_desktop_items(self):
        for item in (
            "cloop", "squashfs", "manifest", "manifest-desktop",
            "manifest-remove", "size", "ext2", "ext3", "ext4", "rootfs.tar.gz",
            "tar.xz", "iso",
            ):
            self.assertPathsEqual(
                ["http://kapok.buildd/~buildd/LiveCD/precise/kubuntu/"
                 "current/livecd.kubuntu.%s" % item],
                "amd64", item, "kubuntu", "precise")
            self.assertPathsEqual(
                ["http://royal.buildd/~buildd/LiveCD/hardy/ubuntu-ps3/"
                 "current/livecd.ubuntu-ps3.%s" % item],
                "powerpc+ps3", item, "ubuntu", "hardy")

    def test_kernel_items(self):
        for item in ("kernel", "initrd", "bootimg"):
            root = "http://kapok.buildd/~buildd/LiveCD/precise/kubuntu/current"
            self.assertPathsEqual(
                ["%s/livecd.kubuntu.%s-generic" % (root, item)],
                "amd64", item, "kubuntu", "precise")
            root = ("http://royal.buildd/~buildd/LiveCD/hardy/ubuntu-ps3/"
                    "current")
            self.assertPathsEqual(
                ["%s/livecd.ubuntu-ps3.%s-powerpc" % (root, item),
                 "%s/livecd.ubuntu-ps3.%s-powerpc64-smp" % (root, item)],
                "powerpc+ps3", item, "ubuntu", "hardy")

    def test_kernel_efi_signed(self):
        self.assertNoPaths("i386", "kernel-efi-signed", "ubuntu", "quantal")
        self.assertNoPaths("amd64", "kernel-efi-signed", "ubuntu", "oneiric")
        root = "http://kapok.buildd/~buildd/LiveCD/precise/ubuntu/current"
        self.assertPathsEqual(
            ["%s/livecd.ubuntu.kernel-generic.efi.signed" % root],
            "amd64", "kernel-efi-signed", "ubuntu", "precise")
        root = "http://kapok.buildd/~buildd/LiveCD/quantal/ubuntu/current"
        self.assertPathsEqual(
            ["%s/livecd.ubuntu.kernel-generic.efi.signed" % root],
            "amd64", "kernel-efi-signed", "ubuntu", "quantal")

    # TODO: Since this is only of historical interest, we only test a small
    # number of cases at the moment.
    def test_winfoss(self):
        self.assertNoPaths("i386", "winfoss", "ubuntu", "warty")
        self.assertNoPaths("powerpc", "winfoss", "ubuntu", "hardy")
        self.assertPathsEqual(
            ["http://people.canonical.com/~henrik/winfoss/gutsy/"
             "ubuntu/current/ubuntu-winfoss-7.10.tar.gz"],
            "i386", "winfoss", "ubuntu", "karmic")
        self.assertNoPaths("i386", "winfoss", "ubuntu", "precise")

    def test_wubi(self):
        for series in all_series[:6]:
            self.assertNoPaths("amd64", "wubi", "ubuntu", series)
            self.assertNoPaths("i386", "wubi", "ubuntu", series)
        for series in all_series[6:]:
            path = "http://people.canonical.com/~evand/wubi/%s/stable" % series
            self.assertPathsEqual([path], "amd64", "wubi", "ubuntu", series)
            self.assertPathsEqual([path], "i386", "wubi", "ubuntu", series)
        self.assertNoPaths("i386", "wubi", "xubuntu", "precise")
        self.assertNoPaths("powerpc", "wubi", "ubuntu", "precise")

    def test_umenu(self):
        for series in all_series[:7] + all_series[8:]:
            self.assertNoPaths("amd64", "umenu", "ubuntu", series)
            self.assertNoPaths("i386", "umenu", "ubuntu", series)
        path = "http://people.canonical.com/~evand/umenu/stable"
        self.assertPathsEqual([path], "amd64", "umenu", "ubuntu", "hardy")
        self.assertPathsEqual([path], "i386", "umenu", "ubuntu", "hardy")
        self.assertNoPaths("powerpc", "umenu", "ubuntu", "hardy")

    def test_usb_creator(self):
        for series in all_series:
            path = ("http://people.canonical.com/~evand/usb-creator/%s/"
                    "stable" % series)
            self.assertPathsEqual(
                [path], "amd64", "usb-creator", "ubuntu", series)
            self.assertPathsEqual(
                [path], "i386", "usb-creator", "ubuntu", series)
        self.assertNoPaths("powerpc", "usb-creator", "ubuntu", "precise")

    def test_ltsp_squashfs(self):
        for series in all_series:
            path = ("http://cardamom.buildd/~buildd/LiveCD/%s/edubuntu/"
                    "current/livecd.edubuntu-ltsp.squashfs" % series)
            self.assertPathsEqual(
                [path], "amd64", "ltsp-squashfs", "edubuntu", series)
            self.assertPathsEqual(
                [path], "i386", "ltsp-squashfs", "edubuntu", series)
        self.assertNoPaths("powerpc", "ltsp-squashfs", "edubuntu", "precise")
