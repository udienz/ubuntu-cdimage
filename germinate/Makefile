VERSION := $(shell dpkg-parsechangelog | awk '/Version:/ { print $$2 }')

build:
	$(MAKE) -C debhelper build

clean:
	-find -name \*.pyc | xargs -r rm -f
	$(MAKE) -C debhelper clean

check:
	if which pychecker >/dev/null 2>&1; then \
		pychecker Germinate/Archive/*.py Germinate/*.py *.py; \
	fi

install:
	install -d $(DESTDIR)/usr/bin $(DESTDIR)/usr/lib/germinate/Germinate/Archive
	install *.py $(DESTDIR)/usr/lib/germinate/
	install -m644 Germinate/*.py $(DESTDIR)/usr/lib/germinate/Germinate/
	install -m644 Germinate/Archive/*.py $(DESTDIR)/usr/lib/germinate/Germinate/Archive/
	sed -i 's/@VERSION@/$(VERSION)/g' \
		$(DESTDIR)/usr/lib/germinate/Germinate/version.py
	ln -s /usr/lib/germinate/germinate.py $(DESTDIR)/usr/bin/germinate
	ln -s /usr/lib/germinate/pkg-diff.py $(DESTDIR)/usr/bin/germinate-pkg-diff
	ln -s /usr/lib/germinate/update-metapackage.py $(DESTDIR)/usr/bin/germinate-update-metapackage
	$(MAKE) -C debhelper install
