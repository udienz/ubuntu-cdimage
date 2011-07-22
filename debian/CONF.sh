#
# This file will have to be sourced where needed
#

# Unset all optional variables first to start from a clean state
unset NONUS             || true
unset FORCENONUSONCD1   || true
unset NONFREE           || true
unset CONTRIB           || true
unset EXTRANONFREE      || true
unset RESTRICTED        || true
unset UNIVERSE          || true
unset MULTIVERSE        || true
# allow configuration on command line
#unset LOCAL             || true
#unset LOCALDEBS         || true
unset SECURED           || true
unset SECRET_KEYRING    || true
unset PUBLIC_KEYRING    || true
unset SIGNING_KEYID     || true
unset SECURITY          || true
unset BOOTDIR           || true
unset BOOTDISKS         || true
unset SYMLINK           || true
unset COPYLINK          || true
unset MKISOFS           || true
unset MKISOFS_OPTS      || true
unset ISOLINUX          || true
unset EXCLUDE           || true
unset SRCEXCLUDE        || true
unset NODEPENDS         || true
unset NORECOMMENDS      || true
unset NOSUGGESTS        || true
unset DOJIGDO           || true
unset JIGDOTEMPLATEURL  || true
unset JIGDOFALLBACKURLS || true
unset JIGDOINCLUDEURLS  || true
unset JIGDOSCRIPT       || true
unset JIGDO_OPTS        || true
unset DEFBINSIZE        || true
unset DEFSRCSIZE        || true
unset FASTSUMS          || true
unset PUBLISH_URL       || true
unset PUBLISH_NONUS_URL || true
unset PUBLISH_PATH      || true
unset UDEB_INCLUDE      || true
unset UDEB_EXCLUDE      || true
unset BASE_INCLUDE      || true
unset BASE_EXCLUDE      || true
unset INSTALLER_CD      || true
unset DI_CODENAME       || true
unset MAXCDS            || true
unset OMIT_MANUAL	    || true
unset OMIT_RELEASE_NOTES || true

if [ -z "$PROJECT" ]; then
  PROJECT=ubuntu
fi
if [ -z "$CAPPROJECT" ]; then
  CAPPROJECT="$(echo "$PROJECT" | perl -ne 'print ucfirst')"
fi

if [ -z "$DIST" ]; then
  DIST=karmic
fi

# The debian-cd dir
# Where I am (hoping I'm in the debian-cd dir)
export BASEDIR=`pwd`

case $DIST in
  warty)
    export CODENAME=warty
    export CAPCODENAME='Warty Warthog'
    export DEBVERSION=4.10
    export OFFICIAL="Linux+ Edition"
    ;;
  hoary)
    export CODENAME=hoary
    export CAPCODENAME='Hoary Hedgehog'
    export DEBVERSION=5.04
    export OFFICIAL="Release"
    ;;
  breezy)
    export CODENAME=breezy
    export CAPCODENAME='Breezy Badger'
    export DEBVERSION=5.10
    export OFFICIAL="Release"
    ;;
  dapper)
    export CODENAME=dapper
    export CAPCODENAME='Dapper Drake'
    export DEBVERSION=6.06.2
    export OFFICIAL="Release"
    ;;
  edgy)
    export CODENAME=edgy
    export CAPCODENAME='Edgy Eft'
    export DEBVERSION=6.10
    export OFFICIAL="Release"
    ;;
  feisty)
    export CODENAME=feisty
    export CAPCODENAME='Feisty Fawn'
    export DEBVERSION=7.04
    export OFFICIAL="Release"
    ;;
  gutsy)
    export PREV_CODENAME=feisty
    export CODENAME=gutsy
    export CAPCODENAME='Gutsy Gibbon'
    export DEBVERSION=7.10
    export OFFICIAL="Release"
    ;;
  hardy)
    export PREV_CODENAME=dapper # need to support upgrades from previous LTS
    export CODENAME=hardy
    export CAPCODENAME='Hardy Heron'
    export DEBVERSION=8.04.4
    export OFFICIAL="Release"
    ;;
  intrepid)
    export PREV_CODENAME=hardy
    export CODENAME=intrepid
    export CAPCODENAME='Intrepid Ibex'
    export DEBVERSION=8.10
    export OFFICIAL="Release"
    ;;
  jaunty)
    export PREV_CODENAME=intrepid
    export CODENAME=jaunty
    export CAPCODENAME='Jaunty Jackalope'
    export DEBVERSION=9.04
    export OFFICIAL="Release"
    ;;
  karmic)
    export PREV_CODENAME=jaunty
    export CODENAME=karmic
    export CAPCODENAME='Karmic Koala'
    export DEBVERSION=9.10
    export OFFICIAL="Release"
    ;;
  lucid)
    export PREV_CODENAME=karmic
    export CODENAME=lucid
    export CAPCODENAME='Lucid Lynx'
    export DEBVERSION=10.04.3
    case $PROJECT in
      ubuntu|ubuntu-server|kubuntu)
	DEBVERSION="$DEBVERSION LTS"
	;;
    esac
    export OFFICIAL="Release"
    ;;
  maverick)
    export PREV_CODENAME=lucid
    export CODENAME=maverick
    export CAPCODENAME='Maverick Meerkat'
    export DEBVERSION=10.10
    export OFFICIAL="Release"
    ;;
  natty)
    export PREV_CODENAME=maverick
    export CODENAME=natty
    export CAPCODENAME='Natty Narwhal'
    export DEBVERSION=11.04
    export OFFICIAL="Release"
    ;;
  oneiric)
    export PREV_CODENAME=natty
    export CODENAME=oneiric
    export CAPCODENAME='Oneiric Ocelot'
    export DEBVERSION=11.10
    export OFFICIAL="Alpha"
    ;;
