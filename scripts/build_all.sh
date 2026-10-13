#!/usr/bin/env bash
# Build every package this machine can build.
#
#   ./scripts/build_all.sh
#   SKIP_APPIMAGE=1 ./scripts/build_all.sh
#
# Windows .exe is NOT built here: PyInstaller cannot cross-compile. Use
# scripts/build_windows.ps1 on Windows or let GitHub Actions do it.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }

step "Unit tests"
"$PY" -m pytest tests -q

step "Icons (PNG, SVG, Windows .ico)"
"$PY" scripts/make_icons.py | tail -3
"$PY" scripts/make_windows_icon.py

step "Screenshots for the README"
QT_QPA_PLATFORM=offscreen "$PY" scripts/render_screenshots.py

step "Frozen application (PyInstaller)"
"$PY" -m PyInstaller packaging/pyinstaller/pastypw-linux.spec \
    --noconfirm --clean --distpath dist --workpath build/pyinstaller >/dev/null
"$PY" scripts/slim_bundle.py

step "Debian package (.deb - Ubuntu, Debian, Kali, Mint...)"
"$PY" scripts/build_deb.py

step "Arch package (.pkg.tar.zst - Arch, Manjaro, Kali)"
if command -v makepkg >/dev/null 2>&1; then
    ./scripts/build_arch_pkg.sh          # канонический makepkg
else
    "$PY" scripts/build_pkg_tar_zst.py   # тот же формат, без makepkg
fi

step "RPM package (.rpm - Fedora, RHEL, openSUSE)"
if command -v rpmbuild >/dev/null 2>&1; then
    ./scripts/build_rpm.sh
else
    echo "   rpmbuild не найден - пропускаю (.rpm соберёт CI)"
    echo "   Debian/Ubuntu: sudo apt install rpm && ./scripts/build_rpm.sh"
fi

if [ -z "${SKIP_APPIMAGE:-}" ]; then
    step "AppImage (portable)"
    if command -v mksquashfs >/dev/null 2>&1 || command -v curl >/dev/null 2>&1; then
        ./scripts/build_appimage.sh || echo "AppImage не собрался - пропускаю"
    fi
fi

step "Готовые файлы"
ls -lh dist/*.deb dist/*.rpm dist/*.pkg.tar.zst dist/*.AppImage 2>/dev/null || true

cat <<'EOF'

Windows .exe здесь не собирается: PyInstaller не умеет кросс-компилировать.
Варианты:
  1. запушить репозиторий на GitHub и забрать .exe из Actions -> Artifacts;
  2. на Windows выполнить:  powershell .\scripts\build_windows.ps1
EOF