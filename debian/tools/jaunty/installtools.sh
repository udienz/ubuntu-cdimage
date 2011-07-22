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
PRESEED_ROOT=$BASEDIR/data/$CODENAME/preseed
for preseed_dir in \
        $PRESEED_ROOT $PRESEED_ROOT/$ARCH \
        $PRESEED_ROOT/$PROJECT $PRESEED_ROOT/$PROJECT/$ARCH; do
    [ -d "$preseed_dir" ] || continue
    for file in $preseed_dir/*.seed; do
        cp -a "$file" $DIR/preseed/
    done
done
if [ "$CDIMAGE_DVD" = 1 ] && [ "$PROJECT" != ubuntu-server ]; then
    # include server on normal DVDs
    for preseed_dir in \
            $PRESEED_ROOT/ubuntu-server $PRESEED_ROOT/ubuntu-server/$ARCH; do
        [ -d "$preseed_dir" ] || continue
        for file in $preseed_dir/*.seed; do
            cp -a "$file" $DIR/preseed/
        done
    done
    # we normally preseed tasksel to install the desktop task, but this is
    # inappropriate on DVDs where much more choice is available
    if [ -e "$DIR/preseed/$PROJECT.seed" ]; then
        perl -ni -e '
            if (/^#/) { $out .= $_ }
            elsif (m[^tasksel\s+tasksel/first\s]) { print $out; print; print "tasksel\ttasksel/first\tseen false\n"; $out = "" }
            else { print $out; print; $out = "" }' \
                "$DIR/preseed/$PROJECT.seed"
        if [ ! -s "$DIR/preseed/$PROJECT.seed" ]; then
            rm -f "$DIR/preseed/$PROJECT.seed"
        fi
    fi
fi