esac

# By default use Debian installer packages from $CODENAME
if [ ! "$DI_CODENAME" ]
then
  export DI_CODENAME=$CODENAME
fi

# If set, controls where the d-i components are downloaded from.
# This may be an url, or "default", which will make it use the default url
# for the daily d-i builds. If not set, uses the official d-i images from
# the Debian mirror.
#export DI_WWW_HOME=default

# installer for properly uploaded debian-installer builds, daily-installer
# for autobuilt dailies. The newest available version is selected
# automatically; this is an override.
#export DI_TYPE=installer

# ... for arch  
export ARCH=`dpkg --print-architecture`

# IMPORTANT : The 4 following paths must be on the same partition/device.
#	      If they aren't then you must set COPYLINK below to 1. This
#	      takes a lot of extra room to create the sandbox for the ISO
#	      images, however. Also, if you are using an NFS partition for
#	      some part of this, you must use this option.
# Paths to the mirrors
export MIRROR=${MIRROR:-$CDIMAGE_ROOT/ftp}

# Comment the following line if you don't have/want non-US
#export NONUS=/ftp/debian-non-US

# And this option will make you 2 copies of CD1 - one with all the
# non-US packages on it, one with none. Useful if you're likely to
# need both.
#export FORCENONUSONCD1=1

# Path of the temporary directory
export TDIR=$CDIMAGE_ROOT/scratch/$PROJECT/$IMAGE_TYPE/tmp

# Path where the images will be written
export OUT=$CDIMAGE_ROOT/scratch/$PROJECT/$IMAGE_TYPE/debian-cd

# Where we keep the temporary apt stuff.
# This cannot reside on an NFS mount.
export APTTMP=$CDIMAGE_ROOT/scratch/$PROJECT/$IMAGE_TYPE/apt

# Where extracted debootstrap scripts live
export DEBOOTSTRAP=$CDIMAGE_ROOT/scratch/$PROJECT/$IMAGE_TYPE/debootstrap

# Where live filesystem images live
export LIVEIMAGES=$CDIMAGE_ROOT/scratch/$PROJECT/$IMAGE_TYPE/live

# Where preinstalled filesystem images live
export PREINSTALLEDIMAGES=$CDIMAGE_ROOT/scratch/$PROJECT/$IMAGE_TYPE/preinstalled

# Do I want to have NONFREE merged in the CD set
# export NONFREE=1

# Do I want to have CONTRIB merged in the CD set
#export CONTRIB=1

# Do I want to have NONFREE on a separate CD (the last CD of the CD set)
# WARNING: Don't use NONFREE and EXTRANONFREE at the same time !
# export EXTRANONFREE=1

