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

### Creator
- **PastyNew** - interface, algorithm and packaging