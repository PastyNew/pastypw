# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- CI: `libglib2.0-0` is installed before PySide6 is imported. Without it the
  Linux job died immediately with
  `ImportError: libglib-2.0.so.0: cannot open shared object file`
- CI: the Windows PyInstaller step runs under `bash`. The default PowerShell
  treated `--noconfirm` as an operator and failed with
  `Missing expression after unary operator '--'`
- CI: `scripts/make_windows_icon.py` no longer crashes with `UnicodeEncodeError`
  when printing cyrillic text to the cp1252 Windows console
- CI: `makensis` is called by its full path. Chocolatey installs it to
  `C:\Program Files (x86)\NSIS`, but the PATH of the running PowerShell session
  is never refreshed, so `makensis` was "not recognized"
- CI: the `linux-packages` artefact now ships the whole `dist/pastypw` bundle.
  It carried only the `pastypw` executable and dropped `_internal/`, so the
  AppImage built from it could not load libpython and started to nothing
- CI: the frozen bundle is verified after restore and fails the build loudly.
  The missing `_internal/` used to be hidden by `|| true` on the smoke test
- Arch packaging: sources are staged into `src/`, where `makepkg` expects them
  (`$srcdir`), instead of next to the PKGBUILD
- Arch packaging: `makepkg` refuses to run as root, and it leaves
  `$startdir/pkg` at mode `0111`, so creating the nested `$pkgdir` failed with
  `Permission denied`
- Arch packaging: the `pastypw` launcher is written with `cat > ... <<EOF`.
  `install -m755 /dev/stdin` exits 0 while creating no file at all, which
  shipped a package with no `pastypw` command
- Arch packaging: `$pkgdir/usr/lib` is created before copying the frozen app

### Changed
- CI: the Arch build runs `makepkg` from a scratch `ARCH_WORKDIR` and disables
  fakeroot, so nothing is written into the bind mount
- `.gitignore` tracks the new Arch scratch paths

## [1.0.0] - 2026-10-13

### Added
- Dark, frameless interface with rounded window, custom title bar and soft shadow
- Cryptographically secure generation via `secrets` (OS CSPRNG)
- Password length slider (4-64) with a numeric field
- Character sets: digits, uppercase, lowercase, special characters
- Guaranteed coverage of every enabled character class
- Batch generation of up to 50 unique passwords with per-row copy and export
- Strength meter: entropy in bits, colour scale and crack-time estimate
- Local history with favourites, reveal toggle, delete and export to `.txt`
- Russian and English interface (switch with the `RU`/`EN` button or `Ctrl+L`)
- Settings persistence (length, amount, character sets, language)
- Packages: `.deb`, `.rpm`, `.pkg.tar.zst` (Arch/Kali), AppImage, Windows `.exe`
- GitHub Actions pipeline that builds every format automatically
- 26 unit tests for the generation, strength and storage layers
- `scripts/build_pkg_tar_zst.py` — builds a pacman package on any Linux
  (without makepkg), writing a valid `.PKGINFO` + `.MTREE` archive
- `scripts/make_windows_icon.py` — multi-size Windows `.ico` (7 resolutions)
- `scripts/build_appimage.sh` — runtime + `mksquashfs` method, `linuxdeploy` fallback

### Fixed
- RPM launcher no longer hardcodes `/usr/lib` (Fedora uses `/usr/lib64`)
- RPM dependency auto-detection disabled: the bundle ships its own Qt6
- History saving keeps the newest entries instead of the first ones

### Creator
- **PastyNew** - interface, algorithm and packaging