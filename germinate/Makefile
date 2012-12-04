VERSION := $(shell dpkg-parsechangelog | awk '/Version:/ { print $$2 }')

build:
	$(MAKE) -C debhelper build

clean:
	-find -name \*.pyc | xargs -r rm -f
	$(MAKE) -C debhelper clean

check:
	if which pychecker >/dev/null 2>&1; then \
		./run-pychecker; \
	fi

install:
	install -d $(DESTDIR)/usr/bin $(DESTDIR)/usr/lib/germinate/germinate
	install bin/* $(DESTDIR)/usr/bin/
	install -m644 germinate/*.py $(DESTDIR)/usr/lib/germinate/germinate/
	sed -i 's/@VERSION@/$(VERSION)/g' \
		$(DESTDIR)/usr/lib/germinate/germinate/version.py
	$(MAKE) -C debhelper install
