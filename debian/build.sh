#!/bin/sh -e

# Script to build one arch

if [ -z "$CF" ] ; then
    CF=./CONF.sh
fi
. $CF

if [ -z "$COMPLETE" ] ; then
    export COMPLETE=1
fi

if [ -n "$1" ] ; then
    FULLARCH="$1"
    export ARCH="${FULLARCH%%+*}"
    if [ "$ARCH" = "$FULLARCH" ]; then
        export SUBARCH=
    else
        export SUBARCH="${FULLARCH#*+}"
    fi
fi

make distclean
make ${CODENAME}_status
if [ "$SKIPMIRRORCHECK" = "yes" ]; then
    echo " ... WARNING: skipping mirror check"
else
    echo " ... checking your mirror"
    make mirrorcheck-binary
    make mirrorcheck-source
    if [ $? -gt 0 ]; then
	    echo "ERROR: Your mirror has a problem, please correct it." >&2
	    exit 1
    fi
fi
echo " ... selecting packages to include"
if [ -e ${MIRROR}/dists/${DI_CODENAME}/main/disks-${ARCH}/current/. ] ; then
	disks=`du -sm ${MIRROR}/dists/${DI_CODENAME}/main/disks-${ARCH}/current/. | \
        	awk '{print $1}'`
else
	disks=0
fi
if [ -f $BASEDIR/tools/boot/$DI_CODENAME/boot-$FULLARCH.calc ]; then
    . $BASEDIR/tools/boot/$DI_CODENAME/boot-$FULLARCH.calc
fi
SIZE_ARGS=''
for CD in 1; do
	size=`eval echo '$'"BOOT_SIZE_${CD}"`
	[ "$size" = "" ] && size=0
	[ $CD = "1" ] && size=$(($size + $disks))
	mult=`eval echo '$'"SIZE_MULT_${CD}"`
	[ "$mult" = "" ] && mult=100
    FULL_SIZE=`echo "($DEFBINSIZE - $size) * 1024 * 1024" | bc`
	echo "INFO: Reserving $size MB on CD $CD for boot files.  SIZELIMIT=$FULL_SIZE."
    if [ $mult != 100 ]; then
        echo "  INFO: Reserving "$((100-$mult))"% of the CD for extra metadata"
        FULL_SIZE=`echo "$FULL_SIZE * $mult" / 100 | bc`
        echo "  INFO: SIZELIMIT now $FULL_SIZE."
    fi
	SIZE_ARGS="$SIZE_ARGS SIZELIMIT${CD}=$FULL_SIZE"
done

FULL_SIZE=`echo "($DEFSRCSIZE - $size) * 1024 * 1024" | bc`
make bin-list $SIZE_ARGS SRCSIZELIMIT=$FULL_SIZE
echo " ... building the images"
export OUT="$OUT/$FULLARCH"
mkdir -p "$OUT"
if [ -z "$IMAGETARGET" ] ; then
    IMAGETARGET="bin-official_images"
fi
make $IMAGETARGET $SIZE_ARGS SRCSIZELIMIT=$FULL_SIZE

make imagesums
make pi-makelist
