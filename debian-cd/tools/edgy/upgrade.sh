#!/bin/sh
set -e

# for edgy
# Include dist-upgrader dir when available

DIR="$1/CD1"
SOURCEDIR="$MIRROR/dists/$CODENAME/main/dist-upgrader-all/current"
TARGETDIR="$DIR/dists/$CODENAME/main/dist-upgrader/binary-all"

if [ -d "$SOURCEDIR" ]; then
    mkdir -p "$TARGETDIR"
    # copy upgrade tarball + signature
    cp -a "$SOURCEDIR/$CODENAME"* "$TARGETDIR"
    # extract the cdromupgrade script from the archive and put it
    # onto the top-level of the CD
    tar -C "$DIR" -x -z -f "$TARGETDIR/$CODENAME.tar.gz" ./cdromupgrade
fi

exit 0
