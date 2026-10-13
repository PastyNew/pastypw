# PastyNew Password Generator - developer shortcuts
# Author: PastyNew

PYTHON ?= python3
PYINSTALLER ?= $(PYTHON) -m PyInstaller

.PHONY: help venv install test icons screenshots linux-binary slim deb rpm arch appimage all clean

help:  ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

venv:  ## create .venv with PySide6 + PyInstaller
	$(PYTHON) -m venv .venv || $(PYTHON) -m venv --without-pip .venv
	@test -x .venv/bin/pip || (curl -sSL https://bootstrap.pypa.io/get-pip.py | .venv/bin/python)
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/pip install PySide6 pyinstaller pytest

install: venv  ## alias for venv

test:  ## run the unit tests
	$(PYTHON) -m pytest tests -q

icons:  ## export application icons into build/icons
	$(PYTHON) scripts/make_icons.py

screenshots:  ## render README screenshots (headless)
	QT_QPA_PLATFORM=offscreen $(PYTHON) scripts/render_screenshots.py

linux-binary:  ## build dist/pastypw with PyInstaller
	$(PYINSTALLER) packaging/pyinstaller/pastypw-linux.spec \
		--noconfirm --clean --distpath dist --workpath build/pyinstaller
	$(PYTHON) scripts/slim_bundle.py

slim:  ## remove unused Qt plugins from the bundle
	$(PYTHON) scripts/slim_bundle.py

deb: linux-binary  ## build the .deb package (needs dpkg-deb)
	$(PYTHON) scripts/build_deb.py

rpm:  ## build the .rpm package (needs rpmbuild)
	./scripts/build_rpm.sh

arch:  ## build the .pkg.tar.zst package (needs makepkg)
	./scripts/build_arch_pkg.sh

appimage: linux-binary  ## build the portable AppImage
	./scripts/build_appimage.sh

all:  ## run the full pipeline (tests, icons, binary, deb, AppImage)
	./scripts/build_all.sh

clean:  ## remove build artefacts
	rm -rf build dist .pytest_cache
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +