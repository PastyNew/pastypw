#!/usr/bin/env python3
"""Build a Debian/Ubuntu/Kali package (.deb) for PastyNew Password Generator.

Requires ``dpkg-deb`` (present on every Debian-family system) and a PyInstaller
build in ``dist/pastypw`` (see ``make linux-binary``).

    python scripts/build_deb.py --version 1.0.0
"""

from __future__ import annotations

import argparse
import gzip
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pastypw import AUTHOR, HOMEPAGE, __version__  # noqa: E402

PACKAGE = "pastypw"
MAINTAINER = f"{AUTHOR} <pastypew@gmail.com>"
SECTION = "utils"
PRIORITY = "optional"
LICENSE = "MIT"
HOMEPAGE_URL = HOMEPAGE

# Runtime libraries Qt6 needs on any glibc distribution.
RUNTIME_DEPS = [
    "libc6",
    "libglib2.0-0",
    "libegl1",
    "libgl1",
    "libfontconfig1",
    "libdbus-1-3",
    "libx11-6",
    "libx11-xcb1",
    "libxcb1",
    "libxcb-cursor0",
    "libxcb-glx0",
    "libxcb-icccm4",
    "libxcb-image0",
    "libxcb-keysyms1",
    "libxcb-randr0",
    "libxcb-render-util0",
    "libxcb-shape0",
    "libxcb-sync1",
    "libxcb-xfixes0",
    "libxcb-xinerama0",
    "libxcb-xkb1",
    "libxkbcommon-x11-0",
    "libxkbcommon0",
]

SHORT_DESCRIPTION = "Offline password generator with a modern dark interface"
LONG_DESCRIPTION = """PastyNew Password Generator is a small, fast and completely offline password
generator with a modern dark interface.

Features:
 * cryptographically secure randomness (OS CSPRNG via Python secrets)
 * length from 4 to 64 characters, digits / letters / symbols on demand
 * batch generation of up to 50 unique passwords at once
 * entropy and crack-time estimate for every password
 * local history with favourites and export to .txt
 * Russian and English interface, no network access, no telemetry

The interface, the sources and the packaging scripts are written by PastyNew.
"""


def description_lines(text: str) -> str:
    """Format an extended description the way dpkg-deb expects it."""
    out = []
    for line in text.rstrip("\n").split("\n"):
        out.append(" ." if not line.strip() else f" {line}")
    return "\n".join(out) + "\n"


