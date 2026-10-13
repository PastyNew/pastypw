#!/usr/bin/env bash
# Build an RPM package for Fedora / RHEL / openSUSE.
#
# Requirements: the PyInstaller bundle in dist/pastypw and rpmbuild.
#     ./scripts/build_rpm.sh                    # -> dist/pastypw-1.0.0-1.x86_64.rpm
#
# RPMBUILD is honoured, which is handy when rpmbuild was extracted from a
# .deb into a private directory (no root required) and its libraries are
# exported through LD_LIBRARY_PATH.
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

RPMBUILD="${RPMBUILD:-rpmbuild}"

if ! command -v "$RPMBUILD" >/dev/null 2>&1; then
    cat <<'EOF'
error: rpmbuild is not installed.

Fedora / RHEL / CentOS:   sudo dnf install rpm-build
openSUSE:                sudo zypper install rpm
Arch (from AUR repo):    sudo pacman -S rpm
Ubuntu / Debian:         sudo apt install rpm
EOF
    exit 1
fi

if [ ! -x dist/pastypw/pastypw ]; then
    echo "error: dist/pastypw is missing - run 'make linux-binary' first" >&2
    exit 1
fi

VERSION="$(grep -m1 '^__version__' pastypw/__init__.py | cut -d'"' -f2)"
RELEASE="${RELEASE:-1}"
ARCH_NAME="$(uname -m)"

BUILD_DIR="$ROOT/build/rpm"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
mkdir -p "$BUILD_DIR/tarball/packaging" "$BUILD_DIR/tarball/build" "$BUILD_DIR/tarball/dist"

cp -a packaging/desktop "$BUILD_DIR/tarball/packaging/desktop"
cp -a packaging/rpm "$BUILD_DIR/tarball/packaging/rpm"
cp -a build/icons "$BUILD_DIR/tarball/build/icons"
cp -a dist/pastypw "$BUILD_DIR/tarball/dist/pastypw"
for f in README.md README.en.md LICENSE CHANGELOG.md; do
    [ -f "$ROOT/$f" ] && cp -a "$ROOT/$f" "$BUILD_DIR/tarball/$f"
done

TARBALL="$BUILD_DIR/SOURCES/pastypw-${VERSION}.tar.gz"
tar -czf "$TARBALL" -C "$BUILD_DIR/tarball" --transform "s,^\.,pastypw-${VERSION}," .

# keep the spec's version/release in sync with the project version
SPEC_FILE="$BUILD_DIR/SPECS/pastypw.spec"
sed -e "s/^%global version.*/%global version ${VERSION}/" \
    -e "s/^%global release.*/%global release ${RELEASE}/" \
    packaging/rpm/pastypw.spec > "$SPEC_FILE"

"$RPMBUILD" -ba \
    --define "_topdir $BUILD_DIR" \
    --define "_dbpath $BUILD_DIR/rpmdb" \
    --define "__find_debuginfo /bin/true" \
    "$SPEC_FILE"

mkdir -p dist
find "$BUILD_DIR/RPMS" -name '*.rpm' -exec cp -f {} dist/ \;
find "$BUILD_DIR/SRPMS" -name '*.rpm' -exec cp -f {} dist/ \;

echo
echo "Built for $ARCH_NAME:"
ls -lh dist/*.rpm
echo
echo "install with:  sudo dnf install ./dist/pastypw-*.rpm"
echo "               (or: sudo rpm -Uvh dist/pastypw-*.rpm)"