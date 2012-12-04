CDIMAGE (alternate+live) for Ubuntu
-----------------------------------

This tools has many sub-tools, including
 * CD Image Script
 * debian-cd Script
 * germinate
 * britney
 * livecd-rootfs
 * ubuntu-archive-tools

Dependency
----------

Packages
========
sudo apt-get install build-essential bc dctrl-tools lynx mkisofs tofrodos \
	debootstrap procmail libapt-pkg-dev ubuntu-keyring syslinux fakeroot \
	rsync python-minimal procps squashfs-tools bittorrent bzr debmirror \
	python-apt python2.7 python2.7-dev xorriso
Misc
====
 * Complete Ubuntu Distribution, i mean if you want to build precise you *must*
   at least main, restricted, and source component
 * Indices you can grab from rsync://archive.ubuntu.com::ubuntu/indices/
 * debian-installer files
 * a huge space