def host_arch() -> str:
    try:
        out = subprocess.run(
            ["dpkg", "--print-architecture"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except Exception:  # pragma: no cover - fallback for odd hosts
        import platform

        machine = platform.machine()
        return {"x86_64": "amd64", "aarch64": "arm64"}.get(machine, "amd64")


def write(path: Path, content: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(mode)


def build_payload(stage: Path, binary_dir: Path) -> int:
    """Copy the PyInstaller bundle into /usr/lib/pastypw."""
    target = stage / "usr" / "lib" / PACKAGE
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(binary_dir, target)

    installed = 0
    for item in stage.rglob("*"):
        if item.is_file():
            installed += item.stat().st_size
            if item.is_file() and (
                item.suffix in ("", ".so") or os_is_executable(item)
            ):
                item.chmod(0o755)
    return installed // 1024


def os_is_executable(path: Path) -> bool:
    import os

    return os.access(path, os.X_OK)


def build(version: str, arch: str, binary_dir: Path, output: Path) -> Path:
    stage = ROOT / "build" / "deb" / f"{PACKAGE}_{version}_{arch}"
    if stage.exists():
        shutil.rmtree(stage)

    installed_kb = build_payload(stage, binary_dir)

    # launcher
    write(
        stage / "usr" / "bin" / PACKAGE,
        "#!/bin/sh\n"
        "# PastyNew Password Generator launcher\n"
        f'exec "/usr/lib/{PACKAGE}/{PACKAGE}" "$@"\n',
        mode=0o755,
    )

    # desktop entry + icon
    apps = stage / "usr" / "share" / "applications"
    apps.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "packaging" / "desktop" / "pastypw.desktop",
                 apps / "pastypw.desktop")
    icons_src = ROOT / "build" / "icons"
    for size in (16, 32, 48, 64, 128, 256, 512):
        source = icons_src / f"pastypw-{size}.png"
        if source.exists():
            dest = stage / "usr" / "share" / "icons" / "hicolor" / f"{size}x{size}" / "apps"
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest / "pastypw.png")
    if (icons_src / "pastypw.svg").exists():
        dest = stage / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(icons_src / "pastypw.svg", dest / "pastypw.svg")

    # documentation
    doc = stage / "usr" / "share" / "doc" / PACKAGE
    doc.mkdir(parents=True, exist_ok=True)
    for name in ("README.md", "README.en.md", "LICENSE", "CHANGELOG.md"):
        source = ROOT / name
        if source.exists():
            shutil.copy2(source, doc / name)
    (doc / "copyright").write_text(
        f"Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/\n"
        f"Upstream-Name: {PACKAGE}\nSource: {HOMEPAGE_URL}\n\n"
        f"Files: *\nCopyright: 2026 {AUTHOR}\nLicense: MIT\n\n"
        "License: MIT\n    Permission is hereby granted, free of charge, to any person\n"
        "    obtaining a copy of this software and associated documentation files\n"
        "    (the \"Software\"), to deal in the Software without restriction.\n\n"
        "    THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND.\n",
        encoding="utf-8",
    )
    changelog = (
        f"{PACKAGE} ({version}-1) unstable; urgency=medium\n\n"
        f"  * Release {version} by {AUTHOR}.\n\n"
        f" -- {AUTHOR} <pastypew@gmail.com>  Tue, 13 Oct 2026 12:00:00 +0300\n"
    )
    raw = changelog.encode("utf-8")
    (doc / "changelog.Debian.gz").write_bytes(gzip.compress(raw))

    # control file
    control = stage / "DEBIAN" / "control"
    write(
        control,
        f"Package: {PACKAGE}\n"
        f"Version: {version}-1\n"
        f"Section: {SECTION}\n"
        f"Priority: {PRIORITY}\n"
        f"Architecture: {arch}\n"
        f"Installed-Size: {installed_kb}\n"
        f"Maintainer: {MAINTAINER}\n"
        f"Homepage: {HOMEPAGE_URL}\n"
        "Depends: " + ", ".join(RUNTIME_DEPS) + "\n"
        f"Description: {SHORT_DESCRIPTION}\n"
        + description_lines(LONG_DESCRIPTION),
    )

    # maintainer scripts
    write(
        stage / "DEBIAN" / "postinst",
        "#!/bin/sh\nset -e\n"
        'case "$1" in\n'
        "  configure)\n"
        "    if command -v update-desktop-database >/dev/null 2>&1; then\n"
        "      update-desktop-database -q /usr/share/applications || true\n"
        "    fi\n"
        "    if command -v gtk-update-icon-cache >/dev/null 2>&1; then\n"
        "      gtk-update-icon-cache -q -f -t /usr/share/icons/hicolor || true\n"
        "    fi\n"
        "    ;;\n"
        "esac\nexit 0\n",
        mode=0o755,
    )
    write(
        stage / "DEBIAN" / "prerm",
        "#!/bin/sh\nset -e\n"
        'case "$1" in\n'
        "  remove|upgrade|deconfigure)\n"
        "    ;;\n"
        "esac\nexit 0\n",
        mode=0o755,
    )
    write(
        stage / "DEBIAN" / "postrm",
        "#!/bin/sh\nset -e\n"
        'case "$1" in\n'
        "  remove|purge)\n"
        "    if command -v update-desktop-database >/dev/null 2>&1; then\n"
        "      update-desktop-database -q /usr/share/applications || true\n"
        "    fi\n"
        "    if command -v gtk-update-icon-cache >/dev/null 2>&1; then\n"
        "      gtk-update-icon-cache -q -f -t /usr/share/icons/hicolor || true\n"
        "    fi\n"
        "    ;;\n"
        "esac\nexit 0\n",
        mode=0o755,
    )

    # build
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    subprocess.run(
        ["dpkg-deb", "--root-owner-group", "--build", str(stage), str(output)],
        check=True,
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the .deb package")
    parser.add_argument("--version", default=__version__)
    parser.add_argument("--arch", default="")
    parser.add_argument("--binary-dir", default=str(ROOT / "dist" / "pastypw"))
    parser.add_argument("--output", default=str(ROOT / "dist"))
    args = parser.parse_args()

    binary_dir = Path(args.binary_dir).resolve()
    if not (binary_dir / PACKAGE).exists():
        print(f"error: {binary_dir / PACKAGE} not found - run PyInstaller first",
              file=sys.stderr)
        return 1

    arch = args.arch or host_arch()
    output = Path(args.output).resolve() / f"{PACKAGE}_{args.version}_{arch}.deb"
    path = build(args.version, arch, binary_dir, output)
    size_mb = path.stat().st_size / (1024 * 1024)
    print(f"OK: {path.relative_to(ROOT)} ({size_mb:.1f} MB)")
    print(f"    install: sudo dpkg -i {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())