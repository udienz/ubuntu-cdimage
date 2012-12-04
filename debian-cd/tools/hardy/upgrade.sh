#!/bin/sh
set -e

# Include dist-upgrader dir when available

DIR="$1/CD1"
SOURCEDIR="$MIRROR/dists/$CODENAME/main/dist-upgrader-all/current"
TARGETDIR="$DIR/dists/$CODENAME/main/dist-upgrader/binary-all"

if ls "$SOURCEDIR/$CODENAME"* >/dev/null 2>&1; then
    mkdir -p "$TARGETDIR"
    # copy upgrade tarball + signature
    cp -a "$SOURCEDIR/$CODENAME"* "$TARGETDIR"
    # extract the cdromupgrade script from the archive and put it
    # onto the top-level of the CD
    tar -C "$DIR" -x -z -f "$TARGETDIR/$CODENAME.tar.gz" ./cdromupgrade
fi

# now check if any prerequisites need to go onto the CD
PACKAGESGZ="$MIRROR/dists/$PREV_CODENAME-backports/main/debian-installer/binary-$ARCH/Packages.gz"
ARCH_TARGETDIR="$DIR/dists/$CODENAME/main/dist-upgrader/binary-$ARCH"
mkdir -p "$ARCH_TARGETDIR"
for pkg in $(zcat "$PACKAGESGZ" | grep-dctrl -PrnsFilename ^release-upgrader-); do
    echo "Adding: $pkg"
    cp -a "$MIRROR/$pkg" "$ARCH_TARGETDIR"
done

exit 0
