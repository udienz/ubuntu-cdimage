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

"""Live filesystems."""

__metaclass__ = type

from cdimage.config import Series


class UnknownArchitecture(Exception):
    pass


class NoLiveItem(Exception):
    pass


class UnknownLiveItem(Exception):
    pass


def split_arch(arch):
    arch_bits = arch.split("+", 1)
    if len(arch_bits) == 1:
        arch_bits.append("")
    cpuarch, subarch = arch_bits

    if cpuarch == "amd64" and subarch == "mac":
        # Use normal amd64 live image on amd64+mac.
        subarch = ""

    return cpuarch, subarch


def live_builder(config, arch):
    cpuarch, subarch = split_arch(arch)
    project = config["PROJECT"]
    series = config["DIST"]

    if cpuarch == "amd64":
        return "kapok.buildd"
    elif cpuarch == "armel":
        return "annonaceae.buildd"
    elif cpuarch == "armhf":
        # TODO: These builders should be separated out again; or, better,
        # moved into the LP build farm.
        if project == "ubuntu":
            if subarch == "omap4":
                return "celbalrai.buildd"
            elif subarch == "omap":
                return "celbalrai.buildd"
            elif subarch == "mx5":
                return "celbalrai.buildd"
        elif project == "ubuntu-server":
            if subarch == "omap4":
                return "celbalrai.buildd"
            elif subarch == "omap":
                return "celbalrai.buildd"
        return "celbalrai.buildd"
    elif cpuarch == "hppa":
        return "castilla.buildd"
    elif cpuarch == "i386":
        return "cardamom.buildd"
    elif cpuarch == "ia64":
        return "weddell.buildd"
    elif cpuarch == "lpia":
        if series <= "hardy":
            return "cardamom.buildd"
        else:
            return "concordia.buildd"
    elif cpuarch == "powerpc":
        return "royal.buildd"
    elif cpuarch == "sparc":
        return "vivies.buildd"
    else:
        raise UnknownArchitecture(
            "No live filesystem builder known for %s" % arch)


def live_project(config):
    project = config["PROJECT"]
    series = config["DIST"]

    if project == "livecd-base":
        liveproject = "base"
    elif project == "tocd3.1":
        liveproject = "tocd"
    else:
        liveproject = project
    if config["CDIMAGE_DVD"]:
        if ((project in ("ubuntu", "kubuntu") and series >= "hardy") or
            (project == "edubuntu" and series >= "karmic") or
            (project == "ubuntustudio" and series >= "precise")):
                liveproject += "-dvd"
    return liveproject


def livecd_base(config, arch):
    if config["LIVECD_BASE"]:
        return config["LIVECD_BASE"]

    cpuarch, subarch = split_arch(arch)
    project = config["PROJECT"]
    series = config["DIST"]

    if config["LIVECD"]:
        root = config["LIVECD"]
    else:
        root = "http://%s/~buildd/LiveCD" % live_builder(config, arch)

    liveproject = live_project(config)
    if config["SUBPROJECT"]:
        liveproject += "-%s" % config["SUBPROJECT"]
    if subarch:
        liveproject += "-%s" % subarch
    if config["UBUNTU_DEFAULTS_LOCALE"]:
        liveproject += "-%s" % config["UBUNTU_DEFAULTS_LOCALE"]

    return "%s/%s/%s/current" % (root, series, liveproject)


def flavours(config, arch):
    cpuarch, subarch = split_arch(arch)
    project = config["PROJECT"]
    series = config["DIST"]

    if cpuarch == "amd64":
        if series <= "dapper":
            return ["amd64-generic"]
        elif series <= "oneiric":
            return ["generic"]
        else:
            if project == "ubuntustudio":
                return ["lowlatency"]
            else:
                return ["generic"]
    elif cpuarch == "armel":
        if series == "jaunty":
            # We don't have any fallback flavour on armel.
            return ["imx51"]
        else:
            if subarch == "mx5":
                return ["linaro-lt-mx5"]
            else:
                # Assume one kernel flavour for each subarch named like the
                # subarch.
                return [subarch]
    elif cpuarch == "armhf":
        if subarch == "mx5":
            return ["linaro-lt-mx5"]
        else:
            return [subarch]
    elif cpuarch == "hppa":
        return ["hppa32", "hppa64"]
    elif cpuarch == "i386":
        if series <= "dapper":
            return ["i386"]
        elif series <= "oneiric":
            return ["generic"]
        elif series <= "precise":
            if project in ("xubuntu", "lubuntu"):
                return ["generic"]
            elif project == "ubuntustudio":
                return ["lowlatency-pae"]
            else:
                return ["generic-pae"]
        else:
            if project == "ubuntustudio":
                return ["lowlatency"]
            else:
                return ["generic"]
    elif cpuarch == "ia64":
        if series <= "dapper":
            return ["itanium-smp", "mckinley-smp"]
        elif series <= "jaunty":
            return ["itanium", "mckinley"]
        else:
            return ["ia64"]
    elif cpuarch == "lpia":
        return ["lpia"]
    elif cpuarch == "powerpc":
        if subarch == "ps3" and series <= "gutsy":
            return ["cell"]
        elif series <= "oneiric":
            return ["powerpc", "powerpc64-smp"]
        else:
            return ["powerpc-smp", "powerpc64-smp"]
    elif cpuarch == "sparc":
        return ["sparc64"]
    else:
        raise UnknownArchitecture(
            "No live filesystem source known for %s" % arch)


