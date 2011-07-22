#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""Update list files from the Wiki."""

# Copyright (c) 2004, 2005, 2006, 2007, 2008 Canonical Ltd.
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

import gzip
import os
import shutil
import sys
import urllib2
import getopt
import logging
import codecs
import cStringIO

import apt_pkg

from Germinate import Germinator
import Germinate.Archive
import Germinate.seeds
import Germinate.version


__pychecker__ = 'maxlines=300'

# Where do we get up-to-date seeds from?
SEEDS = ["http://people.canonical.com/~ubuntu-archive/seeds/"]
SEEDS_BZR = ["http://bazaar.launchpad.net/~ubuntu-core-dev/ubuntu-seeds/"]
RELEASE = "ubuntu.natty"

# If we need to download Packages.gz and/or Sources.gz, where do we get
# them from?
MIRRORS = []
SOURCE_MIRRORS = []
DEFAULT_MIRROR = "http://archive.ubuntu.com/ubuntu/"
DEFAULT_SOURCE_MIRROR = None
DIST = ["natty"]
COMPONENTS = ["main", "restricted"]
ARCH = "i386"

CHECK_IPV6 = False

# If we need to download a new IPv6 dump, where do we get it from?
IPV6DB = "http://debdev.fabbione.net/stat/"


def open_ipv6_tag_file(filename):
    """Download the daily IPv6 db dump if needed, and open it."""
    if os.path.exists(filename):
        return open(filename, "r")

    print "Downloading", filename, "file ..."
    url = IPV6DB + filename + ".gz"
    url_f = urllib2.urlopen(url)
    url_data = cStringIO.StringIO(url_f.read())
    url_f.close()
    print "Decompressing", filename, "file ..."
    gzip_f = gzip.GzipFile(fileobj=url_data)
    f = open(filename, "w")
    for line in gzip_f:
        print >>f, line,
    f.close()
    gzip_f.close()
    url_data.close()

    return open(filename, "r")

def write_list(whyname, filename, g, pkgset):
    pkglist = list(pkgset)
    pkglist.sort()

    pkg_len = len("Package")
    src_len = len("Source")
    why_len = len("Why")
    mnt_len = len("Maintainer")

    for pkg in pkglist:
        _pkg_len = len(pkg)
        if _pkg_len > pkg_len: pkg_len = _pkg_len

        _src_len = len(g.packages[pkg]["Source"])
        if _src_len > src_len: src_len = _src_len

        _why_len = len(g.why[whyname][pkg][0])
        if _why_len > why_len: why_len = _why_len

        _mnt_len = len(g.packages[pkg]["Maintainer"])
        if _mnt_len > mnt_len: mnt_len = _mnt_len

    size = 0
    installed_size = 0

    pkglist.sort()
    f = codecs.open(filename, "w", "utf8", "replace")
    print >>f, "%-*s | %-*s | %-*s | %-*s | %-15s | %-15s" % \
          (pkg_len, "Package",
           src_len, "Source",
           why_len, "Why",
           mnt_len, "Maintainer",
           "Deb Size (B)",
           "Inst Size (KB)")
    print >>f, ("-" * pkg_len) + "-+-" + ("-" * src_len) + "-+-" \
          + ("-" * why_len) + "-+-" + ("-" * mnt_len) + "-+-" \
          + ("-" * 15) + "-+-" + ("-" * 15) + "-"
    for pkg in pkglist:
        size += g.packages[pkg]["Size"]
        installed_size += g.packages[pkg]["Installed-Size"]
        print >>f, "%-*s | %-*s | %-*s | %-*s | %15d | %15d" % \
              (pkg_len, pkg,
               src_len, g.packages[pkg]["Source"],
               why_len, g.why[whyname][pkg][0],
               mnt_len, g.packages[pkg]["Maintainer"],
               g.packages[pkg]["Size"],
               g.packages[pkg]["Installed-Size"])
    print >>f, ("-" * (pkg_len + src_len + why_len + mnt_len + 9)) + "-+-" \
          + ("-" * 15) + "-+-" + ("-" * 15) + "-"
    print >>f, "%*s | %15d | %15d" % \
          ((pkg_len + src_len + why_len + mnt_len + 9), "",
           size, installed_size)

    f.close()

