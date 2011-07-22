#!/bin/bash

# Install files in /install and some in /doc
set -e

# The location of the tree for CD#1, passed in
DIR=$1

if [ "$CDIMAGE_INSTALL_BASE" = 1 ]; then
    DOCDIR=doc

    if [ -n "$BOOTDISKS" -a -e $BOOTDISKS/current/$DOCDIR ] ; then
            DOCS=$BOOTDISKS/current/$DOCDIR
    elif MANUALDEB="$($BASEDIR/tools/apt-selection cache show "installation-guide-$ARCH")"; then
            MANUALDEB="$(echo "$MANUALDEB" | grep ^Filename | awk '{print $2}')"
    else
            echo "WARNING: Using $DI_CODENAME bootdisk documentation"
            DOCS=$MIRROR/dists/$DI_CODENAME/main/installer-$ARCH/current/$DOCDIR
    fi

    # Put the install documentation in /doc/install
    if [ "$DOCS" ] && [ -d "$DOCS" ]; then
        cd $DOCS
        mkdir -p $DIR/$DOCDIR/install
        if ! cp -a * $DIR/$DOCDIR/install; then
            echo "ERROR: Unable to copy installer documentation to CD."
        fi
    elif [ "$MANUALDEB" ]; then
        mkdir -p "$DIR/$DOCDIR/install/tmp" "$DIR/$DOCDIR/install/manual"
        ar p "$MIRROR/$MANUALDEB" data.tar.gz | tar xzf - -C "$DIR/$DOCDIR/install/tmp"
        mv "$DIR/$DOCDIR/install/tmp/usr/share/doc/installation-guide-$ARCH"/* "$DIR/$DOCDIR/install/manual/"
        rm -rf "$DIR/$DOCDIR/install/tmp"
        # just keep the HTML version
        rm -f "$DIR/$DOCDIR/install/manual/copyright" \
            "$DIR/$DOCDIR/install/manual/changelog.gz" \
            "$DIR/$DOCDIR/install/manual"/*/install.*.pdf* \
            "$DIR/$DOCDIR/install/manual"/*/install.*.txt*
    else
        echo "ERROR: Unable to copy installer documentation to CD."
    fi
fi

# Preseed files for special install types
mkdir -p $DIR/preseed
# TODO: odd path?
if [ -d $BASEDIR/data/$CODENAME/preseed/$PROJECT ]; then
    PRESEED_ROOT=$BASEDIR/data/$CODENAME/preseed/$PROJECT
else
    PRESEED_ROOT=$BASEDIR/data/$CODENAME/preseed
fi
for file in $PRESEED_ROOT/*.seed; do
    cp -a "$file" $DIR/preseed/
done
if [ -d $PRESEED_ROOT/$ARCH ]; then
    for file in $PRESEED_ROOT/$ARCH/*.seed; do
        cp -a "$file" $DIR/preseed/
    done
fi
