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

"""Keep track of image build identifiers."""

from __future__ import print_function

import os
import time

from cdimage.atomicfile import AtomicFile


def next_build_id(config, image_type):
    if not image_type:
        image_type = "daily"
    stamp = os.path.join(
        config.root, "etc",
        ".next-build-suffix-%s-%s-%s" % (
            config["PROJECT"], config.series, image_type))
    date = config["DATE"] or time.strftime("%Y%m%d")

    if config["DATE_SUFFIX"]:
        suffix = int(config["DATE_SUFFIX"])
    else:
        suffix = 0
        if os.path.exists(stamp):
            with open(stamp) as stamp_file:
                for line in stamp_file:
                    if line.startswith("%s:" % date):
                        suffix = int(line.split(":")[1])
                        break

    if suffix:
        if not config["DEBUG"]:
            with AtomicFile(stamp) as stamp_file:
                print("%s:%d" % (date, suffix + 1), file=stamp_file)
        return "%s.%d" % (date, suffix)
    else:
        if not config["DEBUG"]:
            with AtomicFile(stamp) as stamp_file:
                print("%s:1" % date, file=stamp_file)
        return date