if [ -z "$CDIMAGE_ONLYFREE" ]; then
  export RESTRICTED=1
fi

if [ "$CDIMAGE_UNSUPPORTED" ]; then
  export UNIVERSE=1
  if [ -z "$CDIMAGE_ONLYFREE" ]; then
    export MULTIVERSE=1
  fi
fi

# If you have a $MIRROR/dists/$CODENAME/local/binary-$ARCH dir with 
# local packages that you want to put on the CD set then
# uncomment the following line 
# export LOCAL=1

# If your local packages are not under $MIRROR, but somewhere else, 
# you can uncomment this line and edit to to point to a directory
# containing dists/$CODENAME/local/binary-$ARCH
# export LOCALDEBS=$CDIMAGE_ROOT/local/packages

# If you want a <codename>-secured tree with a copy of the signed
# Release.gpg and files listed by this Release file, then
# uncomment this line
# export SECURED=1

case $DIST in
  warty) ;;
  *)
    export SECRET_KEYRING=$CDIMAGE_ROOT/secret/dot-gnupg/secring.gpg
    export PUBLIC_KEYRING=$CDIMAGE_ROOT/secret/dot-gnupg/pubring.gpg
    export SIGNING_KEYID=FBB75451
    ;;
esac

# Where to find the security patches.  This directory should be the
# top directory of a security.debian.org mirror.
case $DIST in
  warty|hoary|breezy|dapper|edgy|feisty|gutsy|hardy|intrepid|jaunty|karmic|lucid)
    export SECURITY="$MIRROR"
    ;;
esac

# Use post-release updates?
export UPDATES=1

case $DIST in
  lucid)
    #export PROPOSED=1
    ;;
esac

# Sparc only : bootdir (location of cd.b and second.b)
# export BOOTDIR=/boot

# Symlink farmers should uncomment this line :
# export SYMLINK=1

# Use this to force copying the files instead of symlinking or hardlinking
# them. This is useful if your destination directories are on a different
# partition than your source files.
# export COPYLINK=1

# Options
# export MKISOFS=/usr/bin/mkisofs
# export MKISOFS_OPTS="-r"		#For normal users
# export MKISOFS_OPTS="-r -F ."	#For symlink farmers

# Override for i386 and amd64 to use xorriso instead of
# mkisofs/genisoimage. Allows creation of isohybrid images: ISO images
# that will burn correctly onto a CD and also can be written raw to a
# USB stick. xorriso 0.6.5 and later has working support for this.
case $DIST in
  warty|hoary|breezy|dapper|edgy|feisty|gutsy|hardy|intrepid|jaunty|karmic|lucid|maverick|natty)
    ;;
  *)
    export i386_MKISOFS="xorriso"
    export i386_MKISOFS_OPTS="-as mkisofs -r -checksum_algorithm_iso md5,sha1"
    export amd64_MKISOFS="xorriso"
    export amd64_MKISOFS_OPTS="-as mkisofs -r -checksum_algorithm_iso md5,sha1"
    ;;
esac

# ISOLinux support for multiboot on CD1 for i386
export ISOLINUX=1

# uncomment this to if you want to see more of what the Makefile is doing
#export VERBOSE_MAKE=1

# uncoment this to make build_all.sh try to build a simple CD image if
# the proper official CD run does not work
#ATTEMPT_FALLBACK=yes

# Set your disk size here in MB. Used in calculating package and
# source file layouts in build.sh and build_all.sh. Defaults are for
# CD-R, try ~4600 for DVD-R.
if [ "$CDIMAGE_DVD" = 1 ]; then
  export DEFBINSIZE=4600
  export DEFSRCSIZE=4600
else
  #export DEFBINSIZE=700
  #export DEFSRCSIZE=645
  export DEFBINSIZE=4600
  export DEFSRCSIZE=4600
fi

# We don't want certain packages to take up space on CD1...
#export EXCLUDE="$BASEDIR"/tasks/exclude-sarge
# ...but they are okay for other CDs (UNEXCLUDEx == may be included on CD >= x)
#export UNEXCLUDE2="$BASEDIR"/tasks/unexclude-CD2-sarge
# Any packages listed in EXCLUDE but not in any UNEXCLUDE will be
# excluded completely.

