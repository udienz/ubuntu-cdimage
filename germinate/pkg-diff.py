#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Copyright (c) 2004, 2005, 2006, 2007, 2008 Canonical Ltd.
#
# This file is part of Germinate.
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
import sys
import getopt
import logging

import apt_pkg

from Germinate import Germinator
import Germinate.Archive
import Germinate.seeds
import Germinate.version

# TODO: cloned from germinate.py; should be common
SEEDS = ["http://ironhide.udienz.web.id/canonical-seed/"]
RELEASE = "ubuntu.oneiric"
MIRRORS = ["http://kambing.ui.ac.id/ubuntu/"]
DIST = ["oneiric"]
COMPONENTS = ["main"]
ARCH = "i386"

class Package:
    def __init__(self, name):
        self.name = name
        self.seed = {}
        self.installed = 0

    def setSeed(self, seed):
        self.seed[seed] = 1

    def setInstalled(self):
        self.installed = 1

    def output(self, outmode):
        ret = self.name.ljust(30) + "\t"
        if outmode == "i":
            if self.installed and not len(self.seed):
                ret += "deinstall"
            elif not self.installed and len(self.seed):
                ret += "install"
            else:
                return ""
        elif outmode == "r":
            if self.installed and not len(self.seed):
                ret += "install"
            elif not self.installed and len(self.seed):
                ret += "deinstall"
            else:
                return ""
        else:           # default case
            if self.installed and not len(self.seed):
                ret = "- " + ret
            elif not self.installed and len(self.seed):
                ret = "+ " + ret
            else:
                ret = "  " + ret
            k = self.seed.keys()
            k.sort()
            ret += ",".join(k)
        return ret


class Globals:
    def __init__(self):
        self.package = {}
        self.seeds = []
        self.outputs = {}
        self.outmode = ""

    def setSeeds(self, seeds):
        self.seeds = seeds

        # Suppress most log information
        logging.getLogger().setLevel(logging.CRITICAL)

        global RELEASE, MIRRORS, DIST, COMPONENTS, ARCH
        print "Germinating"
        g = Germinator()
        apt_pkg.init_config()
        apt_pkg.config.set("APT::Architecture", ARCH)
        apt_pkg.init_system()

        Germinate.Archive.TagFile(MIRRORS).feed(
            g, DIST, COMPONENTS, ARCH, True)

        try:
            seednames, seedinherit, seedbranches, _ = g.parseStructure(SEEDS,
                                                                       RELEASE)
        except Germinate.seeds.SeedError:
            sys.exit(1)
        seednames, seedinherit, seedbranches = g.expandInheritance(
            seednames, seedinherit, seedbranches)
        needed_seeds = []
        build_tree = False
        for seedname in self.seeds:
            if seedname == ('%s+build-depends' % g.supported):
                seedname = g.supported
                build_tree = True
            for inherit in seedinherit[seedname]:
                if inherit not in needed_seeds:
                    needed_seeds.append(inherit)
            if seedname not in needed_seeds:
                needed_seeds.append(seedname)
        for seedname in needed_seeds:
            try:
                seed_fd = Germinate.seeds.open_seed(SEEDS, seedbranches,
                                                    seedname)
            except Germinate.seeds.SeedError:
                sys.exit(1)
            g.plantSeed(seed_fd,
                        ARCH, seedname, list(seedinherit[seedname]), RELEASE)
            seed_fd.close()
        g.prune()
        g.grow()

        for seedname in needed_seeds:
            for pkg in g.seed[seedname]:
                self.package.setdefault(pkg, Package(pkg))
                self.package[pkg].setSeed(seedname + ".seed")
            for pkg in g.seedrecommends[seedname]:
                self.package.setdefault(pkg, Package(pkg))
                self.package[pkg].setSeed(seedname + ".seed-recommends")
            for pkg in g.depends[seedname]:
                self.package.setdefault(pkg, Package(pkg))
                self.package[pkg].setSeed(seedname + ".depends")

            if build_tree:
                build_depends = dict.fromkeys(g.build_depends[seedname], True)
                for inner in g.innerSeeds(g.supported):
                    build_depends.update(dict.fromkeys(g.seed[inner], False))
                    build_depends.update(dict.fromkeys(g.seedrecommends[inner],
                                                       False))
                    build_depends.update(dict.fromkeys(g.depends[inner],
                                                       False))
                for (pkg, use) in build_depends.iteritems():
                    if use:
                        self.package.setdefault(pkg, Package(pkg))
                        self.package[pkg].setSeed(g.supported + ".build-depends")

    def parseDpkg(self, fname):
        if fname == None:
            f = os.popen("dpkg --get-selections")
        else:
            f = open(fname)
        lines = f.readlines()
        f.close()
        for l in lines:
            pkg, st = l.split(None)
            self.package.setdefault(pkg, Package(pkg))
            if st == "install" or st == "hold":
                self.package[pkg].setInstalled()

    def setOutput(self, mode):
        self.outmode = mode

    def output(self):
        keys = self.package.keys()
        keys.sort()
        for k in keys:
            l = self.package[k].output(self.outmode)
            if len(l):
                print l

def usage(f):
    print >>f, """Usage: pkg-diff.py [options] [seeds]

Options:

  -h, --help            Print this help message and exit.
  --version             Output version information and exit.
  -l, --list=FILE       Read list of packages from this file
                        (default: read from dpkg --get-selections).
  -m, --mode=[i|r|d]    Show packages to install/remove/diff (default: d).
  -S, --seed-source=SOURCE
                        Fetch seeds from SOURCE
                        (default: %s).
  -s, --seed-dist=DIST  Fetch seeds for distribution DIST (default: %s).
  -d, --dist=DIST       Operate on distribution DIST (default: %s).
  -a, --arch=ARCH       Operate on architecture ARCH (default: %s).

A list of seeds against which to compare may be supplied as non-option
arguments. Seeds from which they inherit will be added automatically. The
default is 'desktop'.
""" % (",".join(SEEDS), RELEASE, ",".join(DIST), ARCH)

def main():
    global SEEDS, RELEASE, DIST, ARCH
    g = Globals()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hl:m:S:s:d:a:",
                                   ["help",
                                    "version",
                                    "list=",
                                    "mode=",
                                    "seed-source=",
                                    "seed-dist=",
                                    "dist=",
                                    "arch="])
    except getopt.GetoptError:
        usage(sys.stderr)
        sys.exit(2)

    dpkgFile = None
    for option, value in opts:
        if option in ("-h", "--help"):
            usage(sys.stdout)
            sys.exit()
        elif option == "--version":
            print "%s %s" % (os.path.basename(sys.argv[0]),
                             Germinate.version.VERSION)
            sys.exit()
        elif option in ("-l", "--list"):
            dpkgFile = value
        elif option in ("-m", "--mode"):
            # one of 'i' (install), 'r' (remove), or 'd' (default)
            g.setOutput(value)
        elif option in ("-S", "--seed-source"):
            SEEDS = value.split(",")
        elif option in ("-s", "--seed-dist"):
            RELEASE = value
        elif option in ("-d", "--dist"):
            DIST = value.split(",")
        elif option in ("-a", "--arch"):
            ARCH = value

    g.parseDpkg(dpkgFile)
    if not len(args):
        args = ["desktop"]
    g.setSeeds(args)
    g.output()

if __name__ == "__main__":
    main()
