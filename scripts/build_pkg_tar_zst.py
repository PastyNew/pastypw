#!/usr/bin/env python3
"""Build a pacman package (``.pkg.tar.zst``) without makepkg.

``makepkg`` only exists on Arch, so on any other Linux host this script builds
the very same archive format by hand: a zstd-compressed tar containing
``.PKGINFO``, ``.MTREE`` and the ``usr/`` tree, which is exactly what pacman
expects from ``pacman -U``.

    python scripts/build_pkg_tar_zst.py

On Arch the canonical path is still ``./scripts/build_arch_pkg.sh`` (makepkg).
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pastypw import AUTHOR, HOMEPAGE, __version__  # noqa: E402
from pastypw.core.generator import SYMBOLS  # noqa: E402

PKGNAME = "pastypw"

DEPENDS = [
    "glibc",
    "glib2",
    "fontconfig",
    "dbus",
    "xorg-libxcb",
    "xcb-util-wm",
    "xcb-util-image",
    "xcb-util-keysyms",
    "xcb-util-renderutil",
    "xcb-util-shape",
    "xcb-util-xinerama",
    "xcb-util-cursor",
    "libxkbcommon",
    "libxkbcommon-x11",
    "xorg-xwayland",
]

OPTDEPENDS = [
    "wl-clipboard: copy passwords on Wayland",
]

ICON_SIZES = (16, 32, 48, 64, 128, 256, 512)


# --------------------------------------------------------------------- helpers
def stage_pkgroot(binary_dir: Path, icons_dir: Path, pkgroot: Path) -> int:
    """Lay out the /usr tree exactly like the PKGBUILD does."""
    if pkgroot.exists():
        shutil.rmtree(pkgroot)

    shutil.copytree(binary_dir, pkgroot / "usr" / "lib" / PKGNAME)

    launcher = pkgroot / "usr" / "bin" / PKGNAME
    launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.write_text(
        "#!/bin/sh\n"
        "# PastyNew Password Generator (packaged for Arch Linux)\n"
        f'exec "/usr/lib/{PKGNAME}/{PKGNAME}" "$@"\n',
        encoding="utf-8",
    )
    launcher.chmod(0o755)

    desktop = pkgroot / "usr" / "share" / "applications" / f"{PKGNAME}.desktop"
    desktop.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "packaging" / "desktop" / f"{PKGNAME}.desktop", desktop)

    for size in ICON_SIZES:
        source = icons_dir / f"{PKGNAME}-{size}.png"
        if source.exists():
            target = (
                pkgroot / "usr" / "share" / "icons" / "hicolor"
                / f"{size}x{size}" / "apps" / f"{PKGNAME}.png"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    svg = icons_dir / f"{PKGNAME}.svg"
    if svg.exists():
        target = (
            pkgroot / "usr" / "share" / "icons" / "hicolor" / "scalable" / "apps"
            / f"{PKGNAME}.svg"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(svg, target)

    for name, destination in (
        ("README.md", f"usr/share/doc/{PKGNAME}/README.md"),
        ("README.en.md", f"usr/share/doc/{PKGNAME}/README.en.md"),
        ("LICENSE", f"usr/share/licenses/{PKGNAME}/LICENSE"),
        ("CHANGELOG.md", f"usr/share/doc/{PKGNAME}/CHANGELOG.md"),
    ):
        source = ROOT / name
        if source.exists():
            target = pkgroot / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    normalize_permissions(pkgroot)
    return sum(f.stat().st_size for f in pkgroot.rglob("*") if f.is_file())


def normalize_permissions(pkgroot: Path) -> None:
    """Pacman expects 755 directories and world-readable files."""
    for item in sorted(pkgroot.rglob("*"), reverse=True):
        if item.is_symlink():
            continue
        if item.is_dir():
            item.chmod(0o755)
        elif os.access(item, os.X_OK):
            item.chmod(0o755)
        else:
            item.chmod(0o644)
    pkgroot.chmod(0o755)


def build_pkginfo(arch: str, installed_size: int) -> str:
    description = (
        "Offline password generator with a modern dark interface. "
        "Cryptographically secure (OS CSPRNG), batch generation, strength "
        f"estimate, local history and an RU/EN interface. Symbols: {SYMBOLS} "
        "Created by PastyNew."
    )
    lines = [
        f"pkgname = {PKGNAME}",
        f"pkgbase = {PKGNAME}",
        f"pkgver = {__version__}-1",
        f"pkgdesc = {description}",
        f"url = {HOMEPAGE}",
        f"builddate = {int(time.time())}",
        f"packager = {AUTHOR} <pastypew@gmail.com>",
        f"size = {installed_size}",
        f"arch = {arch}",
        "license = MIT",
        "xdata = NONE",
        "provides = pastypw",
    ]
    lines += [f"depend = {name}" for name in DEPENDS]
    lines += [f"optdepend = {name}" for name in OPTDEPENDS]
    return "\n".join(lines) + "\n"


def build_mtree(pkgroot: Path) -> bytes:
    """alpm/BSD mtree description (gzip compressed, like makepkg does)."""
    lines = ["#mtree"]

    def digest(path: Path) -> tuple[str, str]:
        md5 = hashlib.md5()
        sha256 = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                md5.update(chunk)
                sha256.update(chunk)
        return md5.hexdigest(), sha256.hexdigest()

    def mode_of(path: Path) -> int:
        return stat.S_IMODE(path.lstat().st_mode)

    for item in sorted(pkgroot.rglob("*")):
        if item.is_symlink():
            relative = "./" + str(item.relative_to(pkgroot))
            lines.append(
                f"{relative} type=link uid=0 gid=0 mode=777 "
                f"link={os.readlink(item)}"
            )
            continue
        relative = "./" + str(item.relative_to(pkgroot))
        mode = mode_of(item)
        if item.is_dir():
            lines.append(f"{relative} type=dir uid=0 gid=0 mode={mode:o}")
            continue
        st = item.stat()
        md5, sha256 = digest(item)
        kind = "file" if stat.S_ISREG(st.st_mode) else "link"
        lines.append(
            f"{relative} type={kind} uid=0 gid=0 mode={mode:o} "
            f"time={int(st.st_mtime)}.0 size={st.st_size} "
            f"md5digest={md5} sha256digest={sha256}"
        )

    raw = ("\n".join(lines) + "\n").encode("utf-8")
    return gzip.compress(raw, mtime=0)


def add_bytes(archive: tarfile.TarFile, name: str, data: bytes, mode: int) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = mode
    info.mtime = int(time.time())
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    info.type = tarfile.REGTYPE
    archive.addfile(info, io.BytesIO(data))


def create_package(pkgroot: Path, pkginfo: str, mtree: bytes, output: Path) -> Path:
    """Write the .pkg.tar.zst archive (tar first, zstd via the zstd binary)."""
    tar_path = output.parent / (output.name[: -len(".zst")] if output.name.endswith(".zst")
                                else output.name + ".tar")
    try:
        with tarfile.open(tar_path, "w", format=tarfile.GNU_FORMAT) as archive:
            add_bytes(archive, ".PKGINFO", pkginfo.encode("utf-8"), 0o644)
            add_bytes(archive, ".MTREE", mtree, 0o644)

            for item in sorted(pkgroot.rglob("*")):
                relative = str(item.relative_to(pkgroot))
                info = archive.gettarinfo(str(item), arcname=relative)
                info.uid = info.gid = 0
                info.uname = info.gname = "root"
                if item.is_file() and not item.is_symlink():
                    with item.open("rb") as handle:
                        archive.addfile(info, handle)
                else:
                    archive.addfile(info)

        if output.exists():
            output.unlink()
        if shutil.which("zstd") is None:
            raise SystemExit(
                "error: the 'zstd' command is required "
                "(Debian/Ubuntu: sudo apt install zstd)"
            )
        subprocess.run(
            ["zstd", "-19", "-q", "-f", str(tar_path), "-o", str(output)],
            check=True,
        )
    finally:
        tar_path.unlink(missing_ok=True)
    return output


# ------------------------------------------------------------------- main flow
def main() -> int:
    parser = argparse.ArgumentParser(description="Build the .pkg.tar.zst package")
    parser.add_argument("--binary-dir", default=str(ROOT / "dist" / PKGNAME))
    parser.add_argument("--icons", default=str(ROOT / "build" / "icons"))
    parser.add_argument("--output", default=str(ROOT / "dist"))
    args = parser.parse_args()

    binary_dir = Path(args.binary_dir).resolve()
    if not (binary_dir / PKGNAME).exists():
        print(f"error: {binary_dir / PKGNAME} not found - run PyInstaller first",
              file=sys.stderr)
        return 1

    arch = {"x86_64": "x86_64", "aarch64": "aarch64"}.get(os.uname().machine, "x86_64")
    pkgroot = ROOT / "build" / "pkg" / "pkgroot"

    print(">> staging the package tree")
    installed_size = stage_pkgroot(binary_dir, Path(args.icons).resolve(), pkgroot)

    print(">> writing .PKGINFO and .MTREE")
    pkginfo = build_pkginfo(arch, installed_size)
    mtree = build_mtree(pkgroot)

    print(">> creating the archive")
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    name = f"{PKGNAME}-{__version__}-1-{arch}.pkg.tar.zst"
    output = output_dir / name
    create_package(pkgroot, pkginfo, mtree, output)

    print(f"OK: {output.relative_to(ROOT)} "
          f"({output.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"    install: sudo pacman -U {name}")
    print("    verify:  tar --zstd -tf " + name + " | head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())