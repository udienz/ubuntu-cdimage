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

"""Mirror handling."""

from __future__ import print_function

__metaclass__ = type

import os
import subprocess


class UnknownMirror(Exception):
    pass


def find_mirror(config, arch):
    return os.path.join(config.root, "ftp")


class UnknownManifestFile(Exception):
    pass


def _trigger_mirror(key, user, host, background=False):
    print("%s:" % host)
    command = [
        "ssh", "-i", key,
        "-o", "StrictHostKeyChecking no",
        "-o", "BatchMode yes",
        "%s@%s" % (user, host),
        "./releases-sync",
        ]
    if background:
        subprocess.Popen(command)
    else:
        subprocess.call(command)


def trigger_mirrors(config):
    # Check for non-existent files in .manifest.
    simple_tree = os.path.join(config.root, "www", "simple")
    with open(os.path.join(simple_tree, ".manifest")) as manifest:
        for line in manifest:
            name = line.rstrip("\n").split()[2]
            if not os.path.exists(os.path.join(simple_tree, name.lstrip("/"))):
                raise UnknownManifestFile(
                    ".manifest has non-existent file %s" % name)

    secret = os.path.join(config.root, "secret")
    home_secret = os.path.expanduser("~/secret")
    if os.path.isdir(home_secret):
        secret = home_secret
    key = os.path.join(secret, "auckland")

    for host in config["TRIGGER_MIRRORS"].split():
        _trigger_mirror(key, "archvsync", host)

    for host in config["TRIGGER_MIRRORS_ASYNC"].split():
        _trigger_mirror(key, "archvsync", host, background=True)
