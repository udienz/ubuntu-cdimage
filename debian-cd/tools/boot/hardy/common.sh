
# This file provides some common code that is intented to be called
# by the various boot-<arch> scripts.


# install_languages decompacts the language packs, you should give the path
# to the CD temporary tree.
# This function should be called for all bootable images.
install_languages() {
    # Param $1 is the CD directory
    if [ -f "$MIRROR/dists/$DI_CODENAME/main/disks-$ARCH/current/xlp.tgz" ]
    then
	mkdir $1/.xlp
	(cd $1/.xlp; \
	tar zxf $MIRROR/dists/$DI_CODENAME/main/disks-$ARCH/current/xlp.tgz )
    fi
}

default_preseed() {
    case $PROJECT in
	ubuntu)
	    DEFAULT_PRESEED='file=/cdrom/preseed/ubuntu.seed'
	    ;;
	kubuntu)
	    DEFAULT_PRESEED='file=/cdrom/preseed/kubuntu.seed'
	    ;;
	kubuntu-kde4)
	    DEFAULT_PRESEED='file=/cdrom/preseed/kubuntu-kde4.seed'
	    ;;
	edubuntu)
	    DEFAULT_PRESEED='file=/cdrom/preseed/edubuntu.seed'
	    ;;
	xubuntu)
	    DEFAULT_PRESEED='file=/cdrom/preseed/xubuntu.seed'
	    ;;
	gobuntu)
	    DEFAULT_PRESEED='file=/cdrom/preseed/gobuntu.seed'
	    ;;
	ubuntu-server)
	    DEFAULT_PRESEED='file=/cdrom/preseed/ubuntu-server.seed'
	    ;;
	jeos)
	    DEFAULT_PRESEED='file=/cdrom/preseed/jeos.seed'
	    ;;
	ubuntustudio)
	    DEFAULT_PRESEED='file=/cdrom/preseed/ubuntustudio.seed'
	    ;;
	mythbuntu)
	    DEFAULT_PRESEED='file=/cdrom/preseed/mythbuntu.seed'
	    ;;
	*)
	    DEFAULT_PRESEED=
	    ;;
    esac
}

HUMANPROJECT="$(echo "$CAPPROJECT" | sed 's/-/ /g')"