def live_item_path_winfoss(config, arch):
    # This is a mess of special cases.  Fortunately it is now only of
    # historical interest.
    cpuarch, subarch = split_arch(arch)
    project = config["PROJECT"]
    series = config["DIST"]

    if series == "warty" or cpuarch not in ("amd64", "i386"):
        raise NoLiveItem

    maitri = "http://maitri.ubuntu.com/theopencd"
    henrik = "http://people.canonical.com/~henrik/winfoss"

    if project == "ubuntu":
        if series == "hoary":
            if cpuarch == "i386":
                return "%s/ubuntu/winfoss/latest/Hoary-WinFOSS.tgz" % maitri
            elif cpuarch == "amd64":
                return ("%s/ubuntu/amd64/latest/"
                        "Hoary-WinFOSS-amd64.tgz" % maitri)
        elif series == "breezy":
            return "%s/winfoss/ubuntu/current/Ubuntu-WinFOSS-5.10.tgz" % maitri
        elif series >= "dapper" and series <= "karmic":
            if series > "gutsy":
                series = Series.find_by_name("gutsy")
            return "%s/%s/ubuntu/current/ubuntu-winfoss-%s.tar.gz" % (
                henrik, series, series.version)
    elif project == "kubuntu":
        if series == "hoary" and cpuarch == "i386":
            return ("%s/kubuntu/winfoss/latest/"
                    "Kubuntu-WinFOSS-i386.tgz" % maitri)
        elif series == "breezy":
            if cpuarch == "i386":
                return ("%s/winfoss/kubuntu/current/"
                       "Kubuntu-WinFOSS-5.10.tgz" % maitri)
            elif cpuarch == "amd64":
                return ("%s/winfoss/kubuntu-AMD/current/"
                       "Kubuntu-WinFOSS-5.10-AMD.tgz" % maitri)
        elif series >= "dapper" and series <= "karmic":
            if series > "gutsy":
                series = Series.find_by_name("gutsy")
            return "%s/%s/kubuntu/current/kubuntu-winfoss-%s.tar.gz" % (
                henrik, series, series.version)
    elif project == "edubuntu":
        if series >= "feisty" and series <= "karmic":
            if series > "gutsy":
                series = Series.find_by_name("gutsy")
            return "%s/%s/edubuntu/current/edubuntu-winfoss-%s.tar.gz" % (
                henrik, series, series.version)
    elif project == "tocd3" and cpuarch == "i386":
            return "%s/tocd3/fsm/TOCD3.tgz" % maitri
    elif project == "tocd3.1" and cpuarch == "i386":
            return "%s/winfoss/tocd3.1/current/TOCD-31.tgz" % maitri

    raise NoLiveItem


def live_item_paths(config, arch, item):
    cpuarch, subarch = split_arch(arch)
    project = config["PROJECT"]
    series = config["DIST"]
    root = livecd_base(config, arch)
    liveproject = live_project(config)
    if subarch:
        liveproject_subarch = "%s-%s" % (liveproject, subarch)
    else:
        liveproject_subarch = liveproject

    if item in (
        "cloop", "squashfs", "manifest", "manifest-desktop", "manifest-remove",
        "size", "ext2", "ext3", "ext4", "rootfs.tar.gz", "tar.xz", "iso",
        ):
        if project == "tocd3":
            # auto-purged - reverting to plan B
            yield "/home/cjwatson/tocd3/livecd.tocd3.%s" % item
        elif project == "ubuntu" and series == "breezy":
            # auto-purged - reverting to plan B
            yield "/home/cjwatson/breezy-live/ubuntu/livecd.%s.%s" % (
                arch, item)
        else:
            yield "%s/livecd.%s.%s" % (root, liveproject_subarch, item)
    elif item in ("kernel", "initrd", "bootimg"):
        for flavour in flavours(config, arch):
            yield "%s/livecd.%s.%s-%s" % (
                root, liveproject_subarch, item, flavour)
    elif item == "kernel-efi-signed":
        if series >= "precise" and arch == "amd64":
            for flavour in flavours(config, arch):
                yield "%s/livecd.%s.kernel-%s.efi.signed" % (
                    root, liveproject_subarch, flavour)
        else:
            raise NoLiveItem
    elif item == "winfoss":
        yield live_item_path_winfoss(config, arch)
    elif item == "wubi":
        if (project != "xubuntu" and arch in ("amd64", "i386") and
            series >= "gutsy"):
            yield ("http://people.canonical.com/~evand/wubi/%s/stable" %
                   series.name)
        else:
            raise NoLiveItem
    elif item == "umenu":
        if arch in ("amd64", "i386") and series == "hardy":
            yield "http://people.canonical.com/~evand/umenu/stable"
        else:
            raise NoLiveItem
    elif item == "usb-creator":
        if arch in ("amd64", "i386"):
            yield ("http://people.canonical.com/~evand/usb-creator/%s/"
                   "stable" % series.name)
        else:
            raise NoLiveItem
    elif item == "ltsp-squashfs":
        if arch == "amd64":
            # use i386 LTSP image on amd64 too
            root = livecd_base(config, "i386")
        if arch in ("amd64", "i386"):
            yield "%s/livecd.%s-ltsp.squashfs" % (root, liveproject)
        else:
            raise NoLiveItem
    else:
        raise UnknownLiveItem("Unknown live filesystem item '%s'" % item)
