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

"""Image publication trees."""

from __future__ import print_function

__metaclass__ = type

from itertools import count
import os
import shutil
import socket
import stat
import subprocess

from cdimage.atomicfile import AtomicFile
from cdimage.checksums import (
    ChecksumFileSet,
    checksum_directory,
    metalink_checksum_directory,
    )
from cdimage.config import Series
from cdimage.log import logger
from cdimage import osextras


# TODO: This should be in a configuration file.  ALL_PROJECTS is not
# currently suitable, because it only lists projects currently being built,
# but manifest generation needs to know about anything currently in a
# published tree.
projects = [
    "edubuntu",
    "gobuntu",
    "jeos",
    "kubuntu",
    "kubuntu-active",
    "kubuntu-netbook",
    "lubuntu",
    "mythbuntu",
    "ubuntu",
    "ubuntu-headless",
    "ubuntu-netbook",
    "ubuntu-server",
    "ubuntustudio",
    "xubuntu",
    ]


def zsyncmake(infile, outfile, url):
    command = ["zsyncmake"]
    if infile.endswith(".gz"):
        command.append("-Z")
    command.extend(["-o", outfile, "-u", url, infile])
    if subprocess.call(command) != 0:
        logger.info("Trying again with block size 2048 ...")
        command[1:1] = ["-b", "2048"]
        subprocess.check_call(command)


class Tree:
    """A publication tree."""

    def __init__(self, config, directory):
        self.config = config
        self.directory = directory

    def path_to_project(self, path):
        """Determine the project for a file based on its tree-relative path."""
        first_dir = path.split("/")[0]
        if first_dir in projects:
            return first_dir
        else:
            return "ubuntu"

    def name_to_series(self, name):
        """Return the series for a file basename."""
        raise NotImplementedError

    def path_to_manifest(self, path):
        """Return a manifest file entry for a tree-relative path.

        May raise ValueError for unrecognised file naming schemes.
        """
        if path.startswith("tocd"):
            return None
        project = self.path_to_project(path)
        base = os.path.basename(path)
        try:
            series = self.name_to_series(base)
        except ValueError:
            return None
        size = os.stat(os.path.join(self.directory, path)).st_size
        return "%s\t%s\t/%s\t%d" % (project, series, path, size)

    def manifest_file_allowed(self, path):
        """Return true if a given file is allowed in the manifest."""
        if (path.endswith(".iso") or path.endswith(".img") or
            path.endswith(".img.gz") or path.endswith(".tar.gz") or
            path.endswith(".tar.xz")):
            if stat.S_ISREG(os.stat(path).st_mode):
                return True
        return False

    def manifest_files(self):
        """Yield all the files to include in a manifest of this tree."""
        raise NotImplementedError

    def manifest(self):
        """Return a manifest of this tree as a sequence of lines."""
        return sorted(filter(
            lambda line: line is not None,
            (self.path_to_manifest(path) for path in self.manifest_files())))


class Publisher:
    """A object that can publish images to a tree."""

    def __init__(self, tree, image_type):
        self.tree = tree
        self.config = tree.config
        self.project = self.config["PROJECT"]
        self.image_type = image_type


class DailyTree(Tree):
    """A publication tree containing daily builds."""

    def __init__(self, config, directory=None):
        if directory is None:
            directory = os.path.join(config.root, "www", "full")
        super(DailyTree, self).__init__(config, directory)

    def name_to_series(self, name):
        """Return the series for a file basename."""
        dist = name.split("-")[0]
        return Series.find_by_name(dist)

    def manifest_files(self):
        """Yield all the files to include in a manifest of this tree."""
        seen_inodes = []
        for dirpath, dirnames, filenames in os.walk(
            self.directory, followlinks=True):
            # Detect loops.
            st = os.stat(dirpath)
            dev_ino = (st.st_dev, st.st_ino)
            seen_inodes.append(dev_ino)
            for i in range(len(dirnames) - 1, -1, -1):
                st = os.stat(os.path.join(dirpath, dirnames[i]))
                dev_ino = (st.st_dev, st.st_ino)
                if dev_ino in seen_inodes:
                    del dirnames[i]

            if "current" in dirpath.split(os.sep):
                relative_dirpath = dirpath[len(self.directory) + 1:]
                for filename in filenames:
                    path = os.path.join(dirpath, filename)
                    if self.manifest_file_allowed(path):
                        yield os.path.join(relative_dirpath, filename)

            if not dirnames:
                seen_inodes.pop()


