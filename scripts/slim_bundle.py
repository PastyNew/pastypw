#!/usr/bin/env python3
"""Remove Qt plugins the password generator never needs.

The PyInstaller bundle ships the complete Qt plugin set (~160 MB).  This
script trims the parts that a plain Qt Widgets application does not touch and
reports how much was saved.  Run it right after PyInstaller, before packaging.

    python scripts/slim_bundle.py [dist/pastypw]
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Whole plugin directories that are never loaded by this application.
REMOVE_DIRS = [
    "imageformats",
    "multimedia",
    "audio",
    "sqldrivers",
    "tls",
    "network",
    "websockets",
    "genericdeployer",
    "printsupport",
    "position",
    "sensors",
    "serialport",
    "bluetooth",
    "nfc",
    "remoteobjects",
    "scxml",
    "statecharts",
    "texttospeech",
    "spatialaudio",
    "webview",
    "help",
    "designer",
    "qmltooling",
    "qtwebchannel",
]

# Files inside the "platforms" directory we do want to keep.
KEEP_PLATFORMS = {"libqxcb.so", "libqoffscreen.so", "libqminimal.so", "libqwayland.so"}


def find_plugin_dir(bundle: Path) -> Path | None:
    for candidate in (
        bundle / "_internal" / "PySide6" / "Qt" / "plugins",
        bundle / "_internal" / "PySide6" / "plugins",
        bundle / "PySide6" / "Qt" / "plugins",
        bundle / "PySide6" / "plugins",
    ):
        if candidate.is_dir():
            return candidate
    for candidate in bundle.rglob("platforms"):
        if (candidate / "libqxcb.so").exists():
            return candidate.parent
    return None


def directory_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def slim(bundle: Path) -> int:
    plugins = find_plugin_dir(bundle)
    if plugins is None:
        print("no Qt plugin directory found - nothing to slim", file=sys.stderr)
        return 0

    freed = 0
    for name in REMOVE_DIRS:
        target = plugins / name
        if target.is_dir():
            freed += directory_size(target)
            shutil.rmtree(target)
            print(f"  removed plugins/{name}")

    platforms = plugins / "platforms"
    if platforms.is_dir():
        for lib in platforms.iterdir():
            if lib.is_file() and lib.name not in KEEP_PLATFORMS:
                freed += lib.stat().st_size
                lib.unlink()
                print(f"  removed platforms/{lib.name}")

    for marker in ("libQt6WebEngineCore.so", "libQt6Qml.so", "libQt6Quick.so"):
        for lib in bundle.rglob(marker):
            freed += lib.stat().st_size
            lib.unlink()
            print(f"  removed {lib.name}")

    # drop the Qt translations / documentation that PyInstaller copies
    for pattern in ("translations/*.qm", "*.qch"):
        for f in list((plugins.parent).rglob(Path(pattern).name)):
            if f.is_file() and f.suffix in (".qm",):
                freed += f.stat().st_size
                f.unlink()

    return freed


def main() -> int:
    bundle = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "pastypw"
    bundle = bundle.resolve()
    if not bundle.is_dir():
        print(f"error: {bundle} not found", file=sys.stderr)
        return 1

    before = directory_size(bundle)
    print(f"slimming {bundle} ({before / 1024 / 1024:.1f} MB)")
    freed = slim(bundle)
    after = directory_size(bundle)
    print(f"done: {before / 1024 / 1024:.1f} MB -> {after / 1024 / 1024:.1f} MB "
          f"(freed {freed / 1024 / 1024:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())