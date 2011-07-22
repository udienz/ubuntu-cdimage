#!/bin/bash

# Install files in /install and some in /doc
set -e

# The location of the tree for CD#1, passed in
DIR=$1

DOCDIR=doc

if [ -n "$BOOTDISKS" -a -e $BOOTDISKS/current/$DOCDIR ] ; then
        DOCS=$BOOTDISKS/current/$DOCDIR
else
        echo "WARNING: Using $DI_CODENAME bootdisk documentation"
        DOCS=$MIRROR/dists/$DI_CODENAME/main/installer-$ARCH/current/$DOCDIR
fi

# Put the install documentation in /doc/install
if [ ! -d $DOCS ]; then
    echo "ERROR: Unable to copy installer documentation to CD."
    exit
fi
cd $DOCS
mkdir -p $DIR/$DOCDIR/install
if ! cp -a * $DIR/$DOCDIR/install; then
    echo "ERROR: Unable to copy installer documentation to CD."
fi

# Preseed files for special install types
mkdir -p $DIR/preseed
for file in $BASEDIR/data/$CODENAME/preseed/*.seed; do
    cp -a "$file" $DIR/preseed/
done
# TODO: odd path?
if [ -d $BASEDIR/data/$CODENAME/preseed/$PROJECT ]; then
    for file in $BASEDIR/data/$CODENAME/preseed/$PROJECT/*.seed; do
        cp -a "$file" $DIR/preseed/
    done
fi