def write_source_list(filename, g, srcset):
    global CHECK_IPV6

    srclist = list(srcset)
    srclist.sort()

    src_len = len("Source")
    mnt_len = len("Maintainer")
    ipv6_len = len("IPv6 status")

    for src in srclist:
        _src_len = len(src)
        if _src_len > src_len: src_len = _src_len

        _mnt_len = len(g.sources[src]["Maintainer"])
        if _mnt_len > mnt_len: mnt_len = _mnt_len

        if CHECK_IPV6:
            _ipv6_len = len(g.sources[src]["IPv6"])
            if _ipv6_len > ipv6_len: ipv6_len = _ipv6_len

    srclist.sort()
    f = codecs.open(filename, "w", "utf8", "replace")

    fmt = "%-*s | %-*s"
    header_args = [src_len, "Source", mnt_len, "Maintainer"]
    separator = ("-" * src_len) + "-+-" + ("-" * mnt_len) + "-"
    if CHECK_IPV6:
        fmt += " | %-*s"
        header_args.extend((ipv6_len, "IPv6 status"))
        separator += "+-" + ("-" * ipv6_len) + "-"

    print >>f, fmt % tuple(header_args)
    print >>f, separator
    for src in srclist:
        args = [src_len, src, mnt_len, g.sources[src]["Maintainer"]]
        if CHECK_IPV6:
            args.extend((ipv6_len, g.sources[src]["IPv6"]))
        print >>f, fmt % tuple(args)

    f.close()

def write_rdepend_list(filename, g, pkg):
    f = open(filename, "w")
    print >>f, pkg
    _write_rdepend_list(f, g, pkg, "", done=set())
    f.close()

def _write_rdepend_list(f, g, pkg, prefix, stack=None, done=None):
    if stack is None:
        stack = []
    else:
        stack = list(stack)
        if pkg in stack:
            print >>f, prefix + "! loop"
            return
    stack.append(pkg)

    if done is None:
        done = set()
    elif pkg in done:
        print >>f, prefix + "! skipped"
        return
    done.add(pkg)

    for seed in g.seeds:
        if pkg in g.seed[seed]:
            print >>f, prefix + "*", seed.title(), "seed"

    if "Reverse-Depends" not in g.packages[pkg]:
        return

    for field in ("Pre-Depends", "Depends", "Recommends",
                  "Build-Depends", "Build-Depends-Indep"):
        if field not in g.packages[pkg]["Reverse-Depends"]:
            continue

        i = 0
        print >>f, prefix + "*", "Reverse", field + ":"
        for dep in g.packages[pkg]["Reverse-Depends"][field]:
            i += 1
            print >>f, prefix + " +- " + dep
            if field.startswith("Build-"):
                continue

            if i == len(g.packages[pkg]["Reverse-Depends"][field]):
                extra = "    "
            else:
                extra = " |  "
            _write_rdepend_list(f, g, dep, prefix + extra, stack, done)

def write_prov_list(filename, provdict):
    provides = provdict.keys()
    provides.sort()

    f = open(filename, "w")
    for prov in provides:
        print >>f, prov

        provlist = list(provdict[prov])
        provlist.sort()
        for pkg in provlist:
            print >>f, "\t%s" % (pkg,)
        print >>f
    f.close()

def write_structure(filename, structure):
    f = open(filename, "w")
    for line in structure:
        print >>f, line
    f.close()

def write_seedtext(filename, seedtext):
    f = open(filename, "w")
    for line in seedtext:
        print >>f, line.rstrip('\n')

def write_dot(filename, seednames, seedinherit):
    """Write a dot file to represent the structure of the seeds"""

    #Initialize dot document
    dotfile = codecs.open(filename, "w", "utf8", "replace")
    print >>dotfile, "digraph structure {"
    print >>dotfile, "    node [color=lightblue2, style=filled];"

    for seed in seednames:
        for inherit in seedinherit[seed]:
            print >>dotfile, "    \"%s\" -> \"%s\";" % (inherit, seed)

    print >>dotfile, "}"
    dotfile.close()

