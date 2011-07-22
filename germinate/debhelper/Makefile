VERSION := $(shell cd ..; dpkg-parsechangelog | awk '/Version:/ { print $$2 }')

PERLLIBDIR := $(shell perl -MConfig -e 'print $$Config{vendorlib}')/Debian/Debhelper

POD2MAN := pod2man -c Debhelper -r "$(VERSION)"

build:
	$(POD2MAN) dh_germinate_clean dh_germinate_clean.1
	$(POD2MAN) dh_germinate_metapackage dh_germinate_metapackage.1

clean:
	rm -f *.1

install:
	install -d $(DESTDIR)/usr/bin $(DESTDIR)$(PERLLIBDIR)/Sequence
	install dh_germinate_clean $(DESTDIR)/usr/bin/
	install dh_germinate_metapackage $(DESTDIR)/usr/bin/
	install -m 0644 *.pm $(DESTDIR)$(PERLLIBDIR)/Sequence/
