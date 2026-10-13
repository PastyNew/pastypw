#!/usr/bin/env bash
# Build every package this machine can build.
#
#   ./scripts/build_all.sh            # deb + AppImage (Linux host)
#   SKIP_APPIMAGE=1 ./scripts/build_all.sh
#
# RPM and Arch packages are built by GitHub Actions (see .github/workflows) or,
# on the matching distro, by scripts/build_rpm.sh / scripts/build_arch_pkg.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$1"; }

step "Unit tests"
"$PY" -m pytest tests -q

step "Icons"
"$PY" scripts/make_icons.py | tail -3

step "Frozen application (PyInstaller)"
"$PY" -m PyInstaller packaging/pyinstaller/pastypw-linux.spec \
    --noconfirm --clean --distpath dist --workpath build/pyinstaller >/dev/null
"$PY" scripts/slim_bundle.py

step "Screenshots for the README"
QT_QPA_PLATFORM=offscreen "$PY" scripts/render_screenshots.py

step "Debian package (.deb - Ubuntu, Debian, Kali, Mint...)"
"$PY" scripts/build_deb.py

if [ -z "${SKIP_APPIMAGE:-}" ]; then
    step "AppImage (portable)"
    if command -v curl >/dev/null 2>&1; then
        ./scripts/build_appimage.sh || echo "AppImage step failed - skipping"
    fi
fi

step "Package-specific builds you can run yourself"
cat <<'EOF'
  RPM   (Fedora/RHEL/openSUSE):  ./scripts/build_rpm.sh
  Arch  (Arch/Kali, pacman):      ./scripts/build_arch_pkg.sh
  EXE   (Windows):                powershell .\scripts\build_windows.ps1
  All of them automatically:      https://github.com/PastyNew/pastypw/actions
EOF

step "Result"
ls -lh dist/ || true