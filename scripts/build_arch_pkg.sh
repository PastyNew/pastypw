#!/usr/bin/env bash
# Build a pacman package (.pkg.tar.zst) for Arch Linux / Kali.
#
# Requirements: makepkg (pacman), bsdtar (libarchive), zstd - all present on
# Arch by default.  No root privileges are needed to *build* the package.
#
#     ./scripts/build_arch_pkg.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARCH_DIR="$ROOT/packaging/arch"
cd "$ROOT"

if ! command -v makepkg >/dev/null 2>&1; then
    cat <<'EOF'
error: makepkg was not found.

Install the Arch tooling:
    sudo pacman -S --needed base-devel libarchive zstd
or run the build inside a container:
    docker run --rm -v "$PWD:/pkg" archlinux:base-devel \\
        bash -lc "pacman -Sy --noconfirm base-devel libarchive zstd && /pkg/scripts/build_arch_pkg.sh"
EOF
    exit 1
fi

if [ ! -x dist/pastypw/pastypw ]; then
    echo "error: dist/pastypw is missing - run 'make linux-binary' first" >&2
    exit 1
fi

echo ">> staging sources into src/ (makepkg builds with \$srcdir = src)"
# makepkg only writes inside its own startdir, so the whole PKGBUILD workspace
# can live on scratch storage - ARCH_WORKDIR does exactly that. In CI the bind
# mount refuses some of the writes makepkg makes, so the build then runs in /tmp
# inside the container instead of next to the PKGBUILD.
WORKDIR="${ARCH_WORKDIR:-$ARCH_DIR}"
mkdir -p "$WORKDIR"
STAGE="$WORKDIR/src"
rm -rf "$WORKDIR/src" "$WORKDIR/pkg" "$WORKDIR/build-dir"
cp -a "$ARCH_DIR/PKGBUILD" "$WORKDIR/"
mkdir -p "$STAGE/dist"
cp -a dist/pastypw "$STAGE/dist/pastypw"
mkdir -p "$STAGE/build"
cp -a build/icons "$STAGE/build/icons"
mkdir -p "$STAGE/packaging"
cp -a packaging/desktop "$STAGE/packaging/desktop"
for f in README.md README.en.md LICENSE CHANGELOG.md; do
    [ -f "$ROOT/$f" ] && cp -a "$ROOT/$f" "$STAGE/$f"
done

echo ">> running makepkg in $WORKDIR"
cd "$WORKDIR"
# Diagnostics: makepkg refuses to build as root, and a build directory that it
# does not own surfaces only as a bare "Permission denied" from install(1).
echo "   uid=$(id -u) user=$(id -un)"
mkdir -p "$WORKDIR/pkg/pastypw"
ls -ld "$WORKDIR" "$WORKDIR/pkg" "$WORKDIR/src"

makepkg -sf --noconfirm --nodeps

mkdir -p "$ROOT/dist"
find "$WORKDIR" -maxdepth 1 \( -name '*.pkg.tar.zst' -o -name '*.pkg.tar.xz' \) \
    -exec cp -f {} "$ROOT/dist/" \;

echo
echo "install with:  sudo pacman -U dist/pastypw-*.pkg.tar.zst"
ls -lh "$ROOT"/dist/pastypw-*.pkg.tar.* 2>/dev/null || true