# We also exclude some source packages
#export SRCEXCLUDE="$BASEDIR"/tasks/exclude-src-potato

export NODEPENDS=1

# Set this if the recommended packages should be skipped when adding 
# package on the CD.  The default is 'false'.
export NORECOMMENDS=1

# Set this if the suggested packages should be skipped when adding 
# package on the CD.  The default is 'true'.
export NOSUGGESTS=1

# Image format:
# vfat = Output an image in VFAT format (.img)
# iso  = Output an image in ISO 9660 format (.iso)
if [ -z "$IMAGE_FORMAT" ]; then
  export IMAGE_FORMAT=iso
fi

# Preinstalled Image Filesystem
# This is the expected filesystem that is downloaded from the livefs builders

if [ -z "$PREINSTALLED_IMAGE_FILESYSTEM" ]; then
  export PREINSTALLED_IMAGE_FILESYSTEM=ext3
fi

# Produce jigdo files:
# 0/unset = Don't do jigdo at all, produce only the full iso image.
# 1 = Produce both the iso image and jigdo stuff.
# 2 = Produce ONLY jigdo stuff; no iso image is created (saves lots
#     of disk space).

if [ "$CDIMAGE_INSTALL" != 1 ] && [ "$CDIMAGE_ONLYSOURCE" != 1 ]; then
  # inappropriate
  export DOJIGDO=0
elif [ "$DIST" = warty ]; then
  # only custom builds now
  export DOJIGDO=0
elif [ "$SPECIAL" = 1 ]; then
  # special custom build
  export DOJIGDO=0
else
  export DOJIGDO=1
fi
# HTTP/FTP URL for directory where you intend to make the templates
# available. You should not need to change this; the default value ""
# means "template in same dir as the .jigdo file", which is usually
# correct. If it is non-empty, it needs a trailing slash. "%ARCH%"
# will be substituted by the current architecture.
#export JIGDOTEMPLATEURL=""
#
# Name of a directory on disc to create data for a fallback server in. 
# Should later be made available by you at the URL given in
# JIGDOFALLBACKURLS. In the directory, two subdirs named "Debian" and
# "Non-US" will be created, and filled with hard links to the actual
# files in your FTP archive. Because of the hard links, the dir must
# be on the same partition as the FTP archive! If unset, no fallback
# data is created, which may cause problems - see README.
#export JIGDOFALLBACKPATH="$(OUT)/snapshot/"
#
# Space-separated list of label->URL mappings for "jigdo fallback
# server(s)" to add to .jigdo file. If unset, no fallback URL is
# added, which may cause problems - see README.
export JIGDOFALLBACKURLS="Debian=http://archive.ubuntu.com/ubuntu/"
# commented out until the snapshot archives actually exist to avoid
# silly server load
#export JIGDOFALLBACKURLS="Debian=http://archive.ubuntu.com/cdimage/jigit/$CODENAME/snapshot/"
#
# Space-separated list of "include URLs" to add to the .jigdo file. 
# The included files are used to provide an up-to-date list of Debian
# mirrors to the jigdo _GUI_application_ (_jigdo-lite_ doesn't support
# "[Include ...]").
#export JIGDOINCLUDEURLS="http://cdimage.debian.org/debian-cd/debian-servers.jigdo"
#
# $JIGDOTEMPLATEURL and $JIGDOINCLUDEURLS are passed to
# "tools/jigdo_header", which is used by default to generate the
# [Image] and [Servers] sections of the .jigdo file. You can provide
# your own script if you need the .jigdo file to contain different
# data.
#export JIGDOSCRIPT="myscript"

# If set, use the md5sums from the main archive, rather than calculating
# them locally
export FASTSUMS=1

# A couple of things used only by publish_cds, so it can tweak the
# jigdo files, and knows where to put the results.
# You need to run publish_cds manually, it is not run by the Makefile.
export PUBLISH_URL="http://cdimage.debian.org/jigdo-area"
export PUBLISH_NONUS_URL="http://non-US.cdimage.debian.org/jigdo-area"
export PUBLISH_PATH="/home/jigdo-area/"