def usage(f):
    print >>f, """Usage: germinate.py [options]

Options:

  -h, --help            Print this help message and exit.
  --version             Output version information and exit.
  -v, --verbose         Be more verbose when processing seeds.
  -S, --seed-source=SOURCE
                        Fetch seeds from SOURCE
                        (default: %s).
  -s, --seed-dist=DIST  Fetch seeds for distribution DIST (default: %s).
  -m, --mirror=MIRROR   Get package lists from MIRROR
                        (default: %s).
  --source-mirror=MIRROR
                        Get source package lists from mirror
                        (default: value of --mirror).
  -d, --dist=DIST       Operate on distribution DIST (default: %s).
  -a, --arch=ARCH       Operate on architecture ARCH (default: %s).
  -c, --components=COMPS
                        Operate on components COMPS (default: %s).
  -i, --ipv6            Check IPv6 status of source packages.
  --bzr                 Fetch seeds using bzr. Requires bzr to be installed.
  --cleanup             Don't cache Packages or Sources files.
  --no-rdepends         Disable reverse-dependency calculations.
  --seed-packages=PARENT/PKG,PARENT/PKG,...
                        Treat each PKG as a seed by itself, inheriting from
                        PARENT.
""" % (",".join(SEEDS), RELEASE, DEFAULT_MIRROR, ",".join(DIST), ARCH,
       ",".join(COMPONENTS))