class DailyTreePublisher(Publisher):
    """An object that can publish daily builds."""

    def __init__(self, tree, image_type, try_zsyncmake=True):
        super(DailyTreePublisher, self).__init__(tree, image_type)
        self.checksum_dirs = []
        self.try_zsyncmake = try_zsyncmake  # for testing

    @property
    def image_output(self):
        return os.path.join(
            self.config.root, "scratch", self.project, self.config.series,
            self.image_type, "debian-cd")

    @property
    def britney_report(self):
        return os.path.join(
            self.config.root, "britney", "report", self.project,
            self.image_type)

    @property
    def full_tree(self):
        if self.project == "ubuntu":
            return self.tree.directory
        else:
            return os.path.join(self.tree.directory, self.project)

    @property
    def image_type_dir(self):
        image_type_dir = self.image_type.replace("_", "/")
        if not self.config["DIST"].is_latest:
            image_type_dir = os.path.join(self.config.series, image_type_dir)
        return image_type_dir

    @property
    def publish_base(self):
        return os.path.join(self.full_tree, self.image_type_dir)

    def metalink_dirs(self, date):
        if self.project == "ubuntu":
            reldir = os.path.join(self.image_type_dir, date)
        else:
            reldir = os.path.join(self.project, self.image_type_dir, date)
        return self.tree.directory, reldir

    @property
    def publish_type(self):
        if self.image_type.endswith("-preinstalled"):
            if self.project == "ubuntu-netbook":
                return "preinstalled-netbook"
            elif self.project == "ubuntu-headless":
                return "preinstalled-headless"
            elif self.project == "ubuntu-server":
                return "preinstalled-server"
            else:
                return "preinstalled-desktop"
        elif self.image_type.endswith("-live"):
            if self.project == "edubuntu":
                if self.config["DIST"] <= "edgy":
                    return "live"
                else:
                    return "desktop"
            elif self.project == "ubuntu-mid":
                return "mid"
            elif self.project == "ubuntu-moblin-remix":
                return "moblin-remix"
            elif self.project in ("ubuntu-netbook", "kubuntu-netbook"):
                return "netbook"
            elif self.project == "ubuntu-server":
                return "live"
            else:
                if self.config["DIST"] <= "breezy":
                    return "live"
                else:
                    return "desktop"
        elif self.image_type.endswith("_dvd") or self.image_type == "dvd":
            return "dvd"
        else:
            if self.project == "edubuntu":
                if self.config["DIST"] <= "edgy":
                    return "install"
                elif self.config["DIST"] <= "gutsy":
                    return "server"
                else:
                    return "addon"
            elif self.project == "ubuntu-server":
                if self.config["DIST"] <= "breezy":
                    return "install"
                else:
                    return "server"
            elif self.project == "jeos":
                return "jeos"
            elif self.project == "ubuntu-core":
                return "core"
            else:
                if self.config["DIST"] <= "breezy":
                    return "install"
                else:
                    return "alternate"

    @property
    def size_limit(self):
        if self.project in ("edubuntu", "ubuntustudio"):
            # All Edubuntu images are DVD sized (including arm).
            # Ubuntu Studio is always DVD-sized for now.
            return 4700372992
        elif self.project in (
            "ubuntu-mid", "ubuntu-moblin-remix", "kubuntu-active"):
            # Mobile images are designed for USB drives; arbitrarily pick
            # 1GB as a limit.
            return 1024 * 1024 * 1024
        elif self.project == "kubuntu":
            # Kubuntu limit of 1GB [quantal]
            return 1000000000
        elif (self.project == "ubuntu" and self.publish_type != "dvd" and
              self.config["DIST"] >= "quantal"):
            # Ubuntu quantal onward has an (arbitrary) 801MB limit.
            return 801000000
        else:
            if self.publish_type == "dvd":
                # http://en.wikipedia.org/wiki/DVD_plus_RW
                return 4700372992
            else:
                # http://en.wikipedia.org/wiki/CD-ROM#Capacity gives a
                # maximum of 737280000; RedBook requires reserving 300
                # sectors, so we do the same here Just In Case.  If we need
                # to surpass this limit we should rigorously re-test and
                # check again with ProMese, the CD pressing vendor.
                return 736665600

    def size_limit_extension(self, extension):
        """Some output file types have adjusted limits.  Cope with this."""
        # TODO: Shouldn't this be per-project/publish_type instead?
        if self.project == "edubuntu":
            return self.size_limit
        elif extension == "img" or extension.endswith(".gz"):
            return 1024 * 1024 * 1024
        else:
            return self.size_limit

    def new_publish_dir(self, date):
        """Copy previous published tree as a starting point for a new one.

        This allows single-architecture rebuilds to carry over other
        architectures from previous builds.
        """
        publish_base = self.publish_base
        publish_date = os.path.join(publish_base, date)
        publish_current = os.path.join(publish_base, "current")
        osextras.ensuredir(publish_date)
        if not self.config["CDIMAGE_NOCOPY"]:
            for name in sorted(osextras.listdir_force(publish_current)):
                if name.startswith("%s-" % self.config.series):
                    os.link(
                        os.path.join(publish_current, name),
                        os.path.join(publish_date, name))

    def detect_image_extension(self, source_prefix):
        subp = subprocess.Popen(
            ["file", "-b", "%s.raw" % source_prefix], stdout=subprocess.PIPE,
            universal_newlines=True)
        output = subp.communicate()[0].rstrip("\n")
        if output.startswith("# "):
            output = output[2:]

        if output.startswith("ISO 9660 CD-ROM filesystem data "):
            return "iso"
        elif output.startswith("x86 boot sector"):
            return "img"
        elif output.startswith("gzip compressed data"):
            with open("%s.type" % source_prefix) as compressed_type:
                real_output = compressed_type.readline().rstrip("\n")
            if real_output.startswith("ISO 9660 CD-ROM filesystem data "):
                return "iso.gz"
            elif real_output.startswith("x86 boot sector"):
                return "img.gz"
            elif real_output.startswith("tar archive"):
                return "tar.gz"
            else:
                logger.warning(
                    "Unknown compressed file type '%s'; assuming .img.gz" %
                    real_output)
                return "img.gz"
        else:
            logger.warning("Unknown file type '%s'; assuming .iso" % output)
            return "iso"

    def jigdo_ports(self, arch):
        series = self.config["DIST"]
        cpuarch = arch.split("+")[0]
        if cpuarch == "powerpc":
            # https://lists.ubuntu.com/archives/ubuntu-announce/2007-February/000098.html
            if series > "edgy":
                return True
        elif cpuarch == "sparc":
            # https://lists.ubuntu.com/archives/ubuntu-devel-announce/2008-March/000400.html
            if series < "dapper" or series > "gutsy":
                return True
        elif cpuarch in ("armel", "armhf", "hppa", "ia64", "lpia"):
            return True
        return False

    def replace_jigdo_mirror(self, path, from_mirror, to_mirror):
        with open(path) as jigdo_in:
            with AtomicFile(path) as jigdo_out:
                from_line = "Debian=%s" % from_mirror
                to_line = "Debian=%s" % to_mirror
                for line in jigdo_in:
                    jigdo_out.write(line.replace(from_line, to_line))

    def publish_binary(self, publish_type, arch, date):
        in_prefix = "%s-%s-%s" % (self.config.series, publish_type, arch)
        out_prefix = "%s-%s-%s" % (self.config.series, publish_type, arch)
        source_dir = os.path.join(self.image_output, arch)
        source_prefix = os.path.join(source_dir, in_prefix)
        target_dir = os.path.join(self.publish_base, date)
        target_prefix = os.path.join(target_dir, out_prefix)

        if not os.path.exists("%s.raw" % source_prefix):
            logger.warning("No %s image for %s!" % (publish_type, arch))
            for name in osextras.listdir_force(target_dir):
                if name.startswith("%s." % out_prefix):
                    os.unlink(os.path.join(target_dir, name))
            return

        logger.info("Publishing %s ..." % arch)
        osextras.ensuredir(target_dir)
        extension = self.detect_image_extension(source_prefix)
        shutil.move(
            "%s.raw" % source_prefix, "%s.%s" % (target_prefix, extension))
        if os.path.exists("%s.list" % source_prefix):
            shutil.move("%s.list" % source_prefix, "%s.list" % target_prefix)
        self.checksum_dirs.append(source_dir)
        with ChecksumFileSet(
            self.config, target_dir, sign=False) as checksum_files:
            checksum_files.remove("%s.%s" % (out_prefix, extension))

        # Jigdo integration
        if os.path.exists("%s.jigdo" % source_prefix):
            logger.info("Publishing %s jigdo ..." % arch)
            shutil.move("%s.jigdo" % source_prefix, "%s.jigdo" % target_prefix)
            shutil.move(
                "%s.template" % source_prefix, "%s.template" % target_prefix)
            if self.jigdo_ports(arch):
                self.replace_jigdo_mirror(
                    "%s.jigdo" % target_prefix,
                    "http://archive.ubuntu.com/ubuntu",
                    "http://ports.ubuntu.com/ubuntu-ports")
        else:
            osextras.unlink_force("%s.jigdo" % target_prefix)
            osextras.unlink_force("%s.template" % target_prefix)

        # Live filesystem manifests
        if os.path.exists("%s.manifest" % source_prefix):
            logger.info("Publishing %s live manifest ..." % arch)
            shutil.move(
                "%s.manifest" % source_prefix, "%s.manifest" % target_prefix)
        else:
            osextras.unlink_force("%s.manifest" % target_prefix)

        if (self.config["CDIMAGE_SQUASHFS_BASE"] and
            os.path.exists("%s.squashfs" % source_prefix)):
            logger.info("Publishing %s squashfs ..." % arch)
            shutil.move(
                "%s.squashfs" % source_prefix, "%s.squashfs" % target_prefix)
        else:
            osextras.unlink_force("%s.squashfs" % target_prefix)

        # Flashable Android boot images
        if os.path.exists("%s.bootimg" % source_prefix):
            logger.info("Publishing %s abootimg bootloader images ..." % arch)
            shutil.move(
                "%s.bootimg" % source_prefix, "%s.bootimg" % target_prefix)

        # zsync metafiles
        if self.try_zsyncmake and osextras.find_on_path("zsyncmake"):
            logger.info("Making %s zsync metafile ..." % arch)
            osextras.unlink_force("%s.%s.zsync" % (target_prefix, extension))
            zsyncmake(
                "%s.%s" % (target_prefix, extension),
                "%s.%s.zsync" % (target_prefix, extension),
                "%s.%s" % (out_prefix, extension))

        size = os.stat("%s.%s" % (target_prefix, extension)).st_size
        if size > self.size_limit_extension(extension):
            with open("%s.OVERSIZED" % target_prefix, "a"):
                pass
        else:
            osextras.unlink_force("%s.OVERSIZED" % target_prefix)

        yield os.path.join(self.project, self.image_type_dir, in_prefix)

    def publish_source(self, date):
        for i in count(1):
            in_prefix = "%s-src-%d" % (self.config.series, i)
            out_prefix = "%s-src-%d" % (self.config.series, i)
            source_dir = os.path.join(self.image_output, "src")
            source_prefix = os.path.join(source_dir, in_prefix)
            target_dir = os.path.join(self.publish_base, date, "source")
            target_prefix = os.path.join(target_dir, out_prefix)
            if not os.path.exists("%s.raw" % source_prefix):
                break

            logger.info("Publishing source %d ..." % i)
            osextras.ensuredir(target_dir)
            shutil.move("%s.raw" % source_prefix, "%s.iso" % target_prefix)
            shutil.move("%s.list" % source_prefix, "%s.list" % target_prefix)
            with ChecksumFileSet(
                self.config, target_dir, sign=False) as checksum_files:
                checksum_files.remove("%s.iso" % out_prefix)

            # Jigdo integration
            if os.path.exists("%s.jigdo" % source_prefix):
                logger.info("Publishing source %d jigdo ..." % i)
                shutil.move(
                    "%s.jigdo" % source_prefix, "%s.jigdo" % target_prefix)
                shutil.move(
                    "%s.template" % source_prefix,
                    "%s.template" % target_prefix)
            else:
                logger.warning("No jigdo for source %d!" % i)
                osextras.unlink_force("%s.jigdo" % target_prefix)
                osextras.unlink_force("%s.template" % target_prefix)

            # zsync metafiles
            if self.try_zsyncmake and osextras.find_on_path("zsyncmake"):
                logger.info("Making source %d zsync metafile ..." % i)
                osextras.unlink_force("%s.iso.zsync" % target_prefix)
                zsyncmake(
                    "%s.iso" % target_prefix, "%s.iso.zsync" % target_prefix,
                    "%s.iso" % out_prefix)

            yield os.path.join(
                self.project, self.image_type, "%s-src" % self.config.series)

    def publish(self, date):
        self.new_publish_dir(date)
        published = []
        self.checksum_dirs = []
        if not self.config["CDIMAGE_ONLYSOURCE"]:
            for arch in self.config.arches:
                published.extend(
                    list(self.publish_binary(self.publish_type, arch, date)))
            if self.project == "edubuntu" and self.publish_type == "server":
                for arch in self.config.arches:
                    published.extend(
                        list(self.publish_binary("serveraddon", arch, date)))
        published.extend(list(self.publish_source(date)))

        if not published:
            logger.warning("No CDs produced!")
            return

        target_dir = os.path.join(self.publish_base, date)

        source_report = os.path.join(
            self.britney_report, "%s_probs.html" % self.config.series)
        target_report = os.path.join(target_dir, "report.html")
        if (self.config["CDIMAGE_INSTALL_BASE"] and
            os.path.exists(source_report)):
            shutil.copy2(source_report, target_report)
        else:
            osextras.unlink_force(target_report)

        if not self.config["CDIMAGE_ONLYSOURCE"]:
            checksum_directory(
                self.config, target_dir, old_directories=self.checksum_dirs,
                map_expr=r"s/\.\(img\|img\.gz\|iso\|iso\.gz\|tar\.gz\)$/.raw/")
            subprocess.check_call(
                [os.path.join(self.config.root, "bin", "make-web-indices"),
                 target_dir, self.config.series, "daily"])

        target_dir_source = os.path.join(target_dir, "source")
        if os.path.isdir(target_dir_source):
            checksum_directory(
                self.config, target_dir_source,
                old_directories=[os.path.join(self.image_output, "src")],
                map_expr=r"s/\.\(img\|img\.gz\|iso\|iso\.gz\|tar\.gz\)$/.raw/")
            subprocess.check_call(
                [os.path.join(self.config.root, "bin", "make-web-indices"),
                 target_dir_source, self.config.series, "daily"])

        if (self.image_type.endswith("-live") or
            self.image_type.endswith("dvd")):
            # Create and publish metalink files.
            md5sums_metalink = os.path.join(target_dir, "MD5SUMS-metalink")
            md5sums_metalink_gpg = os.path.join(
                target_dir, "MD5SUMS-metalink.gpg")
            osextras.unlink_force(md5sums_metalink)
            osextras.unlink_force(md5sums_metalink_gpg)
            basedir, reldir = self.metalink_dirs(date)
            if subprocess.call([
                os.path.join(self.config.root, "bin", "make-metalink"),
                basedir, self.config.series, reldir, "cdimage.ubuntu.com",
                ]) == 0:
                metalink_checksum_directory(self.config, target_dir)
            else:
                for name in os.listdir(target_dir):
                    if name.endswith(".metalink"):
                        osextras.unlink_force(os.path.join(target_dir, name))

        publish_current = os.path.join(self.publish_base, "current")
        osextras.unlink_force(publish_current)
        os.symlink(date, publish_current)

        manifest_lock = os.path.join(
            self.config.root, "etc", ".lock-manifest-daily")
        try:
            subprocess.check_call(["lockfile", "-r", "4", manifest_lock])
        except subprocess.CalledProcessError:
            logger.error("Couldn't acquire manifest-daily lock!")
            raise
        try:
            manifest_daily = os.path.join(
                self.tree.directory, ".manifest-daily")
            with AtomicFile(manifest_daily) as manifest_daily_file:
                for line in self.tree.manifest():
                    print(line, file=manifest_daily_file)
            os.chmod(
                manifest_daily, os.stat(manifest_daily).st_mode | stat.S_IWGRP)

            # Create timestamps for this run.
            # TODO cjwatson 20120807: Shouldn't these be in www/full
            # rather than www/full[/project]?
            trace_dir = os.path.join(self.full_tree, ".trace")
            osextras.ensuredir(trace_dir)
            fqdn = socket.getfqdn()
            with open(os.path.join(trace_dir, fqdn), "w") as trace_file:
                subprocess.check_call(["date", "-u"], stdout=trace_file)
        finally:
            osextras.unlink_force(manifest_lock)

        subprocess.check_call([
            os.path.join(self.config.root, "bin", "post-qa"), date,
            ] + published)


