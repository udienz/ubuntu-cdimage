#!/usr/bin/make -f

# Main Makefile for YACS
#
# Copyright 1999 Raphaël Hertzog <hertzog@debian.org>
# See the README file for the license

# The environment variables must have been set
# before. For this you can source the CONF.sh 
# file in your shell


## DEFAULT VALUES
ifdef SUBARCH
export FULLARCH=$(ARCH)+$(SUBARCH)
else
export FULLARCH=$(ARCH)
endif
ifndef VERBOSE_MAKE
Q=@
endif
ifndef SIZELIMIT
export SIZELIMIT=$(shell echo -n $$[ 690 * 1024 * 1024 ])
endif
ifndef TASK
ifneq (,$(wildcard $(BASEDIR)/tasks/auto/$(IMAGE_TYPE)/$(PROJECT)/$(DIST)/MASTER))
TASK=$(BASEDIR)/tasks/auto/$(IMAGE_TYPE)/$(PROJECT)/$(DIST)/MASTER
else
TASK=$(BASEDIR)/tasks/$(CAPPROJECT)_$(CODENAME)
endif
endif
ifndef CAPCODENAME
CAPCODENAME:=$(shell perl -e "print ucfirst("$(CODENAME)")")
endif
ifndef BINDISKINFO
ifneq ($(MAXCDS),1)
export BINDISKINFO="$(CAPPROJECT) $(DEBVERSION) \"$(CAPCODENAME)\" - $(OFFICIAL) $(FULLARCH) Binary-$$num ($$DATE)"
else
export BINDISKINFO="$(CAPPROJECT) $(DEBVERSION) \"$(CAPCODENAME)\" - $(OFFICIAL) $(FULLARCH) ($$DATE)"
endif
endif
ifndef SRCDISKINFO
export SRCDISKINFO="$(CAPPROJECT) $(DEBVERSION) \"$(CAPCODENAME)\" - $(OFFICIAL) Source-$$num ($$DATE)"
endif
# ND=No-Date versions for README
ifndef BINDISKINFOND
ifneq ($(MAXCDS),1)
export BINDISKINFOND="$(CAPPROJECT) $(DEBVERSION) \"$(CAPCODENAME)\" - $(OFFICIAL) $(FULLARCH) Binary-$$num"
else
export BINDISKINFOND="$(CAPPROJECT) $(DEBVERSION) \"$(CAPCODENAME)\" - $(OFFICIAL) $(FULLARCH)"
endif
endif
ifndef SRCDISKINFOND
export SRCDISKINFOND="$(CAPPROJECT) $(DEBVERSION) \"$(CAPCODENAME)\" - $(OFFICIAL) Source-$$num"
endif
ifndef BINVOLID
ifeq ($(ARCH),powerpc)
ifneq ($(MAXCDS),1)
BINVOLID="$(CAPPROJECT) $(DEBVERSION) ppc $$num"
else
BINVOLID="$(CAPPROJECT) $(DEBVERSION) ppc"
endif
else
ifneq ($(MAXCDS),1)
BINVOLID="$(CAPPROJECT) $(DEBVERSION) $(ARCH) $$num"
else
BINVOLID="$(CAPPROJECT) $(DEBVERSION) $(ARCH)"
endif
endif
endif
ifndef SRCVOLID
SRCVOLID="$(CAPPROJECT) $(DEBVERSION) Source $$num"
endif
ifndef MKISOFS
export MKISOFS=/usr/bin/mkisofs
endif
ifndef MKISOFS_OPTS
#For normal users
MKISOFS_OPTS=-r
#For symlink farmers
#MKISOFS_OPTS=-r -F .
endif
ifndef HOOK
HOOK=$(BASEDIR)/tools/$(CODENAME).hook
endif
ifneq "$(wildcard $(MIRROR)/dists/$(DI_CODENAME)/main/disks-$(ARCH))" ""
ifndef BOOTDISKS
export BOOTDISKS=$(MIRROR)/dists/$(DI_CODENAME)/main/disks-$(ARCH)
endif
endif
ifndef DOJIGDO
export DOJIGDO=0
endif

ifndef UDEB_INCLUDE
# Netinst/businesscard CD have different udeb_include files
ifeq ($(INSTALLER_CD),1)
UDEB_INCLUDE=$(BASEDIR)/data/$(DI_CODENAME)/$(ARCH)_businesscard_udeb_include
endif
ifeq ($(INSTALLER_CD),2)
UDEB_INCLUDE=$(BASEDIR)/data/$(DI_CODENAME)/$(ARCH)_netinst_udeb_include
endif
endif
# Default udeb_include files.
ifndef UDEB_INCLUDE
UDEB_INCLUDE=$(BASEDIR)/data/$(DI_CODENAME)/$(ARCH)_udeb_include
endif

ARCH_MKISOFS = ${${ARCH}_MKISOFS}
ARCH_MKISOFS_OPTS = ${${ARCH}_MKISOFS_OPTS}
ifneq (${ARCH_MKISOFS},)
    MKISOFS = ${ARCH_MKISOFS}
endif
ifneq (${ARCH_MKISOFS_OPTS},)
    MKISOFS_OPTS = ${ARCH_MKISOFS_OPTS}
endif

## Internal variables  
apt=$(BASEDIR)/tools/apt-selection
list2cds=$(BASEDIR)/tools/list2cds
list2src=$(BASEDIR)/tools/list2src
cds2src=$(BASEDIR)/tools/cds2src
master2tasks=$(BASEDIR)/tools/master2tasks
mirrorcheck=$(BASEDIR)/tools/mirror_check
add_packages=$(BASEDIR)/tools/add_packages
add_dirs=$(BASEDIR)/tools/add_dirs
add_bin_doc=$(BASEDIR)/tools/add-bin-doc
scanpackages=$(BASEDIR)/tools/scanpackages
scansources=$(BASEDIR)/tools/scansources
add_files=$(BASEDIR)/tools/add_files
set_mkisofs_opts=$(BASEDIR)/tools/set_mkisofs_opts
strip_nonus_bin=$(BASEDIR)/tools/strip-nonUS-bin
add_secured=$(BASEDIR)/tools/add_secured
md5sum=/usr/bin/md5sum
sha1sum=/usr/bin/sha1sum
fastsums=$(BASEDIR)/tools/fast_sums
jigdo_cleanup=$(BASEDIR)/tools/jigdo_cleanup
grab_md5=$(BASEDIR)/tools/grab_md5
add_live_filesystem=$(BASEDIR)/tools/add_live_filesystem
add_winfoss=$(BASEDIR)/tools/add_winfoss
find_newest_installer=$(BASEDIR)/tools/find-newest-installer
verbose=$(BASEDIR)/tools/verbose_command
make_vfat_img=$(BASEDIR)/tools/make-vfat-img
hardlink=$(BASEDIR)/tools/hardlink

BDIR=$(TDIR)/$(CODENAME)-$(FULLARCH)
ADIR=$(APTTMP)/$(CODENAME)-$(FULLARCH)
SDIR=$(TDIR)/$(CODENAME)-src

FIRSTDISKS=CD1 
ifdef FORCENONUSONCD1
FIRSTDISKS=CD1 CD1_NONUS
forcenonusoncd1=1
else
forcenonusoncd1=0
endif

# we don't know how to generate ISOs for armel/iMX51; force vfat images
ifeq ($(ARCH),armel)
IMAGE_FORMAT := vfat
endif

