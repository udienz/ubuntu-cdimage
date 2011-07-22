#! /bin/sh

mkemptydir () {
	rm -rf "$1"
	mkdir -p "$1"
}

confirm () {
	printf ' [yN] '
	read yesno
	yesno="$(printf %s "$yesno" | tr A-Z a-z)"
	case $yesno in
		y|yes)
			return 0
			;;
		*)
			return 1
			;;
	esac
}

get_notify_addresses () {
	[ -e "$CDIMAGE_ROOT/etc/notify-addresses" ] || return
	while read project addresses; do
		if [ "$project" = ALL ]; then
			echo "$addresses"
		elif [ "$project" = "$1" ]; then
			echo "$addresses"
		fi
	done < "$CDIMAGE_ROOT/etc/notify-addresses"
}

zsyncmake_wrapper () {
	if ! zsyncmake "$@"; then
		echo "Trying again with block size 2048 ..."
		zsyncmake -b 2048 "$@"
	fi
}

dist_lt () {
	case " $ALL_DISTS " in
		*" $DIST $1 "*|*" $DIST "*" $1 "*)
			return 0
			;;
		*)
			return 1
			;;
	esac
}

dist_le () {
	case $DIST in
		$1)	return 0 ;;
	esac
	dist_lt "$1"
}

dist_ge () {
	! dist_lt "$1"
}

dist_gt () {
	! dist_le "$1"
}
