#!/usr/bin/perl
# debhelper sequence file for germinate

use warnings;
use strict;
use Debian::Debhelper::Dh_Lib;

insert_before("dh_installdeb", "dh_germinate_metapackage");
insert_before("dh_clean", "dh_germinate_clean");

1;
