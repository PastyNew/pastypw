# Maintainer: PastyNew <pastypew@gmail.com>
# RPM spec for PastyNew Password Generator.
#
# The PyInstaller bundle must be built before running this script:
#     python -m PyInstaller packaging/pyinstaller/pastypw-linux.spec --noconfirm --clean
#     python scripts/make_icons.py
#
# Then:
#     ./scripts/build_rpm.sh                 # builds dist/pastypw-1.0.0-1.x86_64.rpm
#     RPMBUILD=rpmbuild ./scripts/build_rpm.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! command -v rpmbuild >/dev/null 2>&1; then
    cat <<'EOF'
error: rpmbuild is not installed.

Fedora / RHEL / CentOS:   sudo dnf install rpm-build
openSUSE:                sudo zypper install rpm
Arch (from AUR repo):    sudo pacman -S rpm
Ubuntu / Debian:         sudo apt install rpm
EOF
    exit 1
fi

if [ ! -d dist/pastypw ]; then
    echo "error: dist/pastypw is missing - build the PyInstaller bundle first" >&2
    exit 1
fi

VERSION="$(grep -m1 '__version__' pastypw/__init__.py | cut -d'"' -f2)"
ARCH_NAME="$(uname -m)"

BUILD_DIR="$ROOT/build/rpm"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
mkdir -p "$BUILD_DIR/tarball/packaging" "$BUILD_DIR/tarball/build"

cp -a packaging/desktop packaging/rpm "$BUILD_DIR/tarball/packaging/"
cp -a packaging/desktop "$BUILD_DIR/tarball/packaging/desktop"
cp -a build/icons "$BUILD_DIR/tarball/build/icons"
mkdir -p "$BUILD_DIR/tarball/dist"
cp -a dist/pastypw "$BUILD_DIR/tarball/dist/pastypw"
for f in README.md README.en.md LICENSE CHANGELOG.md; do
    [ -f "$f" ] && cp -a "$f" "$BUILD_DIR/tarball/$f"
done

TARBALL="$BUILD_DIR/SOURCES/pastypw-${VERSION}.tar.gz"
tar -czf "$TARBALL" -C "$BUILD_DIR/tarball" --transform "s,^\.,pastypw-${VERSION}," .

rpmbuild -ba \
    --define "_topdir $BUILD_DIR" \
    --define "_version $VERSION" \
    packaging/rpm/pastypw.spec

mkdir -p dist
find "$BUILD_DIR/RPMS" -name '*.rpm' -exec cp -f {} dist/ \;
find "$BUILD_DIR/SRPMS" -name '*.rpm' -exec cp -f {} dist/ \;

echo
echo "Built for $ARCH_NAME:"
ls -lh dist/*.rpm
echo
echo "install with:  sudo dnf install ./dist/pastypw-*.rpm"
echo "               (or: sudo rpm -Uvh --nodeps dist/pastypw-*.rpm)"