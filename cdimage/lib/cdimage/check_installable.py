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

"""Check package installability on images."""

from __future__ import print_function

import atexit
import gzip
import os
import shutil
import subprocess
import tempfile

from cdimage.log import logger
from cdimage.osextras import mkemptydir, run_bounded


def _check_installable_dirs(config):
    britney = os.path.join(config.root, "britney")
    image_top = os.path.join(
        config.root, "scratch", config["PROJECT"], config.series,
        config["IMAGE_TYPE"], "tmp")
    live = os.path.join(
        config.root, "scratch", config["PROJECT"], config.series,
        config["IMAGE_TYPE"], "live")
    data = os.path.join(
        britney, "data", config["PROJECT"], config["IMAGE_TYPE"],
        config.series)
    return britney, image_top, live, data


_tempdir = None


def _ensure_tempdir():
    global _tempdir
    if not _tempdir:
        _tempdir = tempfile.mkdtemp(prefix="cdimage")
        atexit.register(shutil.rmtree, _tempdir)


def _prepare_check_installable(config):
    _, image_top, live, data = _check_installable_dirs(config)
    mkemptydir(data)

    for fullarch in config.arches:
        arch = fullarch.split("+")[0]

        packages = os.path.join(data, "Packages_%s" % arch)
        with open(packages, "w") as packages_file:
            if config["CDIMAGE_SQUASHFS_BASE"]:
                squashfs = os.path.join(live, "%s.squashfs" % fullarch)
                if os.path.exists(squashfs):
                    _ensure_tempdir()
                    with open("/dev/null", "w") as devnull:
                        subprocess.check_call([
                            "unsquashfs",
                            "-d", os.path.join(_tempdir, fullarch),
                            squashfs, "/var/lib/dpkg/status",
                            ], stdout=devnull)
                    status_path = os.path.join(
                        _tempdir, fullarch, "var", "lib", "dpkg", "status")
                    with open(os.path.join(status_path)) as status:
                        subprocess.call([
                            "grep-dctrl", "-XFStatus", "install ok installed",
                            ], stdin=status, stdout=packages_file)

            for component in "main", "restricted", "universe", "multiverse":
                packages_gz = os.path.join(
                    image_top, "%s-%s" % (config.series, fullarch), "CD1",
                    "dists", config.series, component, "binary-%s" % arch,
                    "Packages.gz")
                if os.path.exists(packages_gz):
                    packages_gz_file = gzip.GzipFile(packages_gz)
                    try:
                        packages_file.write(packages_gz_file.read())
                    finally:
                        packages_gz_file.close()

        if os.stat(packages).st_size == 0:
            logger.warning(
                "No Packages.gz for %s/%s; not checking" %
                (config.series, arch))
            os.unlink(packages)

    with open(os.path.join(data, "Sources"), "w"):
        pass


def _check_installable_command(config):
    britney, _, _, data = _check_installable_dirs(config)
    report_dir = os.path.join(
        britney, "report", config["PROJECT"], config["IMAGE_TYPE"])
    mkemptydir(report_dir)
    return [
        os.path.join(britney, "rptprobs.sh"), data,
        os.path.join(report_dir, "%s_probs.html" % config.series),
        "%s %s" % (config["CAPPROJECT"], config.series),
        ]


def check_installable(config):
    _prepare_check_installable(config)
    # Sometimes this inexplicably hangs on a futex. We'll give it thirty
    # seconds and then kill it.
    run_bounded(30, _check_installable_command(config))
