"""Persistence of history, favourites and window settings.

Everything is stored locally as plain JSON inside the XDG base directories:

    ~/.config/pastypw/settings.json      -- last used options / language
    ~/.local/share/pastypw/history.json  -- generated password log

No network access, no telemetry.  The history file is *not* encrypted (see
README, "Безопасность"), keep it on an encrypted disk if that matters to you.

Creator: PastyNew
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator

APP_DIR = "pastypw"
MAX_HISTORY = 200


def _xdg_dir(env_var: str, fallback: str) -> Path:
    raw = os.environ.get(env_var)
    base = Path(raw).expanduser() if raw else Path.home() / fallback
    path = base / APP_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass
class Entry:
    """One generated password kept in the local log."""

    password: str
    created_at: float = field(default_factory=time.time)
    length: int = 0
    bits: float = 0.0
    favorite: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Entry":
        return cls(
            password=str(data.get("password", "")),
            created_at=float(data.get("created_at", 0.0)),
            length=int(data.get("length", 0)),
            bits=float(data.get("bits", 0.0)),
            favorite=bool(data.get("favorite", False)),
            id=str(data.get("id") or uuid.uuid4().hex[:12]),
        )


class Storage:
    """Tiny JSON-backed store, safe to use from the UI thread (tiny files)."""

    def __init__(self, data_dir: Path | None = None, config_dir: Path | None = None) -> None:
        self.data_dir = data_dir or _xdg_dir("XDG_DATA_HOME", ".local/share")
        self.config_dir = config_dir or _xdg_dir("XDG_CONFIG_HOME", ".config")
        self.history_file = self.data_dir / "history.json"
        self.settings_file = self.config_dir / "settings.json"

    # ------------------------------------------------------------------ util
    @staticmethod
    def _read_json(path: Path) -> Any:
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        """Atomic write: temp file in the same dir + ``os.replace``."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
            os.replace(tmp_name, path)
        except OSError:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    # --------------------------------------------------------------- history
    def _load_entries(self) -> list[Entry]:
        raw = self._read_json(self.history_file) or []
        if not isinstance(raw, list):
            return []
        entries: list[Entry] = []
        for item in raw:
            if isinstance(item, dict) and item.get("password"):
                entries.append(Entry.from_dict(item))
        entries.sort(key=lambda e: e.created_at, reverse=True)
        return entries

    def _save_entries(self, entries: list[Entry]) -> None:
        ordered = sorted(entries, key=lambda e: e.created_at, reverse=True)
        payload = [e.to_dict() for e in ordered[:MAX_HISTORY]]
        self._write_json(self.history_file, payload)

    def add(self, password: str, *, bits: float = 0.0, save: bool = True) -> Entry:
        """Append a password to the history (skipping the newest duplicate)."""
        entries = self._load_entries()
        if entries and entries[0].password == password and not entries[0].favorite:
            return entries[0]
        entry = Entry(password=password, length=len(password), bits=round(bits, 1))
        entries.insert(0, entry)
        if save:
            self._save_entries(entries)
        return entry

    def entries(self, *, favorites_only: bool = False) -> list[Entry]:
        entries = self._load_entries()
        if favorites_only:
            return [e for e in entries if e.favorite]
        return entries

    def find(self, entry_id: str) -> Entry | None:
        for entry in self._load_entries():
            if entry.id == entry_id:
                return entry
        return None

    def toggle_favorite(self, entry_id: str) -> Entry | None:
        entries = self._load_entries()
        for entry in entries:
            if entry.id == entry_id:
                entry.favorite = not entry.favorite
                self._save_entries(entries)
                return entry
        return None

    def remove(self, entry_id: str) -> None:
        entries = [e for e in self._load_entries() if e.id != entry_id]
        self._save_entries(entries)

    def clear(self, *, favorites_only: bool = False) -> None:
        if favorites_only:
            self._save_entries([e for e in self._load_entries() if e.favorite])
        else:
            self._save_entries([])

    def __iter__(self) -> Iterator[Entry]:
        return iter(self._load_entries())

    def __len__(self) -> int:
        return len(self._load_entries())

    # -------------------------------------------------------------- settings
    def load_settings(self) -> dict[str, Any]:
        data = self._read_json(self.settings_file)
        return data if isinstance(data, dict) else {}

    def save_settings(self, settings: dict[str, Any]) -> None:
        self._write_json(self.settings_file, settings)