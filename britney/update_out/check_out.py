#!/usr/bin/env python2.6

import sys
import britney;

arches = [ 'amd64', 'hppa', 'i386', 'ia64', 'powerpc', 'sparc' ]
arches.sort()

print arches

if len(sys.argv) == 2:
	dir = sys.argv[1];
else:
	dir = ''

testing = britney.Sources(dir, arches)
testingpkgs = {}
for arch in testing.arches:
	testingpkgs[arch] = testing.Packages(arch)

x = ''
for arch in testing.arches:
	cnt = 0
	for pkg in testingpkgs[arch].packages:
		if not testingpkgs[arch].is_installable(pkg):
			src = testingpkgs[arch].get_source(pkg)
			srcv = testingpkgs[arch].get_sourcever(pkg)
			print "%s %s %s (%s) uninstallable" \
				% (src, srcv, pkg, arch)
			cnt = cnt + 1
	if x != '':
		x = x + ':'
	x = x + ('%s-%d' % (arch[0], cnt))

print x

