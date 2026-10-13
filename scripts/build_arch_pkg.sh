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

echo ">> staging sources next to PKGBUILD"
rm -rf "$ARCH_DIR/dist" "$ARCH_DIR/build" "$ARCH_DIR/packaging"
cp -a dist/pastypw "$ARCH_DIR/dist/pastypw"
mkdir -p "$ARCH_DIR/build"
cp -a build/icons "$ARCH_DIR/build/icons"
mkdir -p "$ARCH_DIR/packaging"
cp -a packaging/desktop "$ARCH_DIR/packaging/desktop"
for f in README.md README.en.md LICENSE CHANGELOG.md; do
    [ -f "$ROOT/$f" ] && cp -a "$ROOT/$f" "$ARCH_DIR/$f"
done

echo ">> running makepkg"
cd "$ARCH_DIR"
makepkg -sf --noconfirm --nodeps

mkdir -p "$ROOT/dist"
find "$ARCH_DIR" -maxdepth 1 \( -name '*.pkg.tar.zst' -o -name '*.pkg.tar.xz' \) \
    -exec cp -f {} "$ROOT/dist/" \;

echo
echo "install with:  sudo pacman -U dist/pastypw-*.pkg.tar.zst"
ls -lh "$ROOT"/dist/pastypw-*.pkg.tar.* 2>/dev/null || true