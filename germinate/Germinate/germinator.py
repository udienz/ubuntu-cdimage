# -*- coding: UTF-8 -*-
"""Expand seeds into dependency-closed lists of packages."""

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

import sys
import apt_pkg
import re
import fnmatch
import logging

import Germinate.seeds
import Germinate.tsort

# TODO: would be much more elegant to reduce our recursion depth!
sys.setrecursionlimit(2000)

class Germinator:
    PROGRESS = 15

    def __init__(self):
        self.packages = {}
        self.packagetype = {}
        self.provides = {}
        self.sources = {}
        self.pruned = {}

        self.structure = []
        self.features = set()
        self.seeds = []
        self.seed = {}
        self.seedfeatures = {}
        self.seedrecommends = {}
        self.seedinherit = {}
        self.seedrelease = {}
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

    def debug(self, msg, *args, **kwargs):
        logging.debug(msg, *args, **kwargs)

    def progress(self, msg, *args, **kwargs):
        logging.getLogger().log(self.PROGRESS, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        logging.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        logging.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        logging.error(msg, *args, **kwargs)

    def parseStructureFile(self, f):
        """Parse a seed structure file. This is an ordered sequence of lines
        as follows:

        SEED:[ INHERITED]

        INHERITED is a space-separated list of seeds from which SEED
        inherits. For example, "ship: base desktop" indicates that packages
        in the "ship" seed may depend on packages in the "base" or "desktop"
        seeds without requiring those packages to appear in the "ship"
        output. INHERITED may be empty.

        The lines should be topologically sorted with respect to
        inheritance, with inherited-from seeds at the start.

        Any line as follows:

        include BRANCH

        causes another seed branch to be included. Seed names will be
        resolved in included branches if they cannot be found in the current
        branch.

        Returns (ordered list of seed names, dict of SEED -> INHERITED,
        branches, structure)."""
        seednames = []
        seedinherit = {}
        seedbranches = []
        lines = []

        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                continue
            words = line.split()
            if words[0].endswith(':'):
                seed = words[0][:-1]
                seednames.append(seed)
                seedinherit[seed] = list(words[1:])
                lines.append(line)
            elif words[0] == 'include':
                seedbranches.extend(words[1:])
            elif words[0] == 'feature':
                self.features.update(words[1:])
            else:
                self.error("Unparseable seed structure entry: %s", line)
        f.close()

        return (seednames, seedinherit, seedbranches, lines)

    def parseStructure(self, seed_base, branch, bzr=False, got_branches=None):
        """Like parseStructureFile, but deals with acquiring the seed
        structure files and recursively acquiring any seed structure files
        it includes. got_branches is for internal use only."""
        if got_branches is None:
            top_level = True
            got_branches = set()
        else:
            top_level = False
        all_names = []
        all_inherit = {}
        all_branches = []
        all_structure = []

        if branch in got_branches:
            return all_names, all_inherit, all_branches, all_structure

        # Fetch this one
        seed = Germinate.seeds.open_seed(seed_base, branch, "STRUCTURE", bzr)
        names, inherit, branches, structure = self.parseStructureFile(seed)
        branches.insert(0, branch)
        got_branches.add(branch)

        # Recursively expand included branches
        for child_branch in branches:
            child_names, child_inherit, child_branches, child_structure = \
                self.parseStructure(seed_base, child_branch, bzr, got_branches)
            for grandchild_name in child_names:
                all_names.append(grandchild_name)
            all_inherit.update(child_inherit)
            for grandchild_branch in child_branches:
                if grandchild_branch not in all_branches:
                    all_branches.append(grandchild_branch)
            for child_structure_line in child_structure:
                child_structure_name = child_structure_line.split()[0][:-1]
                for i in range(len(all_structure)):
                    if all_structure[i].split()[0][:-1] == child_structure_name:
                        del all_structure[i]
                        break
                all_structure.append(child_structure_line)

        # Attach the main branch's data to the end
        for child_name in names:
            all_names.append(child_name)
        all_inherit.update(inherit)
        for child_branch in branches:
            if child_branch not in all_branches:
                all_branches.append(child_branch)
        for structure_line in structure:
            structure_name = structure_line.split()[0][:-1]
            for i in range(len(all_structure)):
                if all_structure[i].split()[0][:-1] == structure_name:
                    del all_structure[i]
                    break
            all_structure.append(structure_line)

        # We generally want to process branches in reverse order, so that
        # later branches can override seeds from earlier branches
        all_branches.reverse()

        if top_level:
            self.structure = all_structure
            self.supported = all_names[-1]
            # TODO: The None return here is unsightly; it's due to signature
            # consistency with the recursive form.
            return all_names, all_inherit, all_branches, None
        else:
            return all_names, all_inherit, all_branches, all_structure

    def expandInheritance(self, unused_all_names, all_inherit, all_branches):
        """Expand out incomplete inheritance lists"""
        order = Germinate.tsort.topo_sort(all_inherit)
        for name in order:
            seen = set()
            new_inherit = []
            for inheritee in all_inherit[name]:
                for expanded in all_inherit[inheritee]:
                    if expanded not in seen:
                        new_inherit.append(expanded)
                        seen.add(expanded)
                if inheritee not in seen:
                    new_inherit.append(inheritee)
                    seen.add(inheritee)
            all_inherit[name] = new_inherit

        return order, all_inherit, all_branches

    def parseHints(self, f):
        """Parse a hints file."""
        for line in f:
            if line.startswith("#") or not len(line.rstrip()): continue

            words = line.rstrip().split(None)
            if len(words) != 2:
                continue

            self.hints[words[1]] = words[0]
        f.close()

    def parsePackages(self, tag_files, pkgtype):
        """Parse a Packages file and get the information we need."""
        for f in tag_files:
            for section in apt_pkg.TagFile(f):
                pkg = section["Package"]
                ver = section["Version"]
                last_ver = None

                # If there is a previous package info stored, fetch
                # the version to compare them.
                if pkg in self.packages:
                    last_ver = self.packages[pkg]["Version"]

                # If this is a new package, or if the stored version
                # is older than the new version, store the new
                # package.
                if (pkg not in self.packages or
                    apt_pkg.version_compare(last_ver, ver) < 0):
                    self.packages[pkg] = {}
                    self.packagetype[pkg] = pkgtype
                    self.pruned[pkg] = set()

                    self.packages[pkg]["Section"] = \
                        section.get("Section", "").split('/')[-1]

                    self.packages[pkg]["Version"] = section.get("Version")

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
            f.close()

    def parseSources(self, tag_files):
        """Parse a Sources file and get the information we need."""
        for f in tag_files:
            for section in apt_pkg.TagFile(f):
                src = section["Package"]
                ver = section["Version"]
                last_ver = None

                if src in self.sources:
                    last_ver = self.sources[src]["Version"]

                if (src not in self.sources or
                    apt_pkg.version_compare(last_ver, ver) < 0):
                    self.sources[src] = {}

                    self.sources[src]["Maintainer"] = \
                        unicode(section.get("Maintainer", ""), "utf8", "replace")
                    self.sources[src]["IPv6"] = "Unknown"
                    self.sources[src]["Version"] = ver

                    for field in "Build-Depends", "Build-Depends-Indep":
                        value = section.get(field, "")
                        self.sources[src][field] = apt_pkg.parse_src_depends(value)

                    binaries = apt_pkg.parse_depends(section.get("Binary", src))
                    self.sources[src]["Binaries"] = [ b[0][0] for b in binaries ]

            f.close()

    def parseIPv6(self, f):
        """Parse the IPv6 dailydump file and get the information we need."""
        for line in f:
            (src, info) = line.split(None, 1)
            if src in self.sources:
                self.sources[src]["IPv6"] = info.strip()
        f.close()

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

        fh = open(filename, 'w')
        sorted_blacklisted = list(self.blacklisted)
        sorted_blacklisted.sort()
        for pkg in sorted_blacklisted:
            blacklist = self.blacklist[pkg]
            fh.write('%s\t%s\n' % (pkg, blacklist))
        fh.close()

    def newSeed(self, seedname, seedinherit, seedrelease):
        self.seeds.append(seedname)
        self.seed[seedname] = []
        self.seedfeatures[seedname] = set()
        self.seedrecommends[seedname] = []
        self.seedinherit[seedname] = seedinherit
        self.seedrelease[seedname] = seedrelease
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

    def filterPackages(self, packages, pattern):
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

    def substituteSeedVars(self, pkg):
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
                    self.error("Undefined seed substvar: %s", name)
            else:
                for substpieces in substituted:
                    substpieces.append(piece)

        substpkgs = []
        for substpieces in substituted:
            substpkgs.append("".join(substpieces))
        return substpkgs

    def innerSeeds(self, seedname):
        """Return this seed and the seeds from which it inherits."""
        innerseeds = list(self.seedinherit[seedname])
        innerseeds.append(seedname)
        return innerseeds

    def strictlyOuterSeeds(self, seedname):
        """Return the seeds that inherit from this seed."""
        outerseeds = []
        for seed in self.seeds:
            if seedname in self.seedinherit[seed]:
                outerseeds.append(seed)
        return outerseeds

    def outerSeeds(self, seedname):
        """Return this seed and the seeds that inherit from it."""
        outerseeds = [seedname]
        outerseeds.extend(self.strictlyOuterSeeds(seedname))
        return outerseeds

    def alreadySeeded(self, seedname, pkg):
        """Has pkg already been seeded in this seed or in one from
        which we inherit?"""

        for seed in self.innerSeeds(seedname):
            if (pkg in self.seed[seed] or
                pkg in self.seedrecommends[seed]):
                return True

        return False

    def plantSeed(self, entries, arch, seedname, seedinherit, seedrelease=None):
        """Add a seed."""
        if seedname in self.seeds:
            return

        self.newSeed(seedname, seedinherit, seedrelease)
        seedpkgs = []
        seedrecommends = []

        for line in entries:
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
                    self.warning("Allowing d-i kernel versions: %s", values)
                    self.di_kernel_versions[seedname].update(values)
                elif name == "feature":
                    self.warning("Setting features {%s} for seed %s",
                        ', '.join(values), seedname)
                    self.seedfeatures[seedname].update(values)
                elif name.endswith("-include"):
                    included_seed = name[:-8]
                    if (included_seed not in self.seeds and
                        included_seed != "extra"):
                        self.error("Cannot include packages from unknown "
                                   "seed: %s", included_seed)
                    else:
                        self.warning("Including packages from %s: %s",
                                     included_seed, values)
                        if included_seed not in self.includes[seedname]:
                            self.includes[seedname][included_seed] = []
                        self.includes[seedname][included_seed].extend(values)
                elif name.endswith("-exclude"):
                    excluded_seed = name[:-8]
                    if (excluded_seed not in self.seeds and
                        excluded_seed != "extra"):
                        self.error("Cannot exclude packages from unknown "
                                   "seed: %s", excluded_seed)
                    else:
                        self.warning("Excluding packages from %s: %s",
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
                    if arch in negarch:
                        continue
                    if posarch and arch not in posarch:
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
                pkgs =  self.filterPackages(self.packages, pkg)
                if not pkgs:
                    pkgs = [pkg] # virtual or expanded; check again later
                for pkg in pkgs:
                    seedrecommends.extend(self.substituteSeedVars(pkg))

            if pkg.startswith('%'):
                pkg = pkg[1:]
                if pkg in self.sources:
                    pkgs = [p for p in self.sources[pkg]["Binaries"]
                              if p in self.packages]
                else:
                    self.warning("Unknown source package: %s", pkg)
                    pkgs = []
            else:
                pkgs = self.filterPackages(self.packages, pkg)
                if not pkgs:
                    pkgs = [pkg] # virtual or expanded; check again later

            if is_blacklist:
                for pkg in pkgs:
                    self.info("Blacklisting %s from %s", pkg, seedname)
                    self.seedblacklist[seedname].update(
                        self.substituteSeedVars(pkg))
            else:
                for pkg in pkgs:
                    seedpkgs.extend(self.substituteSeedVars(pkg))

        for pkg in seedpkgs:
            if pkg in self.hints and self.hints[pkg] != seedname:
                self.warning("Taking the hint: %s", pkg)
                continue

            if pkg in self.packages:
                # Ordinary package
                if self.alreadySeeded(seedname, pkg):
                    self.warning("Duplicated seed: %s", pkg)
                elif self.is_pruned(pkg, seedname):
                    self.warning("Pruned %s from %s", pkg, seedname)
                else:
                    if pkg in seedrecommends:
                        self.seedrecommends[seedname].append(pkg)
                    else:
                        self.seed[seedname].append(pkg)
            elif pkg in self.provides:
                # Virtual package, include everything
                msg = "Virtual %s package: %s" % (seedname, pkg)
                for vpkg in self.provides[pkg]:
                    if self.alreadySeeded(seedname, vpkg):
                        pass
                    elif seedname in self.pruned[vpkg]:
                        pass
                    else:
                        msg += "\n  - %s" % vpkg
                        if pkg in seedrecommends:
                            self.seedrecommends[seedname].append(vpkg)
                        else:
                            self.seed[seedname].append(vpkg)
                self.info("%s", msg)

            else:
                # No idea
                self.error("Unknown %s package: %s", seedname, pkg)

        for pkg in self.hints:
            if self.hints[pkg] == seedname and not self.alreadySeeded(seedname, pkg):
                if pkg in self.packages:
                    if pkg in seedrecommends:
                        self.seedrecommends[seedname].append(pkg)
                    else:
                        self.seed[seedname].append(pkg)
                else:
                    self.error("Unknown hinted package: %s", pkg)

    def is_pruned(self, pkg, seed):
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
                if self.is_pruned(pkg, seed):
                    self.pruned[pkg].add(seed)

    def weedBlacklist(self, pkgs, seedname, build_tree, why):
        """Weed out blacklisted seed entries from a list."""
        white = []
        if build_tree:
            outerseeds = [self.supported]
        else:
            outerseeds = self.outerSeeds(seedname)
        for pkg in pkgs:
            for outerseed in outerseeds:
                if (outerseed in self.seedblacklist and
                    pkg in self.seedblacklist[outerseed]):
                    self.error("Package %s blacklisted in %s but seeded in "
                               "%s (%s)", pkg, outerseed, seedname, why)
                    break
            else:
                white.append(pkg)
        return white

    def grow(self):
        """Grow the seeds."""
        for seedname in self.seeds:
            self.progress("Resolving %s dependencies ...", seedname)
            if self.seedrelease[seedname] is None:
                why = "%s seed" % seedname.title()
            else:
                why = ("%s %s seed" %
                       (self.seedrelease[seedname].title(), seedname))

            # Check for blacklisted seed entries.
            self.seed[seedname] = self.weedBlacklist(
                self.seed[seedname], seedname, False, why)
            self.seedrecommends[seedname] = self.weedBlacklist(
                self.seedrecommends[seedname], seedname, False, why)

            # Note that seedrecommends are not processed with
            # recommends=True; that is reserved for Recommends of packages,
            # not packages recommended by the seed. Changing this results in
            # less helpful output when a package is recommended by an inner
            # seed and required by an outer seed.
            for pkg in self.seed[seedname] + self.seedrecommends[seedname]:
                self.addPackage(seedname, pkg, why)

            for rescue_seedname in self.seeds:
                self.rescueIncludes(seedname, rescue_seedname,
                                    build_tree=False)
                if rescue_seedname == seedname:
                    # only rescue from seeds up to and including the current
                    # seed; later ones have not been grown
                    break
            self.rescueIncludes(seedname, "extra", build_tree=False)

        self.rescueIncludes(self.supported, "extra", build_tree=True)

    def addExtras(self, seedrelease=None):
        """Add packages generated by the sources but not in any seed."""
        self.newSeed("extra", self.seeds, seedrelease)

        self.progress("Identifying extras ...")
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
                        self.warning("Taking the hint: %s", pkg)
                        continue

                    self.seed["extra"].append(pkg)
                    self.addPackage("extra", pkg, "Generated by " + srcname,
                                    second_class=True)
                    found = True

    def allowedDependency(self, pkg, depend, seedname, build_depend):
        """Is pkg allowed to satisfy a (build-)dependency using depend
           within seedname? Note that depend must be a real package.
           
           If seedname is None, check whether the (build-)dependency is
           allowed within any seed."""
        if depend not in self.packages:
            self.warning("allowedDependency called with virtual package %s", depend)
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

    def allowedVirtualDependency(self, pkg, deptype):
        """May pkg's dependency relationship type deptype be satisfied by a
           virtual package? (Versioned dependencies may not be satisfied by
           virtual packages, unless pkg is a udeb.)"""
        if pkg in self.packagetype and self.packagetype[pkg] == "udeb":
            return True
        elif deptype == "":
            return True
        else:
            return False

    def checkVersionedDependency(self, depname, depver, deptype):
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
            self.error("Unknown dependency comparator: %s" % deptype)
            return False

    def unparseDependency(self, depname, depver, deptype):
        """Return a string representation of a dependency."""
        if deptype == "":
            return depname
        else:
            return "%s (%s %s)" % (depname, deptype, depver)

    def followRecommends(self, seed=None):
        """Should we follow Recommends for this seed?"""
        if seed is not None and seed in self.seedfeatures:
            if "follow-recommends" in self.seedfeatures[seed]:
                return True
            if "no-follow-recommends" in self.seedfeatures[seed]:
                return False
        if "follow-recommends" in self.features:
            return True
        return False

    def addReverse(self, pkg, field, rdep):
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
            if (self.followRecommends() or
                self.packages[pkg]["Section"] == "metapackages"):
                fields.append("Recommends")
            for field in fields:
                for deplist in self.packages[pkg][field]:
                    for dep in deplist:
                        if dep[0] in self.all and \
                           self.allowedDependency(pkg, dep[0], None, False):
                            self.addReverse(dep[0], field, pkg)

        for src in self.all_srcs:
            for field in "Build-Depends", "Build-Depends-Indep":
                for deplist in self.sources[src][field]:
                    for dep in deplist:
                        if dep[0] in self.all and \
                           self.allowedDependency(src, dep[0], None, True):
                            self.addReverse(dep[0], field, src)

        for pkg in self.all:
            if "Reverse-Depends" not in self.packages[pkg]:
                continue

            fields = ["Pre-Depends", "Depends"]
            if (self.followRecommends() or
                self.packages[pkg]["Section"] == "metapackages"):
                fields.append("Recommends")
            fields.extend(["Build-Depends", "Build-Depends-Indep"])
            for field in fields:
                if field not in self.packages[pkg]["Reverse-Depends"]:
                    continue

                self.packages[pkg]["Reverse-Depends"][field].sort()

    def alreadySatisfied(self, seedname, pkg, depend, build_depend=False, with_build=False):
        """Work out whether a dependency has already been satisfied."""
        (depname, depver, deptype) = depend
        if self.allowedVirtualDependency(pkg, deptype) and depname in self.provides:
            trylist = [ d for d in self.provides[depname]
                        if d in self.packages and self.allowedDependency(pkg, d, seedname, build_depend) ]
        elif (self.checkVersionedDependency(depname, depver, deptype) and
              self.allowedDependency(pkg, depname, seedname, build_depend)):
            trylist = [ depname ]
        else:
            return False

        for trydep in trylist:
            if with_build:
                for seed in self.innerSeeds(seedname):
                    if trydep in self.build[seed]:
                        return True
            else:
                for seed in self.innerSeeds(seedname):
                    if trydep in self.not_build[seed]:
                        return True
            if (trydep in self.seed[seedname] or
                trydep in self.seedrecommends[seedname]):
                return True
        else:
            return False

    def addDependency(self, seedname, pkg, dependlist, build_depend,
                      second_class, build_tree, recommends):
        """Add a single dependency. Returns True if a dependency was added,
           otherwise False."""
        if build_tree and build_depend:
            why = self.packages[pkg]["Source"] + " (Build-Depend)"
        elif recommends:
            why = pkg + " (Recommends)"
        else:
            why = pkg

        dependlist = self.weedBlacklist(dependlist, seedname, build_tree, why)
        if not dependlist:
            return False

        if build_tree:
            for dep in dependlist:
                self.build_depends[seedname].add(dep)
        else:
            for dep in dependlist:
                self.depends[seedname].add(dep)

        for dep in dependlist:
            self.addPackage(seedname, dep, why,
                            build_tree, second_class, recommends)

        return True

    def promoteDependency(self, seedname, pkg, depend, close, build_depend,
                          second_class, build_tree, recommends):
        """Try to satisfy a dependency by promoting an item from a lesser
           seed. If close is True, only "close-by" seeds (ones that generate
           the same task, as defined by Task-Seeds headers) are considered.
           Returns True if a dependency was added, otherwise False."""
        (depname, depver, deptype) = depend
        if (self.checkVersionedDependency(depname, depver, deptype) and
            self.allowedDependency(pkg, depname, seedname, build_depend)):
            trylist = [ depname ]
        elif (self.allowedVirtualDependency(pkg, deptype) and
              depname in self.provides):
            trylist = [ d for d in self.provides[depname]
                        if d in self.packages and
                           self.allowedDependency(pkg, d, seedname,
                                                  build_depend) ]
        else:
            return False

        for trydep in trylist:
            lesserseeds = self.strictlyOuterSeeds(seedname)
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
                        self.warning("Promoted %s from %s to %s to satisfy %s",
                                     trydep, lesserseed, seedname, pkg)

                    return self.addDependency(seedname, pkg, [trydep],
                                              build_depend, second_class,
                                              build_tree, recommends)

        return False

    def newDependency(self, seedname, pkg, depend, build_depend,
                      second_class, build_tree, recommends):
        """Try to satisfy a dependency by adding a new package to the output
           set. Returns True if a dependency was added, otherwise False."""
        (depname, depver, deptype) = depend
        if (self.checkVersionedDependency(depname, depver, deptype) and
            self.allowedDependency(pkg, depname, seedname, build_depend)):
            virtual = None
        elif self.allowedVirtualDependency(pkg, deptype) and depname in self.provides:
            virtual = depname
        else:
            if build_depend:
                desc = "build-dependency"
            elif recommends:
                desc = "recommendation"
            else:
                desc = "dependency"
            self.error("Unknown %s %s by %s", desc,
                       self.unparseDependency(depname, depver, deptype), pkg)
            return False

        dependlist = [depname]
        if virtual is not None:
            reallist = [ d for d in self.provides[virtual]
                         if d in self.packages and self.allowedDependency(pkg, d, seedname, build_depend) ]
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
                self.info("Chose %s out of %s to satisfy %s",
                          ", ".join(dependlist), virtual, pkg)
            else:
                self.error("Nothing to choose out of %s to satisfy %s",
                           virtual, pkg)
                return False

        return self.addDependency(seedname, pkg, dependlist, build_depend,
                                  second_class, build_tree, recommends)

    def addDependencyTree(self, seedname, pkg, depends,
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
                # calling rememberWhy with a dependency, so self.why will be
                # a bit inaccurate. We may need another pass for Recommends
                # to fix this.
                if self.alreadySatisfied(seedname, pkg, dep, build_depend, second_class):
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
                    if self.promoteDependency(seedname, pkg, dep, close,
                                              build_depend, second_class,
                                              build_tree, recommends):
                        if len(deplist) > 1:
                            self.info("Chose %s to satisfy %s", dep[0], pkg)
                        break
                else:
                    for dep in deplist:
                        if self.newDependency(seedname, pkg, dep, build_depend,
                                              second_class, build_tree,
                                              recommends):
                            if len(deplist) > 1:
                                self.info("Chose %s to satisfy %s", dep[0],
                                          pkg)
                            break
                    else:
                        if len(deplist) > 1:
                            self.error("Nothing to choose to satisfy %s", pkg)

    def rememberWhy(self, seedname, pkg, why, build_tree=False,
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

    def addPackage(self, seedname, pkg, why,
                   second_class=False,
                   build_tree=False,
                   recommends=False):
        """Add a package and its dependency trees."""
        if seedname in self.pruned[pkg]:
            self.warning("Pruned %s from %s", pkg, seedname)
            return
        if build_tree:
            outerseeds = [self.supported]
        else:
            outerseeds = self.outerSeeds(seedname)
        for outerseed in outerseeds:
            if (outerseed in self.seedblacklist and
                pkg in self.seedblacklist[outerseed]):
                self.error("Package %s blacklisted in %s but seeded in %s "
                           "(%s)", pkg, outerseed, seedname, why)
                return
        if build_tree: second_class=True

        if pkg not in self.all:
            self.all.add(pkg)
        elif not build_tree:
            for buildseed in self.innerSeeds(seedname):
                self.build_depends[buildseed].discard(pkg)

        for seed in self.innerSeeds(seedname):
            if pkg in self.build[seed]:
                break
        else:
            self.build[seedname].add(pkg)

        if not build_tree:
            for seed in self.innerSeeds(seedname):
                if pkg in self.not_build[seed]:
                    break
            else:
                self.not_build[seedname].add(pkg)

        # Remember why the package was added to the output for this seed.
        # Also remember a reason for "all" too, so that an aggregated list
        # of all selected packages can be constructed easily.
        self.rememberWhy(seedname, pkg, why, build_tree, recommends)
        self.rememberWhy("all", pkg, why, build_tree, recommends)

        for prov in self.packages[pkg]["Provides"]:
            if prov[0][0] not in self.pkgprovides:
                self.pkgprovides[prov[0][0]] = set()
            self.pkgprovides[prov[0][0]].add(pkg)

        self.addDependencyTree(seedname, pkg,
                               self.packages[pkg]["Pre-Depends"],
                               second_class=second_class,
                               build_tree=build_tree)

        self.addDependencyTree(seedname, pkg, self.packages[pkg]["Depends"],
                               second_class=second_class,
                               build_tree=build_tree)

        if (self.followRecommends(seedname) or
            self.packages[pkg]["Section"] == "metapackages"):
            self.addDependencyTree(seedname, pkg,
                                   self.packages[pkg]["Recommends"],
                                   second_class=second_class,
                                   build_tree=build_tree,
                                   recommends=True)

        src = self.packages[pkg]["Source"]
        if src not in self.sources:
            self.error("Missing source package: %s (for %s)", src, pkg)
            return

        if second_class:
            for seed in self.innerSeeds(seedname):
                if src in self.build_srcs[seed]:
                    return
        else:
            for seed in self.innerSeeds(seedname):
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

        self.addDependencyTree(seedname, pkg,
                               self.sources[src]["Build-Depends"],
                               build_depend=True)
        self.addDependencyTree(seedname, pkg,
                               self.sources[src]["Build-Depends-Indep"],
                               build_depend=True)

    def rescueIncludes(self, seedname, rescue_seedname, build_tree):
        """Automatically rescue packages matching certain patterns from
        other seeds."""

        if seedname not in self.seeds and seedname != "extra":
            return
        if rescue_seedname not in self.seeds and rescue_seedname != "extra":
            return

        # Find all the source packages.
        rescue_srcs = set()
        if rescue_seedname == "extra":
            rescue_seeds = self.innerSeeds(seedname)
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
                    included |= set(self.filterPackages(rescue, include))
            if (seedname in self.excludes and
                rescue_seedname in self.excludes[seedname]):
                for exclude in self.excludes[seedname][rescue_seedname]:
                    included -= set(self.filterPackages(rescue, exclude))
            for pkg in included:
                if pkg in self.all:
                    continue
                for lesserseed in self.strictlyOuterSeeds(seedname):
                    if pkg in self.seed[lesserseed]:
                        self.seed[lesserseed].remove(pkg)
                        self.warning("Promoted %s from %s to %s due to "
                                     "%s-Includes",
                                     pkg, lesserseed, seedname,
                                     rescue_seedname.title())
                        break
                self.debug("Rescued %s from %s to %s", pkg,
                           rescue_seedname, seedname)
                if build_tree:
                    self.build_depends[seedname].add(pkg)
                else:
                    self.depends[seedname].add(pkg)
                self.addPackage(seedname, pkg, "Rescued from %s" % src,
                                build_tree=build_tree)

logging.addLevelName(logging.DEBUG, '  ')
logging.addLevelName(Germinator.PROGRESS, '')
logging.addLevelName(logging.INFO, '* ')
logging.addLevelName(logging.WARNING, '! ')
logging.addLevelName(logging.ERROR, '? ')
