# Contributing to PastyNew Password Generator

Thanks for helping out, PastyNew's project stays open for pull requests.

## Quick rules

1. Never commit real passwords, tokens or anything from your history file.
2. Keep the code offline-only: no telemetry, no network calls, no analytics.
3. All randomness must come from `secrets` (never `random`).
4. Any UI change must keep the dark theme consistent (`pastypw/ui/theme.py`).

## Development setup

```bash
git clone https://github.com/PastyNew/pastypw
cd pastypw
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

python -m pytest tests -q          # tests
python -m pastypw                   # run from sources
```

## Project layout

```
pastypw/core/     generation, strength, storage   (no Qt imports!)
pastypw/ui/       theme, i18n, icons, widgets, window
scripts/          icons, screenshots, package builders
packaging/        desktop entry, RPM spec, PKGBUILD, NSIS, PyInstaller specs
tests/            unit tests for pastypw/core
```

## Before opening a pull request

```bash
python -m pytest tests -q
make all          # tests + icons + frozen app + .deb (+ AppImage)
```

Describe the change, mention the platforms you tested on, and add a line to
`CHANGELOG.md`.

## Reporting bugs

Use the bug template: version, distribution, desktop environment, steps to
reproduce, terminal output. Do not attach screenshots containing passwords -
mask them with the eye button in the history card first.