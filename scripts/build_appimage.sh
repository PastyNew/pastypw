#!/usr/bin/env bash
# Build a portable AppImage (works on Arch, Kali, Ubuntu, Fedora, ...).
#
# Two ways to finish the job - the script picks the first one that works:
#   1. AppImage type-2 runtime + mksquashfs   (no FUSE, no network after download)
#   2. linuxdeploy                             (standard tool, used in CI as well)
#
#     ./scripts/build_appimage.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="$(grep -m1 '^__version__' pastypw/__init__.py | cut -d'"' -f2)"
APPDIR="$ROOT/build/AppDir"
TOOLS="$ROOT/build/tools"
RUNTIME_URL="https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-x86_64"
OUT_NAME="pastypw-${VERSION}-x86_64.AppImage"
export APPIMAGE_EXTRACT_AND_RUN=1

if [ ! -x dist/pastypw/pastypw ]; then
    echo "error: dist/pastypw is missing - run 'make linux-binary' first" >&2
    exit 1
fi

if [ ! -f build/icons/pastypw-256.png ]; then
    echo ">> icons missing, generating"
    python3 scripts/make_icons.py
fi

echo ">> assembling AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/lib" \
         "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
         "$APPDIR/usr/share/icons/hicolor/scalable/apps" \
         "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/metainfo"

cp -a dist/pastypw "$APPDIR/usr/lib/pastypw"

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export QT_PLUGIN_PATH="${HERE}/usr/lib/pastypw/_internal/PySide6/Qt/plugins:${QT_PLUGIN_PATH:-}"
exec "${HERE}/usr/lib/pastypw/pastypw" "$@"
EOF
chmod +x "$APPDIR/AppRun"

install -m 644 packaging/desktop/pastypw.desktop "$APPDIR/pastypw.desktop"
install -m 644 packaging/desktop/pastypw.desktop \
    "$APPDIR/usr/share/applications/pastypw.desktop"
install -m 644 build/icons/pastypw-256.png "$APPDIR/pastypw.png"
install -m 644 build/icons/pastypw-256.png \
    "$APPDIR/usr/share/icons/hicolor/256x256/apps/pastypw.png"
if [ -f build/icons/pastypw.svg ]; then
    install -m 644 build/icons/pastypw.svg \
        "$APPDIR/usr/share/icons/hicolor/scalable/apps/pastypw.svg"
fi
cp README.en.md "$APPDIR/usr/share/metainfo/README.md" 2>/dev/null || true

build_with_runtime() {
    command -v mksquashfs >/dev/null 2>&1 || return 1
    local runtime="$TOOLS/runtime-x86_64"
    mkdir -p "$TOOLS"
    if [ ! -f "$runtime" ]; then
        echo "   downloading the AppImage runtime..."
        curl -fsSL -o "$runtime" "$RUNTIME_URL" || return 1
    fi
    echo ">> building the squashfs image"
    rm -f "$ROOT/build/AppDir.squashfs"
    mksquashfs "$APPDIR" "$ROOT/build/AppDir.squashfs" \
        -root-owned -noappend -no-progress -quiet \
        -comp gzip -b 1048576 >/dev/null || return 1
    echo ">> attaching the runtime"
    rm -f "dist/$OUT_NAME"
    mkdir -p dist
    cat "$runtime" "$ROOT/build/AppDir.squashfs" > "dist/$OUT_NAME"
    chmod +x "dist/$OUT_NAME"
    rm -f "$ROOT/build/AppDir.squashfs"
    return 0
}

build_with_linuxdeploy() {
    local deploy="$TOOLS/linuxdeploy-x86_64.AppImage"
    mkdir -p "$TOOLS"
    if [ ! -f "$deploy" ]; then
        curl -fsSL -o "$deploy" \
            "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage" || return 1
        chmod +x "$deploy"
    fi
    "$deploy" --appdir "$APPDIR" --output appimage \
        --executable "usr/lib/pastypw/pastypw" \
        --desktop-file "$APPDIR/pastypw.desktop" \
        --icon-file "$APPDIR/pastypw.png" \
        --no-appstream || return 1
    find "$APPDIR" -maxdepth 1 -name '*.AppImage' -exec cp -f {} dist/ \;
    return 0
}

mkdir -p dist
if build_with_runtime; then
    echo ">> built with the AppImage runtime + mksquashfs"
elif build_with_linuxdeploy; then
    echo ">> built with linuxdeploy"
else
    cat >&2 <<'EOF'
error: could not build the AppImage.

Install one of the following and try again:
    sudo apt install squashfs-tools     # method 1 (recommended)
    # or let the script download linuxdeploy (needs FUSE or extract-and-run)
EOF
    exit 1
fi

echo
echo "install with:  chmod +x dist/$OUT_NAME && ./$OUT_NAME"
ls -lh dist/*.AppImage
echo
echo "verify with:  ./dist/$OUT_NAME --appimage-extract && ls squashfs-root"