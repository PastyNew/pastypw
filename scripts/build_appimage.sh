#!/usr/bin/env bash
# Build a portable AppImage (works on Arch, Kali, Ubuntu, Fedora, ...).
#
# Requirements: linuxdeploy (downloaded automatically), zstd.
#     ./scripts/build_appimage.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VERSION="$(grep -m1 '__version__' pastypw/__init__.py | cut -d'"' -f2)"
APPDIR="$ROOT/build/AppDir"
TOOLS="$ROOT/build/tools"
OUT="$ROOT/dist/pastypw-${VERSION}-x86_64.AppImage"

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
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" "$APPDIR/usr/share/icons/hicolor/256x256/apps" \
         "$APPDIR/usr/share/applications" "$APPDIR/usr/share/metainfo"

cp -a dist/pastypw "$APPDIR/usr/lib/pastypw"

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib/pastypw:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/lib/pastypw/pastypw" "$@"
EOF
chmod +x "$APPDIR/AppRun"

cat > "$APPDIR/pastypw.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=PastyNew Password Generator
Name[ru]=Генератор паролей PastyNew
Comment=Offline password generator by PastyNew
Exec=AppRun
Icon=pastypw
Categories=Utility;Security;
Terminal=false
EOF

cp packaging/desktop/pastypw.desktop "$APPDIR/pastypw.desktop"
cp build/icons/pastypw-256.png "$APPDIR/pastypw.png"
cp build/icons/pastypw-256.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/pastypw.png"
cp build/icons/pastypw.svg "$APPDIR/usr/share/icons/hicolor/scalable/apps/pastypw.svg" 2>/dev/null || true
mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"
cp build/icons/pastypw.svg "$APPDIR/usr/share/icons/hicolor/scalable/apps/pastypw.svg"
cp README.en.md "$APPDIR/usr/share/metainfo/README.md" 2>/dev/null || true

echo ">> packaging with linuxdeploy"
mkdir -p "$TOOLS"
LINUXDEPLOY="$TOOLS/linuxdeploy-x86_64.AppImage"
if [ ! -f "$LINUXDEPLOY" ]; then
    curl -fL -o "$LINUXDEPLOY" \
        "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
    chmod +x "$LINUXDEPLOY"
fi

export APPIMAGE_EXTRACT_AND_RUN=1
"$LINUXDEPLOY" \
    --appdir "$APPDIR" \
    --output appimage \
    --executable usr/lib/pastypw/pastypw \
    --desktop-file "$APPDIR/pastypw.desktop" \
    --icon-file "$APPDIR/pastypw.png" \
    --no-appstream

mkdir -p dist
find "$APPDIR" -maxdepth 1 -name '*.AppImage' -exec cp -f {} dist/ \;

echo
echo "install with:  chmod +x dist/$(basename "$(find "$APPDIR" -maxdepth 1 -name '*.AppImage' | head -1)")"
ls -lh dist/*.AppImage 2>/dev/null || true
_ = "$OUT"