# CDBASE = $(CODENAME)-$(FULLARCH)-$(1)
ifeq ($(CDIMAGE_DVD),1)
CDBASE = $(CODENAME)-dvd-$(FULLARCH)
else
 ifeq ($(CDIMAGE_PREINSTALLED),1)
  ifeq ($(PROJECT),ubuntu-netbook)
   CDBASE = $(CODENAME)-preinstalled-netbook-$(FULLARCH)
  else
   ifeq ($(PROJECT),ubuntu-headless)
    CDBASE = $(CODENAME)-preinstalled-headless-$(FULLARCH)
   else
    ifeq ($(PROJECT),ubuntu-server)
     CDBASE = $(CODENAME)-preinstalled-server-$(FULLARCH)
    else
     ifeq ($(PROJECT),kubuntu-mobile)
      CDBASE = $(CODENAME)-preinstalled-mobile-$(FULLARCH)
     else
      CDBASE = $(CODENAME)-preinstalled-desktop-$(FULLARCH)
     endif
    endif
   endif
  endif
 else 
 ifeq ($(CDIMAGE_ADDON),1)
  CDBASE = $(CODENAME)-addon-$(FULLARCH)
 else
  ifeq ($(CDIMAGE_INSTALL),1)
   ifeq ($(PROJECT),edubuntu)
    ifneq (,$(findstring $(CODENAME),warty hoary breezy dapper edgy))
 CDBASE = $(CODENAME)-install-$(FULLARCH)
    else
 CDBASE = $(CODENAME)-$$(if test "$(1)" = 1; then echo server; else echo serveraddon; fi)-$(FULLARCH)
    endif
   else
    ifneq (,$(findstring $(CODENAME),warty hoary breezy))
 CDBASE = $(CODENAME)-install-$(FULLARCH)
    else
     ifeq ($(PROJECT),ubuntu-server)
 CDBASE = $(CODENAME)-server-$(FULLARCH)
     else
      ifeq ($(PROJECT),jeos)
 CDBASE = $(CODENAME)-jeos-$(FULLARCH)
      else
 CDBASE = $(CODENAME)-alternate-$(FULLARCH)
      endif
     endif
    endif
   endif
  else
   ifeq ($(PROJECT),edubuntu)
    ifneq (,$(findstring $(CODENAME),warty hoary breezy dapper edgy))
 CDBASE = $(CODENAME)-live-$(FULLARCH)
    else
 CDBASE = $(CODENAME)-desktop-$(FULLARCH)
    endif
   else
    ifneq (,$(findstring $(CODENAME),warty hoary breezy))
 CDBASE = $(CODENAME)-live-$(FULLARCH)
    else
     ifeq ($(PROJECT),ubuntu-server)
 CDBASE = $(CODENAME)-live-$(FULLARCH)
     else
      ifeq ($(PROJECT),ubuntu-mid)
 CDBASE = $(CODENAME)-mid-$(FULLARCH)
      else
       ifeq ($(PROJECT),ubuntu-netbook)
 CDBASE = $(CODENAME)-netbook-$(FULLARCH)
       else
        ifeq ($(PROJECT),kubuntu-netbook)
 CDBASE = $(CODENAME)-netbook-$(FULLARCH)
        else
         ifeq ($(PROJECT),ubuntu-moblin-remix)
 CDBASE = $(CODENAME)-moblin-remix-$(FULLARCH)
         else
          ifeq ($(PROJECT),kubuntu-mobile)
 CDBASE = $(CODENAME)-mobile-$(FULLARCH)
          else
 CDBASE = $(CODENAME)-desktop-$(FULLARCH)
          endif
         endif
        endif
       endif
      endif
     endif
    endif
   endif
  endif
 endif
endif
endif
CDSRCBASE = $(CODENAME)-src-$(1)

INSTALLER_TYPE := $(shell $(find_newest_installer))
INSTALLER_VERSION := $(shell readlink $(MIRROR)/dists/$(CODENAME)/main/$(INSTALLER_TYPE)-$(ARCH)/current)

## DEBUG STUFF ##

PrintVars:
	@num=1; \
	DATE=$${CDIMAGE_DATE:-`date +%Y%m%d`} ; \
	echo BINDISKINFO: ; \
        echo $(BINDISKINFO) ; \
	echo SRCDISKINFO: ; \
        echo $(SRCDISKINFO) ; \
	echo BINDISKINFOND: ; \
        echo $(BINDISKINFOND) ; \
	echo SRCDISKINFOND: ; \
        echo $(SRCDISKINFOND) ; \
	echo BINVOLID: ; \
        echo $(BINVOLID) ; \
	echo SRCVOLID: ; \
        echo $(SRCVOLID) ; \

default:
	@echo "Please refer to the README file for more information"
	@echo "about the different targets available."

## CHECKS ##

# Basic checks in order to avoid problems
ok:
ifndef TDIR
	@echo TDIR undefined -- set up CONF.sh; false
endif
ifndef BASEDIR
	@echo BASEDIR undefined -- set up CONF.sh; false
endif
ifndef MIRROR
	@echo MIRROR undefined -- set up CONF.sh; false
endif
ifndef ARCH
	@echo ARCH undefined -- set up CONF.sh; false
endif
ifndef CODENAME
	@echo CODENAME undefined -- set up CONF.sh; false
endif
ifndef OUT
	@echo OUT undefined -- set up CONF.sh; false
endif
ifdef NONFREE
ifdef EXTRANONFREE
	@echo Never use NONFREE and EXTRANONFREE at the same time; false
endif
endif
ifdef FORCENONUSONCD1
ifndef NONUS
	@echo If we have FORCENONUSONCD1 set, we must also have NONUS set; false
endif
endif

## INITIALIZATION ##

# Creation of the directories needed
init: ok $(OUT) $(TDIR) $(BDIR) $(SDIR) $(ADIR)
$(OUT):
	$(Q)mkdir -p $(OUT)
$(TDIR):
	$(Q)mkdir -p $(TDIR)
$(BDIR):
	$(Q)mkdir -p $(BDIR)
$(SDIR):
	$(Q)mkdir -p $(SDIR)
$(ADIR):
	$(Q)mkdir -p $(ADIR)
	$(Q)mkdir -p $(ADIR)/apt-ftparchive-db

## CLEANINGS ##

# Cleans the current arch tree (but not packages selection info)
clean: ok bin-clean src-clean
bin-clean:
	$(Q)rm -rf $(BDIR)/CD[1234567890]*
	$(Q)rm -rf $(BDIR)/*_NONUS
	$(Q)rm -f $(BDIR)/*.filelist*
	$(Q)rm -f  $(BDIR)/packages-stamp $(BDIR)/bootable-stamp \
	         $(BDIR)/upgrade-stamp $(BDIR)/secured-stamp $(BDIR)/md5-check
src-clean:
	$(Q)rm -rf $(SDIR)/CD[1234567890]*
	$(Q)rm -rf $(SDIR)/*_NONUS
	$(Q)rm -rf $(SDIR)/sources-stamp $(SDIR)/secured-stamp $(SDIR)/md5-check

# Completely cleans the current arch tree
realclean: distclean
distclean: ok bin-distclean src-distclean
bin-distclean:
	$(Q)echo "Cleaning the binary build directory"
	$(Q)rm -rf $(BDIR)
	$(Q)rm -rf $(ADIR)
src-distclean:
	$(Q)echo "Cleaning the source build directory"
	$(Q)rm -rf $(SDIR)

## STATUS and APT ##

# Regenerate the status file with only packages that
# are of priority standard or higher
status: init $(ADIR)/status
$(ADIR)/status:
	@echo "Generating a fake status file for apt-get and apt-cache..."
	:> $(ADIR)/status
	# Updating the apt database
	$(Q)$(apt) update
	#
	# Checking the consistence of the standard system
	# If this does fail, then launch make correctstatus
	#
	$(Q)$(apt) check || $(MAKE) correctstatus

# Only useful if the standard system is broken
# It tries to build a better status file with apt-get -f install
correctstatus: status apt-update
	# You may need to launch correctstatus more than one time
	# in order to correct all dependencies
	#
	# Removing packages from the system :
	$(Q)set -e; \
	for i in `$(apt) deselected -f install`; do \
		echo $$i; \
		perl -i -000 -ne "print unless /^Package: \Q$$i\E/m" \
		$(ADIR)/status; \
	done
	#
	# Adding packages to the system :
	$(Q)set -e; \
	for i in `$(apt) selected -f install`; do \
	  echo $$i; \
	  $(apt) cache dumpavail | perl -000 -ne \
	      "s/^(Package: .*)\$$/\$$1\nStatus: install ok installed/m; \
	       print if /^Package: \Q$$i\E\s*\$$/m;" \
	       >> $(ADIR)/status; \
	done
	#
	# Showing the output of apt-get check :
	$(Q)$(apt) check

apt-update: status
	@echo "Apt-get is updating his files ..."
	$(Q)$(apt) update


## GENERATING LISTS ##

# Deleting the list only
deletelist: ok
	$(Q)-rm $(BDIR)/rawlist
	$(Q)-rm $(BDIR)/rawlist-exclude
	$(Q)-rm $(BDIR)/list
	$(Q)-rm $(BDIR)/list.exclude

# Generates the list of packages/files to put on each CD
list: bin-list src-list

# Generate the listing of binary packages
bin-list: ok apt-update bin-genlist $(BDIR)/1.packages
$(BDIR)/1.packages:
	@echo "Dispatching the packages on all the CDs ..."
	$(Q)$(list2cds) $(BDIR)/list $(SIZELIMIT)
ifdef FORCENONUSONCD1
	$(Q)set -e; \
	 for file in $(BDIR)/*.packages; do \
	    newfile=$${file%%.packages}_NONUS.packages; \
	    cp $$file $$newfile; \
	    $(strip_nonus_bin) $$file $$file.tmp; \
	    if (cmp -s $$file $$file.tmp) ; then \
	        rm -f $$file.tmp $$newfile ; \
	    else \
	        echo Splitting non-US packages: $$file and $$newfile ; \
	        mv -f $$file.tmp $$file; \
	    fi ;\
	done
endif

# Generate the listing for sources CDs corresponding to the packages included
# in the binary set
src-list: ok apt-update src-genlist $(SDIR)/1.sources
$(SDIR)/1.sources:
	@echo "Dispatching the sources on all the CDs ..."
	$(Q)$(list2src) $(SDIR)/list $(SIZELIMIT)
ifdef FORCENONUSONCD1
	$(Q)set -e; \
	 for file in $(SDIR)/*.sources; do \
	    newfile=$${file%%.sources}_NONUS.sources; \
	    cp $$file $$newfile; \
	    grep -v non-US $$file >$$file.tmp; \
	    if (cmp -s $$file $$file.tmp) ; then \
	        rm -f $$file.tmp $$newfile ; \
	    else \
	        echo Splitting non-US sources: $$file and $$newfile ; \
	        mv -f $$file.tmp $$file; \
	    fi ;\
	done
endif

# Generate the complete listing of packages from the task
# Build a nice list without doubles and without spaces
bin-genlist: ok $(BDIR)/list $(BDIR)/list.exclude
$(BDIR)/list: $(BDIR)/rawlist
	@echo "Generating the complete list of packages to be included ..."
	$(Q)perl -ne 'chomp; next if /^\s*$$/; \
	          print "$$_\n" if not $$seen{$$_}; $$seen{$$_}++;' \
		  $(BDIR)/rawlist \
		  > $(BDIR)/list


$(BDIR)/list.exclude: $(BDIR)/rawlist-exclude
	@echo "Generating the complete list of packages to be removed ..."
	$(Q)perl -ne 'chomp; next if /^\s*$$/; \
	          print "$$_\n" if not $$seen{$$_}; $$seen{$$_}++;' \
		  $(BDIR)/rawlist-exclude \
		  > $(BDIR)/list.exclude

# Build the raw list (cpp output) with doubles and spaces
$(BDIR)/rawlist:
ifdef FORCENONUSONCD1
	$(Q)$(apt) cache dumpavail | \
		grep-dctrl -FSection -n -sPackage -e '^(non-US|non-us)' - | \
		sort | uniq > $(BDIR)/$(CAPPROJECT)_$(CODENAME)_nonUS
endif
	$(Q)if [ -x "/usr/sbin/debootstrap" -a _$(INSTALLER_CD) != _1 ]; then \
		mkdir -p $(DEBOOTSTRAP)/tmp-$(ARCH) ; \
		$(DEBOOTSTRAPROOT) /usr/sbin/debootstrap --arch $(ARCH) --print-debs $(CODENAME) $(DEBOOTSTRAP)/tmp-$(ARCH) file://$(MIRROR) $(DEBOOTSTRAP)/$(CODENAME)-$(FULLARCH) \
		| tr ' ' '\n' >>$(BDIR)/rawlist.debootstrap; \
	fi
	$(Q)perl -npe 's/\@ARCH\@/$(FULLARCH)/g' $(TASK) | \
	 cpp -nostdinc -nostdinc++ -P -undef -D ARCH=$(FULLARCH) -D ARCH_$(subst -,_,$(subst +,_,$(FULLARCH))) \
	     -U $(ARCH) -U i386 -U linux -U unix \
	     -DFORCENONUSONCD1=$(forcenonusoncd1) \
	     -I $(BASEDIR)/tasks/auto/$(IMAGE_TYPE) -I $(BASEDIR)/tasks -I $(BDIR) - - >> $(BDIR)/rawlist

# Build the raw list (cpp output) with doubles and spaces for excluded packages
$(BDIR)/rawlist-exclude:
	$(Q)if [ -n "$(EXCLUDE)" ]; then \
	 	perl -npe 's/\@ARCH\@/$(FULLARCH)/g' $(EXCLUDE) | \
			cpp -nostdinc -nostdinc++ -P -undef -D ARCH=$(FULLARCH) -D ARCH_$(subst -,_,$(subst +,_,$(FULLARCH))) \
				-U $(ARCH) -U i386 -U linux -U unix \
	     			-DFORCENONUSONCD1=$(forcenonusoncd1) \
	     			-I $(BASEDIR)/tasks/auto/$(IMAGE_TYPE) -I $(BASEDIR)/tasks -I $(BDIR) - - >> $(BDIR)/rawlist-exclude; \
	else \
		echo > $(BDIR)/rawlist-exclude; \
	fi

# Generate the complete listing of sources from the task
# Build a nice list without doubles and without spaces
# TODO: no exclude support; does it matter?
src-genlist: ok $(SDIR)/list
$(SDIR)/list: $(SDIR)/rawlist
	@echo "Generating the complete list of packages to be included ..."
	$(Q)perl -ne 'chomp; next if /^\s*$$/; \
	          print "$$_\n" if not $$seen{$$_}; $$seen{$$_}++;' \
		  $(SDIR)/rawlist \
		  > $(SDIR)/list

$(SDIR)/rawlist:
	$(Q)($(foreach arch,$(ARCHES), \
	perl -npe 's/\@ARCH\@/$(arch)/g' $(TASK) | \
	 cpp -nostdinc -nostdinc++ -P -undef -D ARCH=$(arch) -D ARCH_$(subst -,_,$(subst +,_,$(arch))) \
	     -U $(arch) -U i386 -U linux -U unix \
	     -DFORCENONUSONCD1=$(forcenonusoncd1) \
	     -I $(BASEDIR)/tasks/auto/$(IMAGE_TYPE) -I $(BASEDIR)/tasks -I $(SDIR) - -; \
	)) | sort | uniq > $(SDIR)/rawlist

## DIRECTORIES && PACKAGES && INFOS ##

# Create all the needed directories for installing packages (plus the
# .disk directory)
tree: bin-tree src-tree
bin-tree: ok bin-list $(BDIR)/CD1/ubuntu
$(BDIR)/CD1/ubuntu:
	@echo "Adding the required directories to the binary CDs ..."
	$(Q)set -e; \
	 for i in $(BDIR)/*.packages; do \
		dir=$${i%%.packages}; \
		dir=$${dir##$(BDIR)/}; \
		dir=$(BDIR)/CD$$dir; \
		mkdir -p $$dir; \
		$(add_dirs) $$dir; \
	done

src-tree: ok src-list $(SDIR)/CD1/ubuntu
$(SDIR)/CD1/ubuntu:
	@echo "Adding the required directories to the source CDs ..."
	$(Q)set -e; \
	 for i in $(SDIR)/*.sources; do \
		dir=$${i%%.sources}; \
		dir=$${dir##$(SDIR)/}; \
		dir=$(SDIR)/CD$$dir; \
		mkdir -p $$dir; \
		$(add_dirs) $$dir; \
	done

# CD labels / volume ids / disk info
infos: bin-infos src-infos
bin-infos: bin-tree $(BDIR)/CD1/.disk/info
$(BDIR)/CD1/.disk/info:
	@echo "Generating the binary CD labels and their volume ids ..."
	$(Q)set -e; \
	 nb=`find $(BDIR) -name \*.packages | grep '^..?\.packages$$' | wc -l | tr -d " "`; num=0;\
	 DATE=$${CDIMAGE_DATE:-`date +%Y%m%d`}; \
	for i in $(BDIR)/*.packages; do \
		num=$${i%%.packages}; num=$${num##$(BDIR)/}; \
		dir=$(BDIR)/CD$$num; \
		echo -n $(BINDISKINFO) | sed 's/_NONUS//g' > $$dir/.disk/info; \
		echo '#define DISKNAME ' $(BINDISKINFOND) | sed 's/_NONUS//g' \
					> $$dir/README.diskdefines; \
		echo '#define TYPE  binary' \
					>> $$dir/README.diskdefines; \
		echo '#define TYPEbinary  1' \
					>> $$dir/README.diskdefines; \
		echo '#define ARCH ' $(ARCH) \
					>> $$dir/README.diskdefines; \
		echo '#define ARCH'$(ARCH) ' 1' \
					>> $$dir/README.diskdefines; \
		echo '#define DISKNUM ' $$num | sed 's/_NONUS//g' \
					>> $$dir/README.diskdefines; \
		echo '#define DISKNUM'$$num ' 1' | sed 's/_NONUS//g' \
					>> $$dir/README.diskdefines; \
		echo '#define TOTALNUM ' $$nb \
					>> $$dir/README.diskdefines; \
		echo '#define TOTALNUM'$$nb ' 1' \
					>> $$dir/README.diskdefines; \
		echo -n $(BINVOLID) > $(BDIR)/$${num}.volid; \
		$(set_mkisofs_opts) bin $$num > $(BDIR)/$${num}.mkisofs_opts; \
	done
src-infos: src-tree $(SDIR)/CD1/.disk/info
$(SDIR)/CD1/.disk/info:
	@echo "Generating the source CD labels and their volume ids ..."
	$(Q)set -e; \
	 nb=`find $(SDIR) -name \*.sources | grep '^..?\.sources$$'  | wc -l | tr -d " "`; num=0;\
	 DATE=$${CDIMAGE_DATE:-`date +%Y%m%d`}; \
	for i in $(SDIR)/*.sources; do \
		num=$${i%%.sources}; num=$${num##$(SDIR)/}; \
		dir=$(SDIR)/CD$$num; \
		echo -n $(SRCDISKINFO) | sed 's/_NONUS//g' > $$dir/.disk/info; \
		echo '#define DISKNAME ' $(SRCDISKINFOND) | sed 's/_NONUS//g' \
					> $$dir/README.diskdefines; \
		echo '#define TYPE  source' \
					>> $$dir/README.diskdefines; \
		echo '#define TYPEsource  1' \
					>> $$dir/README.diskdefines; \
		echo '#define ARCH ' $(ARCH) \
					>> $$dir/README.diskdefines; \
		echo '#define ARCH'$(ARCH) ' 1' \
					>> $$dir/README.diskdefines; \
		echo '#define DISKNUM ' $$num | sed 's/_NONUS//g' \
					>> $$dir/README.diskdefines; \
		echo '#define DISKNUM'$$num ' 1' | sed 's/_NONUS//g' \
					>> $$dir/README.diskdefines; \
		echo '#define TOTALNUM ' $$nb \
					>> $$dir/README.diskdefines; \
		echo '#define TOTALNUM'$$nb ' 1' \
					>> $$dir/README.diskdefines; \
		echo -n $(SRCVOLID) > $(SDIR)/$${num}.volid; \
		$(set_mkisofs_opts) src $$num > $(SDIR)/$${num}.mkisofs_opts; \
	done

# Adding the deb files to the images
packages: bin-infos bin-list $(BDIR)/packages-stamp
$(BDIR)/packages-stamp:
	@echo "Current disk usage on the binary CDs (before the debs are added) :"
	@cd $(BDIR) && du -sm CD[0123456789]*
	@echo "Adding the selected packages to each CD :"
ifeq ($(CDIMAGE_INSTALL_BASE),1)
ifneq ($(CDIMAGE_ADDON),1)
	@# Check that all packages required by debootstrap are included
	@# and create .disk/base_installable if yes
	@# Also create .disk/base_components
	$(Q)for DISK in $(FIRSTDISKS); do \
	    DISK=$${DISK##CD}; \
	    if [ -x "/usr/sbin/debootstrap" ]; then \
	        ok=yes; \
		mkdir -p $(DEBOOTSTRAP)/tmp-$(ARCH) ; \
	        for p in `$(DEBOOTSTRAPROOT) /usr/sbin/debootstrap --arch $(ARCH) --print-debs $(CODENAME) $(DEBOOTSTRAP)/tmp-$(ARCH) file://$(MIRROR) $(DEBOOTSTRAP)/$(CODENAME)-$(FULLARCH)`; do \
		    if ! grep -q ^$$p$$ $(BDIR)/$$DISK.packages; then \
			if [ -n "$(BASE_EXCLUDE)" ] && grep -q ^$$p$$ $(BASE_EXCLUDE); then \
				echo "Missing debootstrap-required $$p but included in $(BASE_EXCLUDE)"; \
				continue; \
			fi; \
		        ok=no; \
		        echo "Missing debootstrap-required $$p"; \
		    fi; \
	        done; \
	        if [ "$$ok" = "yes" ]; then \
		    echo "CD$$DISK contains all packages needed by debootstrap"; \
		    touch $(BDIR)/CD$$DISK/.disk/base_installable; \
	        else \
		    echo "CD$$DISK missing some packages needed by debootstrap"; \
		    exit 1; \
	        fi; \
	    else \
	        echo "Unable to find debootstrap program"; \
	    fi; \
	    echo 'main' > $(BDIR)/CD$$DISK/.disk/base_components; \
	    if [ "$$RESTRICTED" = 1 ]; then \
		echo 'restricted' >> $(BDIR)/CD$$DISK/.disk/base_components; \
	    fi; \
	    if [ "$$UNIVERSE" = 1 ]; then \
		echo 'universe' >> $(BDIR)/CD$$DISK/.disk/base_components; \
	    fi; \
	    if [ "$$MULTIVERSE" = 1 ]; then \
		echo 'multiverse' >> $(BDIR)/CD$$DISK/.disk/base_components; \
	    fi; \
	    if [ "$$CDIMAGE_DVD" = 1 ]; then \
	    	echo 'dvd/single' > $(BDIR)/CD$$DISK/.disk/cd_type; \
	    else \
	        echo 'full_cd/single' > $(BDIR)/CD$$DISK/.disk/cd_type; \
	    fi; \
	    if [ -n "$(UDEB_INCLUDE)" ] ; then \
		if [ -r "$(UDEB_INCLUDE)" ] ; then \
		    cp -af "$(UDEB_INCLUDE)" \
		        "$(BDIR)/CD$$DISK/.disk/udeb_include"; \
		else \
		    echo "ERROR: Unable to read UDEB_INCLUDE file $(UDEB_INCLUDE)"; \
		fi; \
	    fi; \
	    if [ -n "$(UDEB_EXCLUDE)" ] ; then \
		if [ -r "$(UDEB_EXCLUDE)" ] ; then \
		    cp -af "$(UDEB_EXCLUDE)" \
		        "$(BDIR)/CD$$DISK/.disk/udeb_exclude"; \
		else \
		    echo "ERROR: Unable to read UDEB_EXCLUDE file $(UDEB_EXCLUDE)"; \
		fi; \
	    fi; \
	    if [ -n "$(BASE_INCLUDE)" ] ; then \
		if [ -r "$(BASE_INCLUDE)" ] ; then \
		    cp -af "$(BASE_INCLUDE)" \
		        "$(BDIR)/CD$$DISK/.disk/base_include"; \
		else \
		    echo "ERROR: Unable to read BASE_INCLUDE file $(BASE_INCLUDE)"; \
		fi; \
	    fi; \
	    if [ -n "$(BASE_EXCLUDE)" ] ; then \
		if [ -r "$(BASE_EXCLUDE)" ] ; then \
		    cp -af $(BASE_EXCLUDE) \
			$(BDIR)/CD$$DISK/.disk/base_exclude; \
		else \
		    echo "ERROR: Unable to read BASE_EXCLUDE file $(BASE_EXCLUDE)"; \
		fi; \
	    fi; \
	done
endif
else
ifeq ($(CDIMAGE_LIVE),1)
	@# Ubuntu live CDs are installable too
	touch $(BDIR)/CD1/.disk/base_installable
	if [ "$$CDIMAGE_DVD" = 1 ]; then \
	    echo 'dvd/single' > $(BDIR)/CD1/.disk/cd_type; \
	else \
	    echo 'full_cd/single' > $(BDIR)/CD1/.disk/cd_type; \
	fi
endif
endif
	$(Q)set -e; \
	 for i in $(BDIR)/*.packages; do \
		dir=$${i%%.packages}; \
		n=$${dir##$(BDIR)/}; \
		dir=$(BDIR)/CD$$n; \
		echo "$$n ... "; \
	  	cat $$i | xargs -n 200 -r $(add_packages) $$dir; \
		if [ -x "$(HOOK)" ]; then \
		   cd $(BDIR) && $(HOOK) $$n before-scanpackages; \
		fi; \
		$(scanpackages) scan $$dir; \
		echo "done."; \
	done
	@#Now install the Packages and Packages.cd files
	$(Q)set -e; \
	 for i in $(BDIR)/*.packages; do \
		dir=$${i%%.packages}; \
		dir=$${dir##$(BDIR)/}; \
		dir=$(BDIR)/CD$$dir; \
		$(scanpackages) install $$dir; \
	done
ifeq ($(CDIMAGE_LIVE),1)
	$(Q)$(add_live_filesystem)
ifneq ($(PROJECT),edubuntu)
	$(Q)$(add_winfoss)
endif
endif
ifeq ($(PROJECT),edubuntu)
ifeq ($(CDIMAGE_INSTALL),1)
	$(Q)$(add_winfoss)
endif
endif
	$(Q)touch $(BDIR)/packages-stamp

sources: src-infos src-list $(SDIR)/sources-stamp
$(SDIR)/sources-stamp:
	@echo "Adding the selected sources to each CD."
	$(Q)set -e; \
	 for i in $(SDIR)/*.sources; do \
		dir=$${i%%.sources}; \
		n=$${dir##$(SDIR)/}; \
		dir=$(SDIR)/CD$$n; \
		echo -n "$$n ... "; \
		echo -n "main ... "; \
		grep -vE "(non-US/|/local/)" $$i > $$i.main || true ; \
		if [ -s $$i.main ] ; then \
			cat $$i.main | xargs $(add_files) $$dir $(MIRROR); \
		fi ; \
		if [ -n "$(LOCAL)" ]; then \
			echo -n "local ... "; \
			grep "/local/" $$i > $$i.local || true ; \
			if [ -s $$i.local ] ; then \
				if [ -n "$(LOCALDEBS)" ] ; then \
					cat $$i.local | xargs $(add_files) \
						$$dir $(LOCALDEBS); \
			    else \
					cat $$i.local | xargs $(add_files) \
						$$dir $(MIRROR); \
				fi; \
		    fi; \
		fi; \
		if [ -n "$(NONUS)" ]; then \
			echo -n "non-US ... "; \
			grep "non-US/" $$i > $$i.nonus || true ; \
			if [ -s $$i.nonus ] ; then \
				cat $$i.nonus | xargs $(add_files) $$dir $(NONUS); \
			fi; \
		fi; \
		$(scansources) $$dir; \
		echo "done."; \
	done
	$(Q)touch $(SDIR)/sources-stamp

## BOOT & DOC & INSTALL ##

# Basic checks
$(MIRROR)/doc: need-complete-mirror
$(MIRROR)/tools: need-complete-mirror
need-complete-mirror:
	# now a no-op

# Add everything that is needed to make the CDs bootable
bootable: ok disks installtools packages $(BDIR)/bootable-stamp
$(BDIR)/bootable-stamp:
	@echo "Making the binary CDs bootable ..."
	$(Q)set -e; \
	 for file in $(BDIR)/*.packages; do \
		dir=$${file%%.packages}; \
		n=$${dir##$(BDIR)/}; \
		dir=$(BDIR)/CD$$n; \
		if [ -f $(BASEDIR)/tools/boot/$(DI_CODENAME)/boot-$(FULLARCH) ]; then \
		    cd $(BDIR); \
		    echo "Running tools/boot/$(DI_CODENAME)/boot-$(FULLARCH) $$n $$dir" ; \
		    $(BASEDIR)/tools/boot/$(DI_CODENAME)/boot-$(FULLARCH) $$n $$dir; \
		elif [ -f $(BASEDIR)/tools/boot/$(DI_CODENAME)/boot-$(ARCH) ]; then \
		    cd $(BDIR); \
		    echo "Running tools/boot/$(DI_CODENAME)/boot-$(ARCH) $$n $$dir" ; \
		    $(BASEDIR)/tools/boot/$(DI_CODENAME)/boot-$(ARCH) $$n $$dir; \
		else \
		    if [ "$${IGNORE_MISSING_BOOT_SCRIPT:-0}" = "0" ]; then \
			echo "No script to make CDs bootable for $(FULLARCH) ..."; \
			exit 1; \
		    fi; \
		fi; \
	done
	$(Q)touch $(BDIR)/bootable-stamp

# Add the doc files to the CDs and the Release-Notes and the
# Contents-$(ARCH).gz files
bin-doc: ok bin-infos $(MIRROR)/doc $(BDIR)/CD1/doc
$(BDIR)/CD1/doc:
	@echo "Adding the documentation (bin) ..."
	mkdir -p $(BDIR)/$$DISK/doc
	$(Q)$(add_bin_doc) # Common stuff for all disks

src-doc: ok src-infos $(SDIR)/CD1/README.html
$(SDIR)/CD1/README.html:
	@echo "Adding the documentation (src) ..."
	$(Q)set -e; \
	 for i in $(SDIR)/*.sources; do \
		dir=$${i%%.sources}; \
		dir=$${dir##$(SDIR)/}; \
		dir=$(SDIR)/CD$$dir; \
		mkdir -p $$dir/pics ; \
		cp $(BASEDIR)/data/pics/*.* $$dir/pics/ ; \
	done

# Add the install stuff on the first CD
installtools: ok bin-doc disks $(BDIR)/CD1/install
$(BDIR)/CD1/install:
	@echo "Adding install tools and documentation ..."
	$(Q)set -e; \
	 for DISK in $(FIRSTDISKS) ; do \
		mkdir $(BDIR)/$$DISK/install ; \
		if [ -x "$(BASEDIR)/tools/$(CODENAME)/installtools.sh" ]; then \
			$(BASEDIR)/tools/$(CODENAME)/installtools.sh $(BDIR)/$$DISK ; \
		fi ; \
	done

ifeq (,$(findstring serveraddon,$(call CDBASE,2)))
ifeq ($(CDIMAGE_ADDON),1)
app-install: ok packages $(BDIR)/CD1/app-install
$(BDIR)/CD1/app-install:
	@echo "Adding app-install data ..."
	$(Q)set -e; \
	if [ -x "$(BASEDIR)/tools/$(CODENAME)/app-install.sh" ]; then \
		$(BASEDIR)/tools/$(CODENAME)/app-install.sh 1 $(BDIR)/CD1; \
	fi
else
app-install:
endif
else
app-install: ok packages $(BDIR)/CD2/app-install
$(BDIR)/CD2/app-install:
	@echo "Adding app-install data ..."
	$(Q)set -e; \
	if [ -x "$(BASEDIR)/tools/$(CODENAME)/app-install.sh" ]; then \
		$(BASEDIR)/tools/$(CODENAME)/app-install.sh 2 $(BDIR)/CD2; \
	fi
endif

# Add the disks-arch directories if/where needed
disks: ok bin-infos $(BDIR)/CD1/dists/$(DI_CODENAME)/main/disks-$(ARCH)
$(BDIR)/CD1/dists/$(DI_CODENAME)/main/disks-$(ARCH):
ifdef BOOTDISKS
	@echo "Adding disks-$(ARCH) stuff ..."
	$(Q)set -e; \
	 for DISK in $(FIRSTDISKS) ; do \
		mkdir -p $(BDIR)/$$DISK/dists/$(DI_CODENAME)/main/disks-$(ARCH) ; \
		$(add_files) \
		  $(BDIR)/$$DISK/dists/$(DI_CODENAME)/main/disks-$(ARCH) \
		  $(BOOTDISKS) . ; \
		touch $(BDIR)/$$DISK/.disk/kernel_installable ; \
		cd $(BDIR)/$$DISK/dists/$(DI_CODENAME)/main/disks-$(ARCH); \
		rm -rf base-images-*; \
		if [ "$(SYMLINK)" != "" ]; then exit 0; fi; \
		if [ -L current ]; then \
			CURRENT_LINK=`readlink current`; \
			mv $$CURRENT_LINK .tmp_link; \
			rm -rf [0123456789]*; \
			mv .tmp_link $$CURRENT_LINK; \
		elif [ -d current ]; then \
			rm -rf [0123456789]*; \
		fi; \
	done
endif

ifneq ($(CDIMAGE_INSTALL_BASE),1)
upgrade:
else
upgrade: ok bin-infos $(BDIR)/upgrade-stamp
$(BDIR)/upgrade-stamp:
	@echo "Trying to add upgrade* directories ..."
	$(Q)if [ -x "$(BASEDIR)/tools/$(CODENAME)/upgrade.sh" ]; then \
		$(BASEDIR)/tools/$(CODENAME)/upgrade.sh $(BDIR); \
	 fi
	$(Q)if [ -x "$(BASEDIR)/tools/$(CODENAME)/upgrade-$(ARCH).sh" ]; then \
		$(BASEDIR)/tools/$(CODENAME)/upgrade-$(ARCH).sh $(BDIR); \
	 fi
	$(Q)touch $(BDIR)/upgrade-stamp
endif

## EXTRAS ##

# Launch the extras scripts correctly for customizing the CDs
extras: bin-extras
bin-extras: ok
	$(Q)if [ -z "$(DIR)" -o -z "$(CD)" -o -z "$(ROOTSRC)" ]; then \
	  echo "Give me more parameters (DIR, CD and ROOTSRC are required)."; \
	  false; \
	fi
	@echo "Adding dirs '$(DIR)' from '$(ROOTSRC)' to '$(BDIR)/CD$(CD)'" ...
	$(Q)$(add_files) $(BDIR)/CD$(CD) $(ROOTSRC) $(DIR)
src-extras:
	$(Q)if [ -z "$(DIR)" -o -z "$(CD)" -o -z "$(ROOTSRC)" ]; then \
	  echo "Give me more parameters (DIR, CD and ROOTSRC are required)."; \
	  false; \
	fi
	@echo "Adding dirs '$(DIR)' from '$(ROOTSRC)' to '$(SDIR)/CD$(CD)'" ...
	$(Q)$(add_files) $(SDIR)/CD$(CD) $(ROOTSRC) $(DIR)

## IMAGE BUILDING ##

# Get some size info about the build dirs
imagesinfo: bin-imagesinfo
bin-imagesinfo: ok
	$(Q)for i in $(BDIR)/*.packages; do \
		echo `du -sb $${i%%.packages}`; \
	done
src-imagesinfo: ok
	$(Q)for i in $(SDIR)/*.sources; do \
		echo `du -sb $${i%%.sources}`; \
	done

# Generate a md5sum.txt file listings all files on the CD
md5list: bin-md5list src-md5list
bin-md5list: ok packages bin-secured $(BDIR)/CD1/md5sum.txt
$(BDIR)/CD1/md5sum.txt:
	@echo "Generating md5sum of files from all the binary CDs ..."
	$(Q)set -e; \
	if [ "$$FASTSUMS" != "1" ] ; then \
	 for file in $(BDIR)/*.packages; do \
		dir=$${file%%.packages}; \
		n=$${dir##$(BDIR)/}; \
		dir=$(BDIR)/CD$$n; \
		test -x "$(HOOK)" && cd $(BDIR) && $(HOOK) $$n before-mkisofs; \
		cd $$dir; \
		find . -follow -type f -print0 | grep -zZ -v "\./md5sum" | \
		grep -zZ -v "dists/stable" | grep -zZ -v "dists/frozen" | \
		grep -zZ -v "dists/unstable" | \
		xargs -0 $(md5sum) > md5sum.txt ; \
	 done \
	else \
	 $(fastsums) $(BDIR); \
	fi
	$(Q)set -e; for dir in $(BDIR)/CD*; do \
		[ -d "$$dir" ] || continue; \
		$(hardlink) "$$dir"; \
	done
src-md5list: ok sources src-secured $(SDIR)/CD1/md5sum.txt
$(SDIR)/CD1/md5sum.txt:
	@echo "Generating md5sum of files from all the source CDs ..."
	$(Q)set -e; \
	if [ "$$FASTSUMS" != "1" ] ; then \
	 for file in $(SDIR)/*.sources; do \
		dir=$${file%%.sources}; \
		dir=$${dir##$(SDIR)/}; \
		dir=$(SDIR)/CD$$dir; \
		cd $$dir; \
		find . -follow -type f -print0 | grep -zZ -v "\./md5sum" | \
		grep -zZ -v "dists/stable" | grep -zZ -v "dists/frozen" | \
		grep -zZ -v "dists/unstable" | \
		xargs -0 $(md5sum) > md5sum.txt ; \
	 done \
	else \
	 $(fastsums) $(SDIR); \
	fi
	$(Q)set -e; for dir in $(BDIR)/CD*; do \
		[ -d "$$dir" ] || continue; \
		$(hardlink) "$$dir"; \
	done


# Generate $CODENAME-secured tree with Packages and Release(.gpg) files
# from the official tree
# Complete the Release file from the normal tree
secured: bin-secured src-secured
bin-secured: $(BDIR)/secured-stamp
$(BDIR)/secured-stamp:
	@echo "Generating $(CODENAME)-secured on all the binary CDs ..."
	$(Q)set -e; \
	 for file in $(BDIR)/*.packages; do \
		dir=$${file%%.packages}; \
		n=$${dir##$(BDIR)/}; \
		dir=$(BDIR)/CD$$n; \
		cd $$dir; \
		$(add_secured); \
	done
	$(Q)touch $(BDIR)/secured-stamp

src-secured: $(SDIR)/secured-stamp
$(SDIR)/secured-stamp:
	@echo "Generating $(CODENAME)-secured on all the source CDs ..."
	$(Q)set -e; \
	 for file in $(SDIR)/*.sources; do \
		dir=$${file%%.sources}; \
		dir=$${dir##$(SDIR)/}; \
		dir=$(SDIR)/CD$$dir; \
		cd $$dir; \
		$(add_secured); \
	done
	$(Q)touch $(SDIR)/secured-stamp

# Generates all the images
images: bin-images src-images

# DOJIGDO actions   (for both binaries and source)
#    0    isofile
#    1    isofile + jigdo, cleanup_jigdo
#    2    jigdo, cleanup_jigdo
#
bin-images: ok bin-md5list $(OUT)
	@echo "Generating the binary iso/jigdo images ..."
	$(Q)set -e; \
	 for file in $(BDIR)/*.packages; do \
		dir=$${file%%.packages}; \
		n=$${dir##$(BDIR)/}; \
		num=$$n; \
		dir=$(BDIR)/CD$$n; \
		cd $$dir/..; \
		opts=`cat $(BDIR)/$$n.mkisofs_opts`; \
		volid=`cat $(BDIR)/$$n.volid`; \
		rm -f $(OUT)/$(call CDBASE,$$n).raw; \
		if [ "$(IMAGE_FORMAT)" = "vfat" ]; then \
			if [ -d boot$$n/ ]; then \
				cp -a boot$$n/* CD$$n; \
			fi; \
			$(make_vfat_img) -d CD$$n \
			 -o $(OUT)/$(call CDBASE,$$n).raw; \
		elif [ "$(IMAGE_FORMAT)" = "iso" ]; then \
		if [ "$(DOJIGDO)" = "0" ]; then \
			$(verbose) $(MKISOFS) $(MKISOFS_OPTS) -V "$$volid" \
			  -o $(OUT)/$(call CDBASE,$$n).raw $$opts CD$$n; \
			chmod +r $(OUT)/$(call CDBASE,$$n).raw; \
		elif [ "$(DOJIGDO)" = "1" ]; then \
			$(verbose) $(MKISOFS) $(MKISOFS_OPTS) -V "$$volid" \
			  -o $(OUT)/$(call CDBASE,$$n).raw \
			  -jigdo-jigdo $(OUT)/$(call CDBASE,$$n).jigdo \
			  -jigdo-template $(OUT)/$(call CDBASE,$$n).template \
			  -jigdo-map Debian=$(MIRROR)/ \
			  -jigdo-exclude boot$$n \
			  -md5-list $(BDIR)/md5-check \
			  $(JIGDO_OPTS) $$opts CD$$n; \
			chmod +r $(OUT)/$(call CDBASE,$$n).raw; \
		elif [ "$(DOJIGDO)" = "2" ]; then \
			$(verbose) $(MKISOFS) $(MKISOFS_OPTS) -V "$$volid" \
			  -o /dev/null -v \
			  -jigdo-jigdo $(OUT)/$(call CDBASE,$$n).jigdo \
			  -jigdo-template $(OUT)/$(call CDBASE,$$n).template \
			  -jigdo-map Debian=$(MIRROR)/ \
			  -jigdo-exclude boot$$n \
			  -md5-list $(BDIR)/md5-check \
			  $(JIGDO_OPTS) $$opts CD$$n; \
		fi; \
		if [ "$(DOJIGDO)" != "0" ]; then \
			$(jigdo_cleanup) $(OUT)/$(call CDBASE,$$n).jigdo \
				$(call CDBASE,$$n).iso $(BDIR)/CD$$n \
				`echo "$(JIGDOTEMPLATEURL)" | sed -e 's|%ARCH%|$(FULLARCH)|g'`"$(call CDBASE,$$n).template" \
				$(BINDISKINFOND) \
				$(JIGDOFALLBACKURLS) ; \
		fi; \
		fi; \
		if [ -f $(BASEDIR)/tools/boot/$(DI_CODENAME)/post-boot-$(FULLARCH) ]; then \
			$(BASEDIR)/tools/boot/$(DI_CODENAME)/post-boot-$(FULLARCH) $$n $(BDIR)/CD$$n \
			$(OUT)/$(call CDBASE,$$n).raw; \
		elif [ -f $(BASEDIR)/tools/boot/$(DI_CODENAME)/post-boot-$(ARCH) ]; then \
			$(BASEDIR)/tools/boot/$(DI_CODENAME)/post-boot-$(ARCH) $$n $(BDIR)/CD$$n \
			$(OUT)/$(call CDBASE,$$n).raw; \
		fi; \
	done
ifeq ($(CDIMAGE_LIVE),1)
	-cp -a $(LIVEIMAGES)/$(FULLARCH).manifest $(OUT)/$(call CDBASE,$$n).manifest
	-if [ -e $(LIVEIMAGES)/$(FULLARCH).manifest-remove ]; then \
		cp -a $(LIVEIMAGES)/$(FULLARCH).manifest-remove $(OUT)/$(call CDBASE,$$n).manifest-remove; \
	else \
		cp -a $(LIVEIMAGES)/$(FULLARCH).manifest-desktop $(OUT)/$(call CDBASE,$$n).manifest-desktop; \
	fi
endif

bin-preinstalled_images: ok $(OUT)
	@echo "Post-processing pre-installed images ...";
	$(Q)set -x; \
	mkdir -p $(BDIR)/CD1; \
	if [ ! -e "$(PREINSTALLEDIMAGES)/$(FULLARCH).$(PREINSTALLED_IMAGE_FILESYSTEM)" ]; then \
		echo "No filesystem for $(FULLARCH)!" >&2; \
		exit 1;	\
	fi;
	mv $(PREINSTALLEDIMAGES)/$(FULLARCH).$(PREINSTALLED_IMAGE_FILESYSTEM) $(OUT)/$(call CDBASE,1).raw; 
	if [ -f $(BASEDIR)/tools/boot/$(DI_CODENAME)/post-boot-$(FULLARCH) ]; then \
		$(BASEDIR)/tools/boot/$(DI_CODENAME)/post-boot-$(FULLARCH) 1 $(BDIR)/CD1 \
		$(OUT)/$(call CDBASE,1).raw; \
	elif [ -f $(BASEDIR)/tools/boot/$(DI_CODENAME)/post-boot-$(ARCH) ]; then \
		$(BASEDIR)/tools/boot/$(DI_CODENAME)/post-boot-$(ARCH) 1 $(BDIR)/CD1 \
		$(OUT)/$(call CDBASE,1).raw; \
	fi
	-cp -a $(PREINSTALLEDIMAGES)/$(FULLARCH).manifest $(OUT)/$(call CDBASE,$$n).manifest
	-if [ -e $(PREINSTALLEDIMAGES)/$(FULLARCH).manifest-remove ]; then \
		cp -a $(PREINSTALLEDIMAGES)/$(FULLARCH).manifest-remove $(OUT)/$(call CDBASE,$$n).manifest-remove; \
	else \
		cp -a $(PREINSTALLEDIMAGES)/$(FULLARCH).manifest-desktop $(OUT)/$(call CDBASE,$$n).manifest-desktop; \
	fi

# FIXME: This only works with CD1, and not with addon CDs.
bin-compress_images: ok $(OUT)
	@if [ ! -e "$(OUT)/$(call CDBASE,1).raw" ]; then \
		echo "No image for $(FULLARCH)!" >&2; \
		exit 1; \
	fi;
	@file -b $(OUT)/$(call CDBASE,1).raw > $(OUT)/$(call CDBASE,1).type
	@gzip -9 --rsyncable $(OUT)/$(call CDBASE,1).raw;
	@mv $(OUT)/$(call CDBASE,1).raw.gz $(OUT)/$(call CDBASE,1).raw; 

src-images: ok src-md5list $(OUT)
	@echo "Generating the source iso/jigdo images ..."
	$(Q)set -e; set -x; \
	 for file in $(SDIR)/*.sources; do \
		dir=$${file%%.sources}; \
		n=$${dir##$(SDIR)/}; \
		num=$$n; \
		dir=$(SDIR)/CD$$n; \
		cd $$dir/..; \
		opts=`cat $(SDIR)/$$n.mkisofs_opts`; \
		volid=`cat $(SDIR)/$$n.volid`; \
		rm -f $(OUT)/$(call CDSRCBASE,$$n).raw; \
		if [ "$(DOJIGDO)" = "0" ]; then \
			$(MKISOFS) $(MKISOFS_OPTS) -V "$$volid" \
			  -o $(OUT)/$(call CDSRCBASE,$$n).raw $$opts CD$$n ; \
			chmod +r $(OUT)/$(call CDSRCBASE,$$n).raw; \
		elif [ "$(DOJIGDO)" = "1" ]; then \
			$(MKISOFS) $(MKISOFS_OPTS) -V "$$volid" \
			  -o $(OUT)/$(call CDSRCBASE,$$n).raw \
			  -jigdo-jigdo $(OUT)/$(call CDSRCBASE,$$n).jigdo \
			  -jigdo-template $(OUT)/$(call CDSRCBASE,$$n).template \
			  -jigdo-map Debian=$(MIRROR)/ \
			  -md5-list $(SDIR)/md5-check \
			  $(JIGDO_OPTS) $$opts CD$$n ; \
			chmod +r $(OUT)/$(call CDSRCBASE,$$n).raw; \
		elif [ "$(DOJIGDO)" = "2" ]; then \
			$(MKISOFS) $(MKISOFS_OPTS) -V "$$volid" \
			  -o /dev/null \
			  -jigdo-jigdo $(OUT)/$(call CDSRCBASE,$$n).jigdo \
			  -jigdo-template $(OUT)/$(call CDSRCBASE,$$n).template \
			  -jigdo-map Debian=$(MIRROR)/ \
			  -md5-list $(SDIR)/md5-check \
			  $(JIGDO_OPTS) $$opts CD$$n ; \
		fi; \
		if [ "$(DOJIGDO)" != "0" ]; then \
			$(jigdo_cleanup) $(OUT)/$(call CDSRCBASE,$$n).jigdo \
				$(call CDSRCBASE,$$n).iso $(SDIR)/CD$$n \
				`echo "$(JIGDOTEMPLATEURL)" | sed -e 's|%ARCH%|src|g'`"$(call CDSRCBASE,$$n).template" \
				$(SRCDISKINFOND) \
				$(JIGDOFALLBACKURLS) ; \
		fi; \
	done

# Generate the *.list files for the Pseudo Image Kit
pi-makelist:
	$(Q)set -e; \
	 cd $(OUT); for file in `find * -name \*.raw`; do \
	     if [ "$(IMAGE_FORMAT)" = "vfat" ]; then \
	         $(BASEDIR)/tools/pi-makelist-vfat \
	             $$file > $${file%%.raw}.list; \
	     elif [ "$(IMAGE_FORMAT)" = "iso" ]; then \
	         $(BASEDIR)/tools/pi-makelist \
	             $$file > $${file%%.raw}.list; \
	     fi \
	 done

# Generate only one image number $(CD)
image: bin-image
bin-image: ok bin-md5list $(OUT)
	@echo "Generating the binary iso image n°$(CD) ..."
	@test -n "$(CD)" || (echo "Give me a CD=<num> parameter !" && false)
	set -e; cd $(BDIR); opts=`cat $(CD).mkisofs_opts`; \
	 volid=`cat $(CD).volid`; \
	 rm -f $(OUT)/$(call CDBASE,$(CD)).raw; \
	 if [ "$(IMAGE_FORMAT)" = "vfat" ]; then \
	 if [ -d boot$(CD)/ ]; then \
	   cp -a boot$(CD)/* CD$(CD); \
	 fi; \
	 $(make_vfat_img) -d CD$(CD) -o $(OUT)/$(call CDBASE,$(CD)).raw; \
	 elif [ "$(IMAGE_FORMAT)" = "iso" ]; then \
	 $(MKISOFS) $(MKISOFS_OPTS) -V "$$volid" \
	  -o $(OUT)/$(call CDBASE,$(CD)).raw $$opts CD$(CD); \
	 chmod +r $(OUT)/$(call CDBASE,$(CD)).raw; \
	 fi; \
         if [ -f $(BASEDIR)/tools/boot/$(DI_CODENAME)/post-boot-$(FULLARCH) ]; then \
                $(BASEDIR)/tools/boot/$(DI_CODENAME)/post-boot-$(FULLARCH) $(CD) $(BDIR)/CD$(CD) \
                 $(OUT)/$(call CDBASE,$(CD)).raw; \
         elif [ -f $(BASEDIR)/tools/boot/$(DI_CODENAME)/post-boot-$(ARCH) ]; then \
                $(BASEDIR)/tools/boot/$(DI_CODENAME)/post-boot-$(ARCH) $(CD) $(BDIR)/CD$(CD) \
                 $(OUT)/$(call CDBASE,$(CD)).raw; \
         fi

src-image: ok src-md5list $(OUT)
	@echo "Generating the source iso image n°$(CD) ..."
	@test -n "$(CD)" || (echo "Give me a CD=<num> parameter !" && false)
	set -e; cd $(SDIR); opts=`cat $(CD).mkisofs_opts`; \
	 volid=`cat $(CD).volid`; \
	 rm -f $(OUT)/$(call CDSRCBASE,$(CD)).raw; \
         $(MKISOFS) $(MKISOFS_OPTS) -V "$$volid" \
	  -o $(OUT)/$(call CDSRCBASE,$(CD)).raw $$opts CD$(CD); \
	 chmod +r $(OUT)/$(call CDSRCBASE,$(CD)).raw


#Calculate the md5sums for the images (if available), or get from templates
imagesums:
	$(Q)cd $(OUT); :> MD5SUMS; :> SHA1SUMS; for file in `find * -name \*.raw`; do \
		$(md5sum) "$$file" >>MD5SUMS; \
		$(sha1sum) "$$file" >>SHA1SUMS; \
	done; \
	for file in `find * -name \*.template`; do \
		if [ "`tail --bytes=33 "$$file" | head --bytes=1 | od -tx1 -An | sed -e 's/ //g'`" != 05 ]; then \
			echo "Possibly invalid template $$file"; exit 1; \
		fi; \
		grep -q " $${file%%.template}.raw"'$$' MD5SUMS \
		 || echo "`tail --bytes=26 "$$file" | head --bytes=16 | od -tx1 -An | sed -e 's/ //g'`  $${file%%.template}.raw" >>MD5SUMS; \
	done

# Likewise, the file size can be extracted from the .template with:
# tail --bytes=32 $$file | head --bytes=6 | od -tx1 -An \
#  | tr ' abcdef' '\nABCDEF' | tac | tr '\n' ' ' \
#  | sed -e 's/ //g; s/^.*$/ibase=16 & /' | tr ' ' '\n' | bc

## MISC TARGETS ##

tasks: ok $(BASEDIR)/data/$(CODENAME)/master
	$(master2tasks)

readme:
	sensible-pager $(BASEDIR)/README

conf:
	sensible-editor $(BASEDIR)/CONF.sh

mirrorcheck-binary: ok
	rm -f $(BDIR)/md5-check
	$(Q)$(grab_md5) $(MIRROR) $(ARCH) $(CODENAME) $(BDIR)/md5-check
	if [ -n "$(NONUS)" ]; then \
		$(grab_md5) $(NONUS) $(ARCH) $(CODENAME) $(BDIR)/md5-check; \
	fi
	if [ -n "$(SECURITY)" ]; then \
		$(grab_md5) $(SECURITY) $(ARCH) $(CODENAME)-security $(BDIR)/md5-check; \
	fi
	if [ "$(UPDATES)" = 1 ]; then \
		$(grab_md5) $(MIRROR) $(ARCH) $(CODENAME)-updates $(BDIR)/md5-check; \
	fi
	if [ "$(PROPOSED)" = 1 ]; then \
		$(grab_md5) $(MIRROR) $(ARCH) $(CODENAME)-proposed $(BDIR)/md5-check; \
	fi

mirrorcheck-source: ok
	rm -f $(SDIR)/md5-check
	$(Q)$(grab_md5) $(MIRROR) source $(CODENAME) $(SDIR)/md5-check
	if [ -n "$(NONUS)" ]; then \
		$(grab_md5) $(NONUS) source $(CODENAME) $(SDIR)/md5-check; \
	fi
	if [ -n "$(SECURITY)" ]; then \
		$(grab_md5) $(SECURITY) source $(CODENAME)-security $(SDIR)/md5-check; \
	fi
	if [ "$(UPDATES)" = 1 ]; then \
		$(grab_md5) $(MIRROR) source $(CODENAME)-updates $(SDIR)/md5-check; \
	fi
	if [ "$(PROPOSED)" = 1 ]; then \
		$(grab_md5) $(MIRROR) source $(CODENAME)-proposed $(SDIR)/md5-check; \
	fi

update-popcon:
	rm -f popcon-inst
	( \
		echo '/*' ; \
		echo '   Popularity Contest results' ; \
		echo '   See the README for details on updating.' ; \
		echo '' ; \
		echo '   Last update: $(shell date)' ; \
		echo '*/' ; \
		echo '' ; \
	) > tasks/popularity-contest-$(CODENAME)
	wget --output-document popcon-inst \
		http://popcon.debian.org/main/by_inst \
		http://popcon.debian.org/contrib/by_inst
	grep -h '^[^#]' popcon-inst | egrep -v '(Total|-----)' | \
		sort -rn -k3,3 -k7,7 -k4,4 | grep -v kernel-source | \
		awk '{print $$2}' >> tasks/popularity-contest-$(CODENAME)
	rm -f popcon-inst

# Little trick to simplify things
official_images: bin-official_images src-official_images
bin-official_images: ok bootable upgrade app-install bin-images
src-official_images: ok src-doc src-images

$(CODENAME)_status: ok init
	@echo "Using the provided status file for $(CODENAME)-$(ARCH) ..."
	$(Q)cp $(BASEDIR)/data/$(CODENAME)/status.$(ARCH) $(ADIR)/status \
	 2>/dev/null || $(MAKE) status || $(MAKE) correctstatus