class SimpleTree(Tree):
    """A publication tree containing a few important releases."""

    def __init__(self, config, directory=None):
        if directory is None:
            directory = os.path.join(config.root, "www", "simple")
        super(SimpleTree, self).__init__(config, directory)

    def name_to_series(self, name):
        """Return the series for a file basename."""
        version = name.split("-")[1]
        try:
            return Series.find_by_version(".".join(version.split(".")[:2]))
        except ValueError:
            logger.warning("Unknown version: %s" % version)
            raise

    def manifest_files(self):
        """Yield all the files to include in a manifest of this tree."""
        main_filenames = set()
        for dirpath, dirnames, filenames in os.walk(self.directory):
            relative_dirpath = dirpath[len(self.directory) + 1:]
            try:
                del dirnames[dirnames.index(".pool")]
            except ValueError:
                pass
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                if self.manifest_file_allowed(path):
                    main_filenames.add(filename)
                    yield os.path.join(relative_dirpath, filename)

        for dirpath, _, filenames in os.walk(self.directory):
            if os.path.basename(dirpath) == ".pool":
                relative_dirpath = dirpath[len(self.directory) + 1:]
                for filename in filenames:
                    if filename not in main_filenames:
                        path = os.path.join(dirpath, filename)
                        if self.manifest_file_allowed(path):
                            yield os.path.join(relative_dirpath, filename)
