#!/usr/bin/env python

import britney
import sys
import re

arches = [ 'i386', 'alpha', 'm68k', 'sparc', 'powerpc', 'arm', 'hurd-i386', 'mips', 'mipsel', 'ia64', 'hppa', 's390' ]
arches.sort()

if len(sys.argv) == 2:
	dir = sys.argv[1];
else:
	dir = ''

testing = britney.Sources(dir, arches)
testingpkgs = {}
for arch in testing.arches:
	testingpkgs[arch] = testing.Packages(arch)

def same_source(sv1, sv2):
	if sv1 == sv2:
		return 1

	if re.search("-", sv1) or re.search("-", sv2):
		m = re.match(r'^(.*-\d+)\.0\.\d+$', sv1)
		if m: sv1 = m.group(1)
		m = re.match(r'^(.*-\d+\.\d+)\.\d+$', sv1)
		if m: sv1 = m.group(1)

		m = re.match(r'^(.*-\d+)\.0\.\d+$', sv2)
		if m: sv2 = m.group(1)
		m = re.match(r'^(.*-\d+\.\d+)\.\d+$', sv2)
		if m: sv2 = m.group(1)

		return (sv1 == sv2)
	else:
		m = re.match(r'^([^-]+)\.0\.\d+$', sv1)
		if m and sv2 == m.group(1): return 1

		m = re.match(r'^([^-]+)\.0\.\d+$', sv2)
		if m and sv1 == m.group(1): return 1

		return 0

noutdate = {}
for arch in testing.arches:
	cnt = bizcnt = 0
	for pkg in testingpkgs[arch].packages:
		pkgv = testingpkgs[arch].get_version(pkg)
		pkgsv = testingpkgs[arch].get_sourcever(pkg)
		src = testingpkgs[arch].get_source(pkg)
		srcv = testing.get_version(src)

		if not same_source(srcv, pkgsv):
			myarch = arch
			realarch = testingpkgs[arch].get_field(pkg, "Architecture")
			if realarch and re.match(r'^all', realarch):
				myarch = myarch + '/all'

			if britney.versioncmp(srcv, pkgsv) < 0:
				bizcnt = bizcnt + 1
				print "%s %s %s(%s) %s from %s ***" % \
					(src, srcv, pkg, myarch, pkgv, pkgsv)
			else:
				print "%s %s %s(%s) %s from %s" % \
					(src, srcv, pkg, myarch, pkgv, pkgsv)
			cnt = cnt + 1
	noutdate[arch] = (cnt, bizcnt)

print "Columns: number-out-of-date, number-newer-than-source, arch"
for arch in testing.arches:
	print "%8d %4d %s" % (noutdate[arch] + (arch,))
