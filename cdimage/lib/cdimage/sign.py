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

"""Sign a file with the cdimage key."""

import os
import subprocess

from cdimage.log import logger


def _gnupg_files(config):
    gpgconf = os.path.join(config["GNUPG_DIR"], "gpg.conf")
    secring = os.path.join(config["GNUPG_DIR"], "secring.gpg")
    pubring = os.path.join(config["GNUPG_DIR"], "pubring.gpg")
    trustdb = os.path.join(config["GNUPG_DIR"], "trustdb.gpg")
    return gpgconf, secring, pubring, trustdb


def can_sign(config):
    gpgconf, secring, pubring, trustdb = _gnupg_files(config)
    if (not os.path.exists(secring) or not os.path.exists(pubring) or
        not os.path.exists(trustdb) or not config["SIGNING_KEYID"]):
        logger.warning("No keys found; not signing images.")
        return False
    return True


def _signing_command(config):
    gpgconf, secring, pubring, trustdb = _gnupg_files(config)
    return [
        "gpg", "--options", gpgconf,
        "--no-default-keyring",
        "--secret-keyring", secring,
        "--keyring", pubring,
        "--trustdb-name", trustdb,
        "--default-key", config["SIGNING_KEYID"],
        "--no-options", "--batch", "--no-tty",
        "--armour", "--detach-sign",
        ]


def sign_cdimage(config, path):
    if not can_sign(config):
        return False

    with open(path, "rb") as infile:
        with open("%s.gpg" % path, "wb") as outfile:
            try:
                subprocess.check_call(
                    _signing_command(config), stdin=infile, stdout=outfile)
            except subprocess.CalledProcessError:
                try:
                    os.unlink("%s.gpg" % path)
                except OSError:
                    pass
                raise
    return True