# Specify files and directories to *exclude* from jigdo processing. These
# files on each CD are expected to be different to those on the mirror, or
# are often subject to change. Any files matching entries in this list will
# simply be placed straight into the template file.
export JIGDO_EXCLUDE="'README*' /doc/ /md5sum.txt /.disk/ /pics/ 'Release*' 'Packages*' 'Sources*' 'Contents*'"

# Specify files and directories to *exclude* from jigdo processing. These
# files on each CD are expected to be different to those on the mirror, or
# are often subject to change. Any files matching entries in this list will
# simply be placed straight into the template file.
export JIGDO_INCLUDE="/pool/"

# Specify the minimum file size to consider for jigdo processing. Any files
# smaller than this will simply be placed straight into the template file.
export JIGDO_OPTS="-jigdo-min-file-size 1024"

for EXCL in $JIGDO_EXCLUDE
do
    JIGDO_OPTS="$JIGDO_OPTS -jigdo-exclude $EXCL"
done

for INCL in $JIGDO_INCLUDE
do
    JIGDO_OPTS="$JIGDO_OPTS -jigdo-force-md5 $INCL"
done

# Where to find the boot disks
#export BOOTDISKS=$TOPDIR/ftp/skolelinux/boot-floppies

# File with list of packages to include when fetching modules for the
# first stage installer (debian-installer). One package per line.
# Lines starting with '#' are comments.  The package order is
# important, as the packages will be installed in the given order.
#export UDEB_INCLUDE="$BASEDIR"/data/$CODENAME/udeb_include

# File with list of packages to exclude as above.
#export UDEB_EXCLUDE="$BASEDIR"/data/$CODENAME/udeb_exclude

# File with list of packages to include when running debootstrap from
# the first stage installer (currently only supported in
# debian-installer). One package per line.  Lines starting with '#'
# are comments.  The package order is important, as the packages will
# be installed in the given order.
#export BASE_INCLUDE="$BASEDIR"/data/$CODENAME/base_include

# File with list of packages to exclude as above.
#export BASE_EXCLUDE="$BASEDIR"/data/$CODENAME/base_exclude

# Only put the installer onto the cd (set NORECOMMENDS,... as well).
# INSTALLER_CD=0: nothing special (default)
# INSTALLER_CD=1: just add debian-installer (use TASK=tasks/debian-installer-$CODENAME)
# INSTALLER_CD=2: add d-i and base (use TASK=tasks/debian-installer+kernel-$CODENAME)
#export INSTALLER_CD=0

# Parameters to pass to kernel when the CD boots. Not currently supported
# for all architectures.
#export KERNEL_PARAMS="priority=critical"

# If set, limits the number of binary CDs to produce.
if [ "$CDIMAGE_DVD" = 1 ]; then
	export MAXCDS=1
else
	case $PROJECT in
		edubuntu)
			case $DIST in
				warty|hoary|breezy|dapper|edgy)
					export MAXCDS=1
					;;
				*)
					export MAXCDS=2
					;;
			esac
			;;
		*)
			export MAXCDS=1
			;;
	esac
fi

# If set to 0, never overflow binary CDs (for when you only want a single CD
# and want to know when it overflows).
export OVERFLOWBINCDS=0

# If set, overrides the boot picture used.
if [ -z "$SPLASHRLE" ]; then
	export SPLASHRLE="$BASEDIR/data/$DI_CODENAME/splash.rle"
fi
if [ -z "$GFXSPLASH" ]; then
	export GFXSPLASH="$BASEDIR/data/$DI_CODENAME/splash.pcx"
fi
if [ -z "$SPLASHPNG" ]; then
	export SPLASHPNG="$BASEDIR/data/$DI_CODENAME/splash.png"
fi

# Used by build.sh to determine what to build, this is the name of a target
# in the Makefile. Use bin-official_images to build only binary CDs. The
# default, official_images, builds everything.
IMAGETARGET=bin-official_images

# Set to 1 to save space by omitting the installation manual. 
# If so the README will link to the manual on the web site.
#export OMIT_MANUAL=1

# Set to 1 to save space by omitting the release notes
# If so we will link to them on the web site.
export OMIT_RELEASE_NOTES=0

# Set this to override the defaul location
#export RELEASE_NOTES_LOCATION="http://www.debian.org/releases/$CODENAME"

COMPLETE=0
