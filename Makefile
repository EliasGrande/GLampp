# main paths
srcdir = ./src
builddir = ./build
distdir = ./dist
license = ./LICENSE

# package info
PACKAGE = glampp
VERSION = 0.1
APPNAME = GLampp
WEBSITE = https://github.com/EliasGrande/GLampp
DESCRIPTION = Gtk3 lampp GUI
DATE := $(shell date -ud @`find "$(srcdir)/" | grep -ve '~$$' \
	| xargs stat -c %Y | sort -nr | sed '1!d'` +%F)

# default values
def_lamppdir = /opt/lampp

# relative paths
rel_bin = glampp.sh
rel_gui = gui/glampp.py
rel_config = config.ini
rel_scriptsdir = scripts
rel_sharedir = share
rel_iconsdir = $(rel_sharedir)/icons
rel_desktop = $(rel_sharedir)/desktop/desktop
rel_install = install.sh
rel_uninstall = uninstall.sh

# install paths
ins_bin = /usr/local/bin/$(PACKAGE)
ins_basedir = /opt/$(PACKAGE)
ins_iconsdir = /usr/share/icons/hicolor
ins_desktop = /usr/share/applications/$(PACKAGE).desktop

# dist
distrun = $(distdir)/$(PACKAGE)-$(VERSION)-$(DATE).run

# substitutions for in.* files
do_sub = sed \
	-e 's,[@]PACKAGE[@],$(PACKAGE),g' \
	-e 's,[@]VERSION[@],$(VERSION),g' \
	-e 's,[@]APPNAME[@],$(APPNAME),g' \
	-e 's,[@]WEBSITE[@],$(WEBSITE),g' \
	-e 's,[@]DESCRIPTION[@],$(DESCRIPTION),g' \
	-e 's,[@]DATE[@],$(DATE),g' \
	-e 's,[@]rel_bin[@],$(rel_bin),g' \
	-e 's,[@]rel_gui[@],$(rel_gui),g' \
	-e 's,[@]rel_config[@],$(rel_config),g' \
	-e 's,[@]rel_scriptsdir[@],$(rel_scriptsdir),g' \
	-e 's,[@]rel_sharedir[@],$(rel_sharedir),g' \
	-e 's,[@]rel_iconsdir[@],$(rel_iconsdir),g' \
	-e 's,[@]rel_desktop[@],$(rel_desktop),g' \
	-e 's,[@]rel_install[@],$(rel_install),g' \
	-e 's,[@]rel_uninstall[@],$(rel_uninstall),g' \
	-e 's,[@]def_lamppdir[@],$(def_lamppdir),g' \
	-e 's,[@]ins_bin[@],$(ins_bin),g' \
	-e 's,[@]ins_basedir[@],$(ins_basedir),g' \
	-e 's,[@]ins_iconsdir[@],$(ins_iconsdir),g' \
	-e 's,[@]ins_desktop[@],$(ins_desktop),g'

all: build

clean:
	find ./ | grep -e '~$$' | xargs rm -f
	rm -Rf "$(builddir)" "$(distdir)"

build: clean
	cp -R "$(srcdir)" "$(builddir)"
	cp "$(license)" "$(builddir)"
	find "$(builddir)/" | grep -e '/in\.[^/]*$$' \
	| while read file_in; do \
		file_out=`echo "$$file_in" | sed -e 's,in\.\([^/]*\)$$,\1,'`; \
		$(do_sub) < "$$file_in" > "$$file_out"; \
		rm "$$file_in"; \
	done
	find "$(builddir)/" -type d | xargs chmod 755
	find "$(builddir)/" -type f | xargs chmod 644
	chmod 744 "$(builddir)/$(rel_gui)"
	chmod 755 "$(builddir)/$(rel_bin)" \
		"$(builddir)/$(rel_install)" \
		"$(builddir)/$(rel_uninstall)"
	find "$(builddir)/$(rel_scriptsdir)/" | xargs chmod 744

install: build
	"$(builddir)/$(rel_install)"
	
uninstall:
	test ! -f "$(ins_basedir)/$(rel_uninstall)" \
		|| "$(ins_basedir)/$(rel_uninstall)"

dist: build
	mkdir -p "$(distdir)"
	makeself "$(builddir)" "$(distrun)" "$(PACKAGE)" "./$(rel_install)"

distinstall: dist
	"$(distrun)"

run:
	"$(ins_bin)"

