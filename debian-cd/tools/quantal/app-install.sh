#! /bin/sh

set -e

N="$1"
# The location of the tree where we should install app-install data files
DIR="$2"

if [ "$PROJECT" = edubuntu ]; then
    EDU_APP_INSTALL_DATA_DEB="$($BASEDIR/tools/apt-selection cache \
				show app-install-data-edubuntu | \
				grep ^Filename: | awk '{print $2}' || true)"

    [ "$EDU_APP_INSTALL_DATA_DEB" ] || exit 0

    mkdir -p "$DIR/app-install/edubuntu/"
    TMP_EDU="$DIR/app-install/edubuntu/"

    dpkg -x "$MIRROR/$EDU_APP_INSTALL_DATA_DEB" "$TMP_EDU"
fi

APP_INSTALL_DATA_DEB="$($BASEDIR/tools/apt-selection cache \
			show app-install-data | \
			grep ^Filename: | awk '{print $2}' || true)"
[ "$APP_INSTALL_DATA_DEB" ] || exit 0

mkdir -p "$DIR/app-install/channels" "$DIR/app-install/desktop" \
	 "$DIR/app-install/icons" "$DIR/app-install/tmp"
TMP="$DIR/app-install/tmp"
dpkg -x "$MIRROR/$APP_INSTALL_DATA_DEB" "$TMP"

find "$TMP/usr/share/app-install/desktop" \
    -name \*.desktop -print0 | \
    xargs -r0 grep -aHi '^X-AppInstall-Package=' | \
    perl -pe "s,^$TMP/usr/share/app-install/desktop/,,; s/\.desktop:.*?=/ /" | \
    sort -k2 > "$TMP/desktop-list"
DESKTOPS="$(sort "$DIR/../$N.packages" | \
	    join -1 2 -o 1.1 "$TMP/desktop-list" -)"

for name in $DESKTOPS; do
    desktop="$TMP/usr/share/app-install/desktop/$name.desktop"
    cp -a "$desktop" "$DIR/app-install/desktop/"
    icon="$(grep -ai '^Icon=' "$desktop" | head -n1 | cut -d= -f2)"
    if [ "$icon" ]; then
	if [ "${icon%.*}" = "$icon" ]; then
	    cp -a "$TMP/usr/share/app-install/icons/$icon".* \
		"$DIR/app-install/icons/" || true
	else
	    cp -a "$TMP/usr/share/app-install/icons/$icon" \
		"$DIR/app-install/icons/" || true
	fi
    fi
done

if [ "$PROJECT" = edubuntu ]; then
    find "$TMP_EDU/usr/share/app-install-data-edubuntu/desktop/" -type f -print0 | \
	xargs -0r cp --target-directory "$DIR/app-install/desktop" || true
    find "$TMP_EDU/usr/share/app-install-data-edubuntu/icons/" -type f -print0 | \
	xargs -0r cp --target-directory "$DIR/app-install/icons" || true
    rm -rf "$DIR/app-install/edubuntu"
else
    cp -a "$TMP/usr/share/app-install/desktop/applications.menu" \
	"$DIR/app-install/desktop/" || true
fi

rm -rf "$DIR/app-install/tmp"

mkdir -p "$DIR/.disk"
echo '/app-install' > "$DIR/.disk/add-on"

exit 0