def main():
    global SEEDS, SEEDS_BZR, RELEASE
    global DEFAULT_MIRROR, DEFAULT_SOURCE_MIRROR, SOURCE_MIRRORS, MIRRORS
    global DIST, ARCH, COMPONENTS, CHECK_IPV6
    verbose = False
    bzr = False
    cleanup = False
    want_rdepends = True
    seed_packages = ()
    seeds_set = False

    g = Germinator()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvS:s:m:d:c:a:i",
                                   ["help",
                                    "version",
                                    "verbose",
                                    "seed-source=",
                                    "seed-dist=",
                                    "mirror=",
                                    "source-mirror=",
                                    "dist=",
                                    "components=",
                                    "arch=",
                                    "ipv6",
                                    "bzr",
                                    "cleanup",
                                    "no-rdepends",
                                    "seed-packages="])
    except getopt.GetoptError:
        usage(sys.stderr)
        sys.exit(2)

    for option, value in opts:
        if option in ("-h", "--help"):
            usage(sys.stdout)
            sys.exit()
        elif option == "--version":
            print "%s %s" % (os.path.basename(sys.argv[0]),
                             Germinate.version.VERSION)
            sys.exit()
        elif option in ("-v", "--verbose"):
            verbose = True
        elif option in ("-S", "--seed-source"):
            SEEDS = value.split(",")
            seeds_set = True
        elif option in ("-s", "--seed-dist"):
            RELEASE = value
        elif option in ("-m", "--mirror"):
            if not value.endswith("/"):
                value += "/"
            MIRRORS.append(value)
        elif option == "--source-mirror":
            if not value.endswith("/"):
                value += "/"
            SOURCE_MIRRORS.append(value)
        elif option in ("-d", "--dist"):
            DIST = value.split(",")
        elif option in ("-c", "--components"):
            COMPONENTS = value.split(",")
        elif option in ("-a", "--arch"):
            ARCH = value
        elif option in ("-i", "--ipv6"):
            CHECK_IPV6 = True
        elif option == "--bzr":
            bzr = True
            if not seeds_set:
                SEEDS = SEEDS_BZR
        elif option == "--cleanup":
            cleanup = True
        elif option == "--no-rdepends":
            want_rdepends = False
        elif option == "--seed-packages":
            seed_packages = value.split(',')

    if not MIRRORS:
        MIRRORS.append(DEFAULT_MIRROR)

    logger = logging.getLogger()
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(Germinator.PROGRESS)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(levelname)s%(message)s'))
    logger.addHandler(handler)

    apt_pkg.init_config()
    apt_pkg.config.set("APT::Architecture", ARCH)
    apt_pkg.init_system()

    Germinate.Archive.TagFile(MIRRORS, SOURCE_MIRRORS).feed(
        g, DIST, COMPONENTS, ARCH, cleanup)

    if CHECK_IPV6:
        g.parseIPv6(open_ipv6_tag_file("dailydump"))

    if os.path.isfile("hints"):
        g.parseHints(open("hints"))

    try:
        blacklist = Germinate.seeds.open_seed(SEEDS, RELEASE, "blacklist", bzr)
    except Germinate.seeds.SeedError:
        blacklist = None
    if blacklist is not None:
        g.parseBlacklist(blacklist)

    try:
        seednames, seedinherit, seedbranches, _ = g.parseStructure(
            SEEDS, RELEASE, bzr)
    except Germinate.seeds.SeedError:
        sys.exit(1)

    write_dot("structure.dot", seednames, seedinherit)

    seednames, seedinherit, seedbranches = g.expandInheritance(
        seednames, seedinherit, seedbranches)

    seedtexts = {}
    for seedname in seednames:
        try:
            seed_fd = Germinate.seeds.open_seed(SEEDS, seedbranches, seedname,
                                                bzr)
        except Germinate.seeds.SeedError:
            sys.exit(1)
        seedtexts[seedname] = seed_fd.readlines()
        seed_fd.close()
        g.plantSeed(seedtexts[seedname],
                    ARCH, seedname, list(seedinherit[seedname]), RELEASE)
    for seed_package in seed_packages:
        (parent, pkg) = seed_package.split('/')
        g.plantSeed([" * " + pkg], ARCH, pkg,
                    seedinherit[parent] + [parent], RELEASE)
        seednames.append(pkg)
    g.prune()
    g.grow()
    g.addExtras(RELEASE)
    if want_rdepends:
        g.reverseDepends()

    seednames_extra = list(seednames)
    seednames_extra.append('extra')
    for seedname in seednames_extra:
        write_list(seedname, seedname,
                   g, set(g.seed[seedname]) | set(g.seedrecommends[seedname]) |
                      set(g.depends[seedname]))
        write_list(seedname, seedname + ".seed",
                   g, g.seed[seedname])
        write_list(seedname, seedname + ".seed-recommends",
                   g, g.seedrecommends[seedname])
        write_list(seedname, seedname + ".depends",
                   g, g.depends[seedname])
        write_list(seedname, seedname + ".build-depends",
                   g, g.build_depends[seedname])

        if seedname != "extra" and seedname in seedtexts:
            write_seedtext(seedname + ".seedtext", seedtexts[seedname])
            write_source_list(seedname + ".sources",
                              g, g.sourcepkgs[seedname])
        write_source_list(seedname + ".build-sources",
                          g, g.build_sourcepkgs[seedname])

    all_bins = set()
    sup_bins = set()
    all_srcs = set()
    sup_srcs = set()
    for seedname in seednames:
        all_bins.update(g.seed[seedname])
        all_bins.update(g.seedrecommends[seedname])
        all_bins.update(g.depends[seedname])
        all_bins.update(g.build_depends[seedname])
        all_srcs.update(g.sourcepkgs[seedname])
        all_srcs.update(g.build_sourcepkgs[seedname])

        if seedname == g.supported:
            sup_bins.update(g.seed[seedname])
            sup_bins.update(g.seedrecommends[seedname])
            sup_bins.update(g.depends[seedname])
            sup_srcs.update(g.sourcepkgs[seedname])

        # Only include those build-dependencies that aren't already in the
        # dependency outputs for inner seeds of supported. This allows
        # supported+build-depends to be usable as an "everything else"
        # output.
        build_depends = dict.fromkeys(g.build_depends[seedname], True)
        build_sourcepkgs = dict.fromkeys(g.build_sourcepkgs[seedname], True)
        for seed in g.innerSeeds(g.supported):
            build_depends.update(dict.fromkeys(g.seed[seed], False))
            build_depends.update(dict.fromkeys(g.seedrecommends[seed], False))
            build_depends.update(dict.fromkeys(g.depends[seed], False))
            build_sourcepkgs.update(dict.fromkeys(g.sourcepkgs[seed], False))
        sup_bins.update([k for (k, v) in build_depends.iteritems() if v])
        sup_srcs.update([k for (k, v) in build_sourcepkgs.iteritems() if v])

    write_list("all", "all", g, all_bins)
    write_source_list("all.sources", g, all_srcs)

    write_list("all", "%s+build-depends" % g.supported, g, sup_bins)
    write_source_list("%s+build-depends.sources" % g.supported, g, sup_srcs)

    write_list("all", "all+extra", g, g.all)
    write_source_list("all+extra.sources", g, g.all_srcs)

    write_prov_list("provides", g.pkgprovides)

    write_structure("structure", g.structure)

    if os.path.exists("rdepends"):
        shutil.rmtree("rdepends")
    if want_rdepends:
        os.mkdir("rdepends")
        os.mkdir(os.path.join("rdepends", "ALL"))
        for pkg in g.all:
            dirname = os.path.join("rdepends", g.packages[pkg]["Source"])
            if not os.path.exists(dirname):
                os.mkdir(dirname)

            write_rdepend_list(os.path.join(dirname, pkg), g, pkg)
            os.symlink(os.path.join("..", g.packages[pkg]["Source"], pkg),
                       os.path.join("rdepends", "ALL", pkg))

    g.writeBlacklisted("blacklisted")

if __name__ == "__main__":
    main()
