#!/bin/sh
set -e

# Include dist-upgrader dir when available

DIR="$1/CD1"
TARGETDIR="$DIR/dists/$CODENAME/main/dist-upgrader/binary-all"

# Assume that -security is always pocket copied to -updates
UPGRADER_POCKETS="$CODENAME-updates $CODENAME"
if [ "${PROPOSED:-0}" != "0" ]; then
    UPGRADER_POCKETS="$CODENAME-proposed $UPGRADER_POCKETS"
fi

SOURCEDIR=""
for POCKET in $UPGRADER_POCKETS; do
    if [ -e "$MIRROR/dists/$POCKET/main/dist-upgrader-all/current/$CODENAME.tar.gz" ]; then
        SOURCEDIR="$MIRROR/dists/$POCKET/main/dist-upgrader-all/current"
        break
    fi
done

if [ -n "$SOURCEDIR" ]; then
    mkdir -p "$TARGETDIR"
    # copy upgrade tarball + signature
    cp -av "$SOURCEDIR/$CODENAME"* "$TARGETDIR"
    # extract the cdromupgrade script from the archive and put it
    # onto the top-level of the CD
    tar -C "$DIR" -x -z -f "$TARGETDIR/$CODENAME.tar.gz" ./cdromupgrade
fi

# now check if any prerequisites need to go onto the CD
PACKAGESGZ="$MIRROR/dists/$PREV_CODENAME-updates/main/binary-$ARCH/Packages.gz"
ARCH_TARGETDIR="$DIR/dists/$CODENAME/main/dist-upgrader/binary-$ARCH"
mkdir -p "$ARCH_TARGETDIR"
for pkg in $(zcat "$PACKAGESGZ" | grep-dctrl -PensFilename '^(release-upgrader-python-apt|libapt-inst1|libapt-pkg4)'); do
    echo "Adding: $pkg"
    cp -a "$MIRROR/$pkg" "$ARCH_TARGETDIR"
done

exit 0
