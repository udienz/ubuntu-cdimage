# -*- coding: UTF-8 -*-
"""Fetch package lists from a Debian-format archive as apt tag files."""

# Copyright (c) 2004, 2005, 2006, 2007 Canonical Ltd.
#
# Germinate is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2, or (at your option) any
# later version.
#
# Germinate is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Germinate; see the file COPYING.  If not, write to the Free
# Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
# 02110-1301, USA.

import os
import urllib2
import tempfile
import shutil

class TagFile:
    def __init__(self, mirrors, source_mirrors=None):
        self.mirrors = mirrors
        if source_mirrors:
            self.source_mirrors = source_mirrors
        else:
            self.source_mirrors = mirrors

    def open_tag_files(self, mirrors, dirname, tagfile_type,
                       dist, component, ftppath):
        def open_tag_file(mirror, suffix):
            """Download an apt tag file if needed, then open it."""
            url = (mirror + "dists/" + dist + "/" + component + "/" + ftppath +
                   suffix)
            req = urllib2.Request(url)
            filename = None

            if req.get_type() != "file":
                filename = "%s_%s_%s_%s" % (req.get_host(), dist, component, tagfile_type)
            else:
                # Make a more or less dummy filename for local URLs.
                filename = os.path.split(req.get_selector())[0].replace(os.sep, "_")

            fullname = os.path.join(dirname, filename)
            if req.get_type() == "file":
                # Always refresh.  TODO: we should use If-Modified-Since for
                # remote HTTP tag files.
                try:
                    os.unlink(fullname)
                except OSError:
                    pass
            if not os.path.exists(fullname):
                print "Downloading", req.get_full_url(), "file ..."

                compressed = os.path.join(dirname, filename + suffix)
                try:
                    url_f = urllib2.urlopen(req)
                    compressed_f = open(compressed, "w")
                    compressed_f.write(url_f.read())
                    compressed_f.close()
                    url_f.close()

                    # apt_pkg is weird and won't accept GzipFile
                    if suffix:
                        print "Decompressing", req.get_full_url(), "file ..."

                        if suffix == ".gz":
                            import gzip
                            compressed_f = gzip.GzipFile(compressed)
                        elif suffix == ".bz2":
                            import bz2
                            compressed_f = bz2.BZ2File(compressed)
                        else:
                            raise RuntimeError("Unknown suffix '%s'" % suffix)

                        f = open(fullname, "w")
                        print >>f, compressed_f.read(),
                        f.flush()
                        f.close()

                        compressed_f.close()
                finally:
                    if suffix:
                        try:
                            os.unlink(compressed)
                        except OSError:
                            pass

            return open(fullname, "r")

        tag_files = []
        for mirror in mirrors:
            tag_file = None
            for suffix in (".bz2", ".gz", ""):
                try:
                    tag_file = open_tag_file(mirror, suffix)
                    tag_files.append(tag_file)
                    break
                except (IOError, OSError):
                    pass
        if len(tag_files) == 0:
            raise IOError, "no %s files found" % tagfile_type
        return tag_files

    def feed(self, g, dists, components, arch, cleanup=False):
        if cleanup:
            dirname = tempfile.mkdtemp(prefix="germinate-")
        else:
            dirname = '.'

        for dist in dists:
            for component in components:
                g.parsePackages(
                    self.open_tag_files(
                        self.mirrors, dirname, "Packages", dist, component,
                        "binary-" + arch + "/Packages"),
                    "deb")

                g.parseSources(
                    self.open_tag_files(
                        self.source_mirrors, dirname, "Sources", dist, component,
                        "source/Sources"))

                instpackages = ""
                try:
                    instpackages = self.open_tag_files(
                        self.mirrors, dirname, "InstallerPackages", dist, component,
                        "debian-installer/binary-" + arch + "/Packages")
                except IOError:
                    # can live without these
                    print "Missing installer Packages file for", component, \
                          "(ignoring)"
                else:
                    g.parsePackages(instpackages, "udeb")

        if cleanup:
            shutil.rmtree(dirname)
