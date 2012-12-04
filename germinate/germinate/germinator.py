# -*- coding: UTF-8 -*-
"""Expand seeds into dependency-closed lists of packages."""

# Copyright (c) 2004, 2005, 2006, 2007, 2008, 2009, 2011 Canonical Ltd.
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

import sys
import re
import fnmatch
import logging
import codecs

import apt_pkg

from germinate.archive import IndexType
from germinate.seeds import Seed

# TODO: would be much more elegant to reduce our recursion depth!
sys.setrecursionlimit(2000)

class Germinator:
    PROGRESS = 15

    def __init__(self, arch):
        self.arch = arch
        apt_pkg.config.set("APT::Architecture", self.arch)

        self.packages = {}
        self.packagetype = {}
        self.provides = {}
        self.sources = {}
        self.pruned = {}

        self.structure = None
        self.seeds = []
        self.seed = {}
        self.seedfeatures = {}
        self.seedrecommends = {}
        self.close_seeds = {}
        self.substvars = {}
        self.depends = {}
        self.build_depends = {}
        self.supported = None

        self.sourcepkgs = {}
        self.build_sourcepkgs = {}

        self.pkgprovides = {}

        self.all = set()
        self.build = {}
        self.not_build = {}

        self.all_srcs = set()
        self.build_srcs = {}
        self.not_build_srcs = {}

        self.why = {}
        self.why["all"] = {}

        self.hints = {}

        self.blacklist = {}
        self.blacklisted = set()
        self.seedblacklist = {}

        self.di_kernel_versions = {}
        self.includes = {}
        self.excludes = {}

    def parseHints(self, f):
        """Parse a hints file."""
        for line in f:
            if line.startswith("#") or not len(line.rstrip()): continue

            words = line.rstrip().split(None)
            if len(words) != 2:
                continue

            self.hints[words[1]] = words[0]
        f.close()

    def _parsePackage(self, section, pkgtype):
        """Parse a section from a Packages file."""
        pkg = section["Package"]
        ver = section["Version"]

        # If we have already seen an equal or newer version of this package,
        # then skip this section.
        if pkg in self.packages:
            last_ver = self.packages[pkg]["Version"]
            if apt_pkg.version_compare(last_ver, ver) >= 0:
                return

        self.packages[pkg] = {}
        self.packagetype[pkg] = pkgtype
        self.pruned[pkg] = set()

        self.packages[pkg]["Section"] = \
            section.get("Section", "").split('/')[-1]

        self.packages[pkg]["Version"] = ver

        self.packages[pkg]["Maintainer"] = \
            unicode(section.get("Maintainer", ""), "utf8", "replace")

        self.packages[pkg]["Essential"] = section.get("Essential", "")

        for field in "Pre-Depends", "Depends", "Recommends", "Suggests":
            value = section.get(field, "")
            self.packages[pkg][field] = apt_pkg.parse_depends(value)

        for field in "Size", "Installed-Size":
            value = section.get(field, "0")
            self.packages[pkg][field] = int(value)

        src = section.get("Source", pkg)
        idx = src.find("(")
        if idx != -1:
            src = src[:idx].strip()
        self.packages[pkg]["Source"] = src

        provides = apt_pkg.parse_depends(section.get("Provides", ""))
        for prov in provides:
            if prov[0][0] not in self.provides:
                self.provides[prov[0][0]] = []
                if prov[0][0] in self.packages:
                    self.provides[prov[0][0]].append(prov[0][0])
            self.provides[prov[0][0]].append(pkg)
        self.packages[pkg]["Provides"] = provides

        if pkg in self.provides:
            self.provides[pkg].append(pkg)

        self.packages[pkg]["Kernel-Version"] = section.get("Kernel-Version", "")

    def _parseSource(self, section):
        """Parse a section from a Sources file."""
        src = section["Package"]
        ver = section["Version"]

        # If we have already seen an equal or newer version of this source,
        # then skip this section.
        if src in self.sources:
            last_ver = self.sources[src]["Version"]
            if apt_pkg.version_compare(last_ver, ver) >= 0:
                return

        self.sources[src] = {}

        self.sources[src]["Maintainer"] = \
            unicode(section.get("Maintainer", ""), "utf8", "replace")
        self.sources[src]["Version"] = ver

        for field in "Build-Depends", "Build-Depends-Indep":
            value = section.get(field, "")
            self.sources[src][field] = apt_pkg.parse_src_depends(value)

        binaries = apt_pkg.parse_depends(section.get("Binary", src))
        self.sources[src]["Binaries"] = [ b[0][0] for b in binaries ]

    def parseArchive(self, archive):
        for indextype, section in archive.sections():
            if indextype == IndexType.PACKAGES:
                self._parsePackage(section, "deb")
            elif indextype == IndexType.SOURCES:
                self._parseSource(section)
            elif indextype == IndexType.INSTALLER_PACKAGES:
                self._parsePackage(section, "udeb")
            else:
                raise ValueError("Unknown index type %d" % indextype)

    def parseBlacklist(self, f):
        """Parse a blacklist file, used to indicate unwanted packages"""

        name = ''

        for line in f:
            line = line.strip()
            if line.startswith('# blacklist: '):
                name = line[13:]
            elif not line or line.startswith('#'):
                continue
            else:
                self.blacklist[line] = name
        f.close()

    def writeBlacklisted(self, filename):
        """Write out the list of blacklisted packages we encountered"""

        with open(filename, 'w') as fh:
            sorted_blacklisted = list(self.blacklisted)
            sorted_blacklisted.sort()
            for pkg in sorted_blacklisted:
                blacklist = self.blacklist[pkg]
                fh.write('%s\t%s\n' % (pkg, blacklist))

    def _newSeed(self, seedname):
        self.seeds.append(seedname)
        self.seed[seedname] = []
        self.seedfeatures[seedname] = set()
        self.seedrecommends[seedname] = []
        self.close_seeds[seedname] = set()
        self.depends[seedname] = set()
        self.build_depends[seedname] = set()
        self.sourcepkgs[seedname] = set()
        self.build_sourcepkgs[seedname] = set()
        self.build[seedname] = set()
        self.not_build[seedname] = set()
        self.build_srcs[seedname] = set()
        self.not_build_srcs[seedname] = set()
        self.why[seedname] = {}
        self.seedblacklist[seedname] = set()
        self.di_kernel_versions[seedname] = set()
        self.includes[seedname] = {}
        self.excludes[seedname] = {}

    def _filterPackages(self, packages, pattern):
        """Filter a list of packages, returning those that match the given
        pattern. The pattern may either be a shell-style glob, or (if
        surrounded by slashes) an extended regular expression."""

        if pattern.startswith('/') and pattern.endswith('/'):
            patternre = re.compile(pattern[1:-1])
            filtered = [p for p in packages if patternre.search(p) is not None]
        elif '*' in pattern or '?' in pattern or '[' in pattern:
            filtered = fnmatch.filter(packages, pattern)
        else:
            # optimisation for common case
            if pattern in packages:
                filtered = [pattern]
            else:
                filtered = []
        filtered.sort()
        return filtered

    def _substituteSeedVars(self, pkg):
        """Process substitution variables. These look like ${name} (e.g.
        "kernel-image-${Kernel-Version}"). The name is case-insensitive.
        Substitution variables are set with a line that looks like
        " * name: value [value ...]", values being whitespace-separated.
        
        A package containing substitution variables will be expanded into
        one package for each possible combination of values of those
        variables."""

        pieces = re.split(r'(\${.*?})', pkg)
        substituted = [[]]

        for piece in pieces:
            if piece.startswith("${") and piece.endswith("}"):
                name = piece[2:-1].lower()
                if name in self.substvars:
                    # Duplicate substituted once for each available substvar
                    # expansion.
                    newsubst = []
                    for value in self.substvars[name]:
                        for substpieces in substituted:
                            newsubstpieces = list(substpieces)
                            newsubstpieces.append(value)
                            newsubst.append(newsubstpieces)
                    substituted = newsubst
                else:
                    logging.error("Undefined seed substvar: %s", name)
            else:
                for substpieces in substituted:
                    substpieces.append(piece)

        substpkgs = []
        for substpieces in substituted:
            substpkgs.append("".join(substpieces))
        return substpkgs

    def _alreadySeeded(self, seedname, pkg):
        """Has pkg already been seeded in this seed or in one from
        which we inherit?"""

        for seed in self.structure.innerSeeds(seedname):
            if (pkg in self.seed[seed] or
                pkg in self.seedrecommends[seed]):
                return True

        return False

    def _plantSeed(self, seedname):
        """Add a seed."""
        if seedname in self.seeds:
            return

        self._newSeed(seedname)
        seedpkgs = []
        seedrecommends = []

        for line in self.structure.texts[seedname]:
            if line.lower().startswith('task-seeds:'):
                self.close_seeds[seedname].update(line[11:].strip().split())
                continue

            if not line.startswith(" * "):
                continue

            pkg = line[3:].strip()
            if pkg.find("#") != -1:
                pkg = pkg[:pkg.find("#")]

            colon = pkg.find(":")
            if colon != -1:
                # Special header
                name = pkg[:colon]
                name = name.lower()
                value = pkg[colon + 1:]
                values = value.strip().split()
                if name == "kernel-version":
                    # Allows us to pick the right modules later
                    logging.warning("Allowing d-i kernel versions: %s", values)
                    self.di_kernel_versions[seedname].update(values)
                elif name == "feature":
                    logging.warning("Setting features {%s} for seed %s",
                                    ', '.join(values), seedname)
                    self.seedfeatures[seedname].update(values)
                elif name.endswith("-include"):
                    included_seed = name[:-8]
                    if (included_seed not in self.seeds and
                        included_seed != "extra"):
                        logging.error("Cannot include packages from unknown "
                                      "seed: %s", included_seed)
                    else:
                        logging.warning("Including packages from %s: %s",
                                        included_seed, values)
                        if included_seed not in self.includes[seedname]:
                            self.includes[seedname][included_seed] = []
                        self.includes[seedname][included_seed].extend(values)
                elif name.endswith("-exclude"):
                    excluded_seed = name[:-8]
                    if (excluded_seed not in self.seeds and
                        excluded_seed != "extra"):
                        logging.error("Cannot exclude packages from unknown "
                                      "seed: %s", excluded_seed)
                    else:
                        logging.warning("Excluding packages from %s: %s",
                                        excluded_seed, values)
                        if excluded_seed not in self.excludes[seedname]:
                            self.excludes[seedname][excluded_seed] = []
                        self.excludes[seedname][excluded_seed].extend(values)
                self.substvars[name] = values
                continue

            pkg = pkg.strip()
            if pkg.endswith("]"):
                archspec = []
                startarchspec = pkg.rfind("[")
                if startarchspec != -1:
                    archspec = pkg[startarchspec + 1:-1].split()
                    pkg = pkg[:startarchspec - 1]
                    posarch = [x for x in archspec if not x.startswith('!')]
                    negarch = [x[1:] for x in archspec if x.startswith('!')]
                    if self.arch in negarch:
                        continue
                    if posarch and self.arch not in posarch:
                        continue

            pkg = pkg.split()[0]

            # a leading ! indicates a per-seed blacklist; never include this
            # package in the given seed or any of its inner seeds, no matter
            # what
            if pkg.startswith('!'):
                pkg = pkg[1:]
                is_blacklist = True
            else:
                is_blacklist = False

            # a (pkgname) indicates that this is a recommend
            # and not a depends
            if pkg.startswith('(') and pkg.endswith(')'):
                pkg = pkg[1:-1]
                pkgs =  self._filterPackages(self.packages, pkg)
                if not pkgs:
                    pkgs = [pkg] # virtual or expanded; check again later
                for pkg in pkgs:
                    seedrecommends.extend(self._substituteSeedVars(pkg))

            if pkg.startswith('%'):
                pkg = pkg[1:]
                if pkg in self.sources:
                    pkgs = [p for p in self.sources[pkg]["Binaries"]
                              if p in self.packages]
                else:
                    logging.warning("Unknown source package: %s", pkg)
                    pkgs = []
            else:
                pkgs = self._filterPackages(self.packages, pkg)
                if not pkgs:
                    pkgs = [pkg] # virtual or expanded; check again later

            if is_blacklist:
                for pkg in pkgs:
                    logging.info("Blacklisting %s from %s", pkg, seedname)
                    self.seedblacklist[seedname].update(
                        self._substituteSeedVars(pkg))
            else:
                for pkg in pkgs:
                    seedpkgs.extend(self._substituteSeedVars(pkg))

        for pkg in seedpkgs:
            if pkg in self.hints and self.hints[pkg] != seedname:
                logging.warning("Taking the hint: %s", pkg)
                continue

            if pkg in self.packages:
                # Ordinary package
                if self._alreadySeeded(seedname, pkg):
                    logging.warning("Duplicated seed: %s", pkg)
                elif self._isPruned(pkg, seedname):
                    logging.warning("Pruned %s from %s", pkg, seedname)
                else:
                    if pkg in seedrecommends:
                        self.seedrecommends[seedname].append(pkg)
                    else:
                        self.seed[seedname].append(pkg)
            elif pkg in self.provides:
                # Virtual package, include everything
                msg = "Virtual %s package: %s" % (seedname, pkg)
                for vpkg in self.provides[pkg]:
                    if self._alreadySeeded(seedname, vpkg):
                        pass
                    elif seedname in self.pruned[vpkg]:
                        pass
                    else:
                        msg += "\n  - %s" % vpkg
                        if pkg in seedrecommends:
                            self.seedrecommends[seedname].append(vpkg)
                        else:
                            self.seed[seedname].append(vpkg)
                logging.info("%s", msg)

            else:
                # No idea
                logging.error("Unknown %s package: %s", seedname, pkg)

        for pkg in self.hints:
            if (self.hints[pkg] == seedname and
                not self._alreadySeeded(seedname, pkg)):
                if pkg in self.packages:
                    if pkg in seedrecommends:
                        self.seedrecommends[seedname].append(pkg)
                    else:
                        self.seed[seedname].append(pkg)
                else:
                    logging.error("Unknown hinted package: %s", pkg)

    def plantSeeds(self, structure, seeds=None):
        """Add all seeds found in a seed structure."""
        if seeds is not None:
            structure.limit(seeds)

        self.structure = structure
        self.supported = structure.original_names[-1]
        for name in structure.names:
            structure.fetch(name)
            self._plantSeed(name)

    def _isPruned(self, pkg, seed):
        if not self.di_kernel_versions[seed]:
            return False
        kernver = self.packages[pkg]["Kernel-Version"]
        if kernver != "" and kernver not in self.di_kernel_versions[seed]:
            return True
        return False

    def prune(self):
        """Remove packages that are inapplicable for some reason, such as
           being for the wrong d-i kernel version."""
        for pkg in self.packages:
            for seed in self.seeds:
                if self._isPruned(pkg, seed):
                    self.pruned[pkg].add(seed)

    def _weedBlacklist(self, pkgs, seedname, build_tree, why):
        """Weed out blacklisted seed entries from a list."""
        white = []
        if build_tree:
            outerseeds = [self.supported]
        else:
            outerseeds = self.structure.outerSeeds(seedname)
        for pkg in pkgs:
            for outerseed in outerseeds:
                if (outerseed in self.seedblacklist and
                    pkg in self.seedblacklist[outerseed]):
                    logging.error("Package %s blacklisted in %s but seeded in "
                                  "%s (%s)", pkg, outerseed, seedname, why)
                    break
            else:
                white.append(pkg)
        return white

    def grow(self):
        """Grow the seeds."""
        for seedname in self.seeds:
            logging.log(self.PROGRESS,
                        "Resolving %s dependencies ...", seedname)
            if self.structure.branch is None:
                why = "%s seed" % seedname.title()
            else:
                why = ("%s %s seed" %
                       (self.structure.branch.title(), seedname))

            # Check for blacklisted seed entries.
            self.seed[seedname] = self._weedBlacklist(
                self.seed[seedname], seedname, False, why)
            self.seedrecommends[seedname] = self._weedBlacklist(
                self.seedrecommends[seedname], seedname, False, why)

            # Note that seedrecommends are not processed with
            # recommends=True; that is reserved for Recommends of packages,
            # not packages recommended by the seed. Changing this results in
            # less helpful output when a package is recommended by an inner
            # seed and required by an outer seed.
            for pkg in self.seed[seedname] + self.seedrecommends[seedname]:
                self._addPackage(seedname, pkg, why)

            for rescue_seedname in self.seeds:
                self._rescueIncludes(seedname, rescue_seedname,
                                     build_tree=False)
                if rescue_seedname == seedname:
                    # only rescue from seeds up to and including the current
                    # seed; later ones have not been grown
                    break
            self._rescueIncludes(seedname, "extra", build_tree=False)

        self._rescueIncludes(self.supported, "extra", build_tree=True)

    def addExtras(self):
        """Add packages generated by the sources but not in any seed."""
        self.structure.addExtra()
        self._newSeed("extra")

        logging.log(self.PROGRESS, "Identifying extras ...")
        found = True
        while found:
            found = False
            sorted_srcs = list(self.all_srcs)
            sorted_srcs.sort()
            for srcname in sorted_srcs:
                for pkg in self.sources[srcname]["Binaries"]:
                    if pkg not in self.packages:
                        continue
                    if self.packages[pkg]["Source"] != srcname:
                        continue
                    if pkg in self.all:
                        continue

                    if pkg in self.hints and self.hints[pkg] != "extra":
                        logging.warning("Taking the hint: %s", pkg)
                        continue

                    self.seed["extra"].append(pkg)
                    self._addPackage("extra", pkg, "Generated by " + srcname,
                                     second_class=True)
                    found = True

    def _allowedDependency(self, pkg, depend, seedname, build_depend):
        """Is pkg allowed to satisfy a (build-)dependency using depend
           within seedname? Note that depend must be a real package.
           
           If seedname is None, check whether the (build-)dependency is
           allowed within any seed."""
        if depend not in self.packages:
            logging.warning("_allowedDependency called with virtual package "
                            "%s", depend)
            return False
        if seedname is not None and seedname in self.pruned[depend]:
            return False
        if build_depend:
            if self.packagetype[depend] == "deb":
                return True
            else:
                return False
        else:
            if self.packagetype[pkg] == self.packagetype[depend]:
                return True
            else:
                return False

    def _allowedVirtualDependency(self, pkg, deptype):
        """May pkg's dependency relationship type deptype be satisfied by a
           virtual package? (Versioned dependencies may not be satisfied by
           virtual packages, unless pkg is a udeb.)"""
        if pkg in self.packagetype and self.packagetype[pkg] == "udeb":
            return True
        elif deptype == "":
            return True
        else:
            return False

    def _checkVersionedDependency(self, depname, depver, deptype):
        """Can this versioned dependency be satisfied with the current set
           of packages?"""
        if depname not in self.packages:
            return False
        if deptype == "":
            return True

        ver = self.packages[depname]["Version"]
        compare = apt_pkg.version_compare(ver, depver)
        if deptype == "<=":
            return compare <= 0
        elif deptype == ">=":
            return compare >= 0
        elif deptype == "<":
            return compare < 0
        elif deptype == ">":
            return compare > 0
        elif deptype == "=":
            return compare == 0
        elif deptype == "!=":
            return compare != 0
        else:
            logging.error("Unknown dependency comparator: %s" % deptype)
            return False

    def _unparseDependency(self, depname, depver, deptype):
        """Return a string representation of a dependency."""
        if deptype == "":
            return depname
        else:
            return "%s (%s %s)" % (depname, deptype, depver)

    def _followRecommends(self, seed=None):
        """Should we follow Recommends for this seed?"""
        if seed is not None and seed in self.seedfeatures:
            if "follow-recommends" in self.seedfeatures[seed]:
                return True
            if "no-follow-recommends" in self.seedfeatures[seed]:
                return False
        if "follow-recommends" in self.structure.features:
            return True
        return False

    def _addReverse(self, pkg, field, rdep):
        """Add a reverse dependency entry."""
        if "Reverse-Depends" not in self.packages[pkg]:
            self.packages[pkg]["Reverse-Depends"] = {}
        if field not in self.packages[pkg]["Reverse-Depends"]:
            self.packages[pkg]["Reverse-Depends"][field] = []

        self.packages[pkg]["Reverse-Depends"][field].append(rdep)

    def reverseDepends(self):
        """Calculate the reverse dependency relationships."""
        for pkg in self.all:
            fields = ["Pre-Depends", "Depends"]
            if (self._followRecommends() or
                self.packages[pkg]["Section"] == "metapackages"):
                fields.append("Recommends")
            for field in fields:
                for deplist in self.packages[pkg][field]:
                    for dep in deplist:
                        if dep[0] in self.all and \
                           self._allowedDependency(pkg, dep[0], None, False):
                            self._addReverse(dep[0], field, pkg)

        for src in self.all_srcs:
            for field in "Build-Depends", "Build-Depends-Indep":
                for deplist in self.sources[src][field]:
                    for dep in deplist:
                        if dep[0] in self.all and \
                           self._allowedDependency(src, dep[0], None, True):
                            self._addReverse(dep[0], field, src)

        for pkg in self.all:
            if "Reverse-Depends" not in self.packages[pkg]:
                continue

            fields = ["Pre-Depends", "Depends"]
            if (self._followRecommends() or
                self.packages[pkg]["Section"] == "metapackages"):
                fields.append("Recommends")
            fields.extend(["Build-Depends", "Build-Depends-Indep"])
            for field in fields:
                if field not in self.packages[pkg]["Reverse-Depends"]:
                    continue

                self.packages[pkg]["Reverse-Depends"][field].sort()

    def _alreadySatisfied(self, seedname, pkg, depend, build_depend=False, with_build=False):
        """Work out whether a dependency has already been satisfied."""
        (depname, depver, deptype) = depend
        if self._allowedVirtualDependency(pkg, deptype) and depname in self.provides:
            trylist = [ d for d in self.provides[depname]
                        if d in self.packages and self._allowedDependency(pkg, d, seedname, build_depend) ]
        elif (self._checkVersionedDependency(depname, depver, deptype) and
              self._allowedDependency(pkg, depname, seedname, build_depend)):
            trylist = [ depname ]
        else:
            return False

        for trydep in trylist:
            if with_build:
                for seed in self.structure.innerSeeds(seedname):
                    if trydep in self.build[seed]:
                        return True
            else:
                for seed in self.structure.innerSeeds(seedname):
                    if trydep in self.not_build[seed]:
                        return True
            if (trydep in self.seed[seedname] or
                trydep in self.seedrecommends[seedname]):
                return True
        else:
            return False

    def _addDependency(self, seedname, pkg, dependlist, build_depend,
                       second_class, build_tree, recommends):
        """Add a single dependency. Returns True if a dependency was added,
           otherwise False."""
        if build_tree and build_depend:
            why = self.packages[pkg]["Source"] + " (Build-Depend)"
        elif recommends:
            why = pkg + " (Recommends)"
        else:
            why = pkg

        dependlist = self._weedBlacklist(dependlist, seedname, build_tree, why)
        if not dependlist:
            return False

        if build_tree:
            for dep in dependlist:
                self.build_depends[seedname].add(dep)
        else:
            for dep in dependlist:
                self.depends[seedname].add(dep)

        for dep in dependlist:
            self._addPackage(seedname, dep, why,
                             build_tree, second_class, recommends)

        return True

    def _promoteDependency(self, seedname, pkg, depend, close, build_depend,
                           second_class, build_tree, recommends):
        """Try to satisfy a dependency by promoting an item from a lesser
           seed. If close is True, only "close-by" seeds (ones that generate
           the same task, as defined by Task-Seeds headers) are considered.
           Returns True if a dependency was added, otherwise False."""
        (depname, depver, deptype) = depend
        if (self._checkVersionedDependency(depname, depver, deptype) and
            self._allowedDependency(pkg, depname, seedname, build_depend)):
            trylist = [ depname ]
        elif (self._allowedVirtualDependency(pkg, deptype) and
              depname in self.provides):
            trylist = [ d for d in self.provides[depname]
                        if d in self.packages and
                           self._allowedDependency(pkg, d, seedname,
                                                   build_depend) ]
        else:
            return False

        for trydep in trylist:
            lesserseeds = self.structure.strictlyOuterSeeds(seedname)
            if close:
                lesserseeds = [l for l in lesserseeds
                                 if seedname in self.close_seeds[l]]
            for lesserseed in lesserseeds:
                if (trydep in self.seed[lesserseed] or
                    trydep in self.seedrecommends[lesserseed]):
                    if second_class:
                        # "I'll get you next time, Gadget!"
                        # When processing the build tree, we don't promote
                        # packages from lesser seeds, since we still want to
                        # consider them (e.g.) part of ship even if they're
                        # build-dependencies of desktop. However, we do need
                        # to process them now anyway, since otherwise we
                        # might end up selecting the wrong alternative from
                        # an or-ed build-dependency.
                        pass
                    else:
                        if trydep in self.seed[lesserseed]:
                            self.seed[lesserseed].remove(trydep)
                        if trydep in self.seedrecommends[lesserseed]:
                            self.seedrecommends[lesserseed].remove(trydep)
                        logging.warning("Promoted %s from %s to %s to satisfy "
                                        "%s",
                                        trydep, lesserseed, seedname, pkg)

                    return self._addDependency(seedname, pkg, [trydep],
                                               build_depend, second_class,
                                               build_tree, recommends)

        return False

    def _newDependency(self, seedname, pkg, depend, build_depend,
                       second_class, build_tree, recommends):
        """Try to satisfy a dependency by adding a new package to the output
           set. Returns True if a dependency was added, otherwise False."""
        (depname, depver, deptype) = depend
        if (self._checkVersionedDependency(depname, depver, deptype) and
            self._allowedDependency(pkg, depname, seedname, build_depend)):
            virtual = None
        elif self._allowedVirtualDependency(pkg, deptype) and depname in self.provides:
            virtual = depname
        else:
            if build_depend:
                desc = "build-dependency"
            elif recommends:
                desc = "recommendation"
            else:
                desc = "dependency"
            logging.error("Unknown %s %s by %s", desc,
                          self._unparseDependency(depname, depver, deptype),
                          pkg)
            return False

        dependlist = [depname]
        if virtual is not None:
            reallist = [ d for d in self.provides[virtual]
                         if d in self.packages and self._allowedDependency(pkg, d, seedname, build_depend) ]
            if len(reallist):
                depname = reallist[0]
                # If this one was a d-i kernel module, pick all the modules
                # for other allowed kernel versions too.
                if self.packages[depname]["Kernel-Version"] != "":
                    dependlist = [ d for d in reallist
                                   if not self.di_kernel_versions[seedname] or
                                      self.packages[d]["Kernel-Version"] in self.di_kernel_versions[seedname] ]
                else:
                    dependlist = [depname]
                logging.info("Chose %s out of %s to satisfy %s",
                             ", ".join(dependlist), virtual, pkg)
            else:
                logging.error("Nothing to choose out of %s to satisfy %s",
                              virtual, pkg)
                return False

        return self._addDependency(seedname, pkg, dependlist, build_depend,
                                   second_class, build_tree, recommends)

    def _addDependencyTree(self, seedname, pkg, depends,
                           build_depend=False,
                           second_class=False,
                           build_tree=False,
                           recommends=False):
        """Add a package's dependency tree."""
        if build_depend: build_tree = True
        if build_tree: second_class = True
        for deplist in depends:
            for dep in deplist:
                # TODO cjwatson 2008-07-02: At the moment this check will
                # catch an existing Recommends and we'll never get as far as
                # calling _rememberWhy with a dependency, so self.why will
                # be a bit inaccurate. We may need another pass for
                # Recommends to fix this.
                if self._alreadySatisfied(seedname, pkg, dep, build_depend, second_class):
                    break
            else:
                firstdep = True
                for dep in deplist:
                    if firstdep:
                        # For the first (preferred) alternative, we may
                        # consider promoting it from any lesser seed.
                        close = False
                        firstdep = False
                    else:
                        # Other alternatives are less favoured, and will
                        # only be promoted from closely-allied seeds.
                        close = True
                    if self._promoteDependency(seedname, pkg, dep, close,
                                               build_depend, second_class,
                                               build_tree, recommends):
                        if len(deplist) > 1:
                            logging.info("Chose %s to satisfy %s", dep[0], pkg)
                        break
                else:
                    for dep in deplist:
                        if self._newDependency(seedname, pkg, dep, build_depend,
                                               second_class, build_tree,
                                               recommends):
                            if len(deplist) > 1:
                                logging.info("Chose %s to satisfy %s", dep[0],
                                             pkg)
                            break
                    else:
                        if len(deplist) > 1:
                            logging.error("Nothing to choose to satisfy %s",
                                          pkg)

    def _rememberWhy(self, seedname, pkg, why, build_tree=False,
                     recommends=False):
        """Remember why this package was added to the output for this seed."""
        if pkg in self.why[seedname]:
            (old_why, old_build_tree, old_recommends) = self.why[seedname][pkg]
            # Reasons from the dependency tree beat reasons from the
            # build-dependency tree; but pick the first of either type that
            # we see. Within either tree, dependencies beat recommendations.
            if not old_build_tree and build_tree:
                return
            if old_build_tree == build_tree:
                if not old_recommends or recommends:
                    return

        self.why[seedname][pkg] = (why, build_tree, recommends)

    def _addPackage(self, seedname, pkg, why,
                    second_class=False,
                    build_tree=False,
                    recommends=False):
        """Add a package and its dependency trees."""
        if seedname in self.pruned[pkg]:
            logging.warning("Pruned %s from %s", pkg, seedname)
            return
        if build_tree:
            outerseeds = [self.supported]
        else:
            outerseeds = self.structure.outerSeeds(seedname)
        for outerseed in outerseeds:
            if (outerseed in self.seedblacklist and
                pkg in self.seedblacklist[outerseed]):
                logging.error("Package %s blacklisted in %s but seeded in %s "
                              "(%s)", pkg, outerseed, seedname, why)
                return
        if build_tree: second_class=True

        if pkg not in self.all:
            self.all.add(pkg)
        elif not build_tree:
            for buildseed in self.structure.innerSeeds(seedname):
                self.build_depends[buildseed].discard(pkg)

        for seed in self.structure.innerSeeds(seedname):
            if pkg in self.build[seed]:
                break
        else:
            self.build[seedname].add(pkg)

        if not build_tree:
            for seed in self.structure.innerSeeds(seedname):
                if pkg in self.not_build[seed]:
                    break
            else:
                self.not_build[seedname].add(pkg)

        # Remember why the package was added to the output for this seed.
        # Also remember a reason for "all" too, so that an aggregated list
        # of all selected packages can be constructed easily.
        self._rememberWhy(seedname, pkg, why, build_tree, recommends)
        self._rememberWhy("all", pkg, why, build_tree, recommends)

        for prov in self.packages[pkg]["Provides"]:
            if prov[0][0] not in self.pkgprovides:
                self.pkgprovides[prov[0][0]] = set()
            self.pkgprovides[prov[0][0]].add(pkg)

        self._addDependencyTree(seedname, pkg,
                                self.packages[pkg]["Pre-Depends"],
                                second_class=second_class,
                                build_tree=build_tree)

        self._addDependencyTree(seedname, pkg, self.packages[pkg]["Depends"],
                                second_class=second_class,
                                build_tree=build_tree)

        if (self._followRecommends(seedname) or
            self.packages[pkg]["Section"] == "metapackages"):
            self._addDependencyTree(seedname, pkg,
                                    self.packages[pkg]["Recommends"],
                                    second_class=second_class,
                                    build_tree=build_tree,
                                    recommends=True)

        src = self.packages[pkg]["Source"]
        if src not in self.sources:
            logging.error("Missing source package: %s (for %s)", src, pkg)
            return

        if second_class:
            for seed in self.structure.innerSeeds(seedname):
                if src in self.build_srcs[seed]:
                    return
        else:
            for seed in self.structure.innerSeeds(seedname):
                if src in self.not_build_srcs[seed]:
                    return

        if build_tree:
            self.build_sourcepkgs[seedname].add(src)
            if src in self.blacklist:
                self.blacklisted.add(src)

        else:
            if src in self.all_srcs:
                for buildseed in self.seeds:
                    self.build_sourcepkgs[buildseed].discard(src)

            self.not_build_srcs[seedname].add(src)
            self.sourcepkgs[seedname].add(src)

        self.all_srcs.add(src)
        self.build_srcs[seedname].add(src)

        self._addDependencyTree(seedname, pkg,
                                self.sources[src]["Build-Depends"],
                                build_depend=True)
        self._addDependencyTree(seedname, pkg,
                                self.sources[src]["Build-Depends-Indep"],
                                build_depend=True)

    def _rescueIncludes(self, seedname, rescue_seedname, build_tree):
        """Automatically rescue packages matching certain patterns from
        other seeds."""

        if seedname not in self.seeds and seedname != "extra":
            return
        if rescue_seedname not in self.seeds and rescue_seedname != "extra":
            return

        # Find all the source packages.
        rescue_srcs = set()
        if rescue_seedname == "extra":
            rescue_seeds = self.structure.innerSeeds(seedname)
        else:
            rescue_seeds = [rescue_seedname]
        for seed in rescue_seeds:
            if build_tree:
                rescue_srcs |= self.build_srcs[seed]
            else:
                rescue_srcs |= self.not_build_srcs[seed]

        # For each source, add any binaries that match the include/exclude
        # patterns.
        for src in rescue_srcs:
            rescue = [p for p in self.sources[src]["Binaries"]
                        if p in self.packages]
            included = set()
            if (seedname in self.includes and
                rescue_seedname in self.includes[seedname]):
                for include in self.includes[seedname][rescue_seedname]:
                    included |= set(self._filterPackages(rescue, include))
            if (seedname in self.excludes and
                rescue_seedname in self.excludes[seedname]):
                for exclude in self.excludes[seedname][rescue_seedname]:
                    included -= set(self._filterPackages(rescue, exclude))
            for pkg in included:
                if pkg in self.all:
                    continue
                for lesserseed in self.structure.strictlyOuterSeeds(seedname):
                    if pkg in self.seed[lesserseed]:
                        self.seed[lesserseed].remove(pkg)
                        logging.warning("Promoted %s from %s to %s due to "
                                        "%s-Includes",
                                        pkg, lesserseed, seedname,
                                        rescue_seedname.title())
                        break
                logging.debug("Rescued %s from %s to %s", pkg,
                              rescue_seedname, seedname)
                if build_tree:
                    self.build_depends[seedname].add(pkg)
                else:
                    self.depends[seedname].add(pkg)
                self._addPackage(seedname, pkg, "Rescued from %s" % src,
                                 build_tree=build_tree)

    def writeList(self, whyname, filename, pkgset):
        pkglist = list(pkgset)
        pkglist.sort()

        pkg_len = len("Package")
        src_len = len("Source")
        why_len = len("Why")
        mnt_len = len("Maintainer")

        for pkg in pkglist:
            _pkg_len = len(pkg)
            if _pkg_len > pkg_len: pkg_len = _pkg_len

            _src_len = len(self.packages[pkg]["Source"])
            if _src_len > src_len: src_len = _src_len

            _why_len = len(self.why[whyname][pkg][0])
            if _why_len > why_len: why_len = _why_len

            _mnt_len = len(self.packages[pkg]["Maintainer"])
            if _mnt_len > mnt_len: mnt_len = _mnt_len

        size = 0
        installed_size = 0

        pkglist.sort()
        with codecs.open(filename, "w", "utf8", "replace") as f:
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
                size += self.packages[pkg]["Size"]
                installed_size += self.packages[pkg]["Installed-Size"]
                print >>f, "%-*s | %-*s | %-*s | %-*s | %15d | %15d" % \
                      (pkg_len, pkg,
                       src_len, self.packages[pkg]["Source"],
                       why_len, self.why[whyname][pkg][0],
                       mnt_len, self.packages[pkg]["Maintainer"],
                       self.packages[pkg]["Size"],
                       self.packages[pkg]["Installed-Size"])
            print >>f, ("-" * (pkg_len + src_len + why_len + mnt_len + 9)) \
                  + "-+-" + ("-" * 15) + "-+-" + ("-" * 15) + "-"
            print >>f, "%*s | %15d | %15d" % \
                  ((pkg_len + src_len + why_len + mnt_len + 9), "",
                   size, installed_size)

    def writeSourceList(self, filename, srcset):
        srclist = list(srcset)
        srclist.sort()

        src_len = len("Source")
        mnt_len = len("Maintainer")

        for src in srclist:
            _src_len = len(src)
            if _src_len > src_len: src_len = _src_len

            _mnt_len = len(self.sources[src]["Maintainer"])
            if _mnt_len > mnt_len: mnt_len = _mnt_len

        srclist.sort()
        with codecs.open(filename, "w", "utf8", "replace") as f:
            fmt = "%-*s | %-*s"

            print >>f, fmt % (src_len, "Source", mnt_len, "Maintainer")
            print >>f, ("-" * src_len) + "-+-" + ("-" * mnt_len) + "-"
            for src in srclist:
                print >>f, fmt % (src_len, src, mnt_len,
                                  self.sources[src]["Maintainer"])

    def writeRdependList(self, filename, pkg):
        with open(filename, "w") as f:
            print >>f, pkg
            self._writeRdependList(f, pkg, "", done=set())

    def _writeRdependList(self, f, pkg, prefix, stack=None, done=None):
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

        for seed in self.seeds:
            if pkg in self.seed[seed]:
                print >>f, prefix + "*", seed.title(), "seed"

        if "Reverse-Depends" not in self.packages[pkg]:
            return

        for field in ("Pre-Depends", "Depends", "Recommends",
                      "Build-Depends", "Build-Depends-Indep"):
            if field not in self.packages[pkg]["Reverse-Depends"]:
                continue

            i = 0
            print >>f, prefix + "*", "Reverse", field + ":"
            for dep in self.packages[pkg]["Reverse-Depends"][field]:
                i += 1
                print >>f, prefix + " +- " + dep
                if field.startswith("Build-"):
                    continue

                if i == len(self.packages[pkg]["Reverse-Depends"][field]):
                    extra = "    "
                else:
                    extra = " |  "
                self._writeRdependList(f, dep, prefix + extra, stack, done)

    def writeProvidesList(self, filename):
        provides = self.pkgprovides.keys()
        provides.sort()

        with open(filename, "w") as f:
            for prov in provides:
                print >>f, prov

                provlist = list(self.pkgprovides[prov])
                provlist.sort()
                for pkg in provlist:
                    print >>f, "\t%s" % (pkg,)
                print >>f

    def writeSeedText(self, filename, seedtext):
        with open(filename, "w") as f:
            for line in seedtext:
                print >>f, line.rstrip('\n')


def pretty_logging():
    logging.addLevelName(logging.DEBUG, '  ')
    logging.addLevelName(Germinator.PROGRESS, '')
    logging.addLevelName(logging.INFO, '* ')
    logging.addLevelName(logging.WARNING, '! ')
    logging.addLevelName(logging.ERROR, '? ')
