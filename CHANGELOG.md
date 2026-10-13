# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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