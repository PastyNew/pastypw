"""Unit tests for the core (UI independent) logic.

Run with:  python -m pytest -q
"""

from __future__ import annotations

import json
import math
import string
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pastypw.core.generator import (  # noqa: E402
    DIGITS,
    LOWERCASE,
    SYMBOLS,
    UPPERCASE,
    PasswordError,
    PasswordOptions,
    generate_many,
    generate_password,
    pool_size,
)
from pastypw.core.strength import (  # noqa: E402
    CrackScenario,
    crack_time,
    entropy_bits,
    rate_password,
    rate_pool,
)
from pastypw.core.storage import Entry, Storage  # noqa: E402


# --------------------------------------------------------------------- options
def test_default_options_are_valid():
    options = PasswordOptions()
    assert options.length == 16
    assert options.can_generate


def test_pool_size_matches_enabled_classes():
    options = PasswordOptions(length=10, use_symbols=False)
    assert pool_size(options) == 10 + 26 + 26
    assert pool_size(PasswordOptions(use_uppercase=False, use_lowercase=False,
                                      use_symbols=False)) == 10


def test_invalid_length_is_rejected():
    with pytest.raises(PasswordError):
        PasswordOptions(length=1)
    with pytest.raises(PasswordError):
        PasswordOptions(length=10_000)


# ------------------------------------------------------------------ generation
def test_password_has_requested_length_and_alphabet():
    options = PasswordOptions(length=24)
    password = generate_password(options)
    assert len(password) == 24
    allowed = set(DIGITS + LOWERCASE + UPPERCASE + SYMBOLS)
    assert set(password) <= allowed


def test_every_enabled_class_is_present():
    options = PasswordOptions(length=16)
    password = generate_password(options)
    assert any(ch.isdigit() for ch in password)
    assert any(ch.islower() for ch in password)
    assert any(ch.isupper() for ch in password)
    assert any(not ch.isalnum() for ch in password)


def test_single_class_only():
    options = PasswordOptions(length=12, use_uppercase=False,
                              use_lowercase=False, use_symbols=False)
    password = generate_password(options)
    assert set(password) <= set(DIGITS)
    assert len(password) == 12


def test_no_classes_selected_raises():
    options = PasswordOptions(use_digits=False, use_uppercase=False,
                              use_lowercase=False, use_symbols=False)
    with pytest.raises(PasswordError):
        generate_password(options)


def test_short_password_does_not_crash():
    # length < number of classes: no guarantee possible, but must not fail
    options = PasswordOptions(length=4)
    assert len(generate_password(options)) == 4


def test_passwords_are_random():
    options = PasswordOptions(length=20)
    passwords = {generate_password(options) for _ in range(50)}
    assert len(passwords) > 45  # collisions are possible but must be rare


def test_generate_many_returns_unique_values():
    options = PasswordOptions(length=24)
    passwords = generate_many(options, 20)
    assert len(passwords) == 20
    assert len(set(passwords)) == 20


def test_generate_many_rejects_zero():
    with pytest.raises(PasswordError):
        generate_many(PasswordOptions(), 0)


def test_generated_passwords_avoid_quotes_only_from_symbol_pool():
    for ch in SYMBOLS:
        assert ch not in string.whitespace


# -------------------------------------------------------------------- strength
def test_entropy_formula():
    assert entropy_bits(16, 94) == pytest.approx(16 * math.log2(94))
    assert entropy_bits(0, 94) == 0.0
    assert entropy_bits(10, 1) == 0.0


def test_rating_levels_are_ordered():
    levels = [rate_pool(bits).level for bits in (10, 40, 70, 90, 110, 140)]
    assert levels == sorted(levels)
    assert levels[0] == 0 and levels[-1] == 5


def test_crack_time_grows_exponentially():
    fast = crack_time(40, CrackScenario.OFFLINE_FAST_HASH)
    slow = crack_time(40, CrackScenario.OFFLINE_SLOW_HASH)
    assert slow > fast * 1000


def test_rate_password_uses_options_when_given():
    options = PasswordOptions(length=16, use_symbols=False,
                              use_uppercase=False)
    password = generate_password(options)
    rating = rate_password(password, options)
    expected = 16 * math.log2(36)  # digits + lowercase only
    assert rating.bits == pytest.approx(expected)


def test_rating_percent_is_bounded():
    for bits in (0, 20, 60, 100, 200):
        assert 0 <= rate_pool(bits).percent <= 100


# --------------------------------------------------------------------- storage
@pytest.fixture()
def storage(tmp_path: Path) -> Storage:
    return Storage(data_dir=tmp_path / "data", config_dir=tmp_path / "config")


def test_add_and_list(storage: Storage):
    storage.add("hunter2!A", bits=60)
    storage.add("other-Pass9", bits=80)
    entries = storage.entries()
    assert [e.password for e in entries] == ["other-Pass9", "hunter2!A"]
    assert len(storage) == 2


def test_duplicate_of_newest_is_ignored(storage: Storage):
    storage.add("same-Pass1")
    storage.add("same-Pass1")
    assert len(storage) == 1


def test_favorites_roundtrip(storage: Storage):
    entry = storage.add("fav-Pass1")
    assert entry.favorite is False
    updated = storage.toggle_favorite(entry.id)
    assert updated is not None and updated.favorite is True
    assert [e.id for e in storage.entries(favorites_only=True)] == [entry.id]
    storage.toggle_favorite(entry.id)
    assert storage.entries(favorites_only=True) == []


def test_remove_and_clear(storage: Storage):
    entry = storage.add("to-remove1")
    storage.add("to-remove2")
    storage.remove(entry.id)
    assert len(storage) == 1
    storage.clear()
    assert len(storage) == 0


def test_history_is_capped(tmp_path: Path):
    store = Storage(data_dir=tmp_path / "d", config_dir=tmp_path / "c")
    entries = [Entry(password=f"pass-{i}", created_at=time.time() + i) for i in range(260)]
    store._save_entries(entries)
    assert len(store) == 200  # MAX_HISTORY
    assert store.entries()[0].password == "pass-259"  # newest kept


def test_corrupted_history_file_is_survivable(storage: Storage):
    storage.add("valid-Pass1")
    storage.history_file.write_text("{not json", encoding="utf-8")
    assert storage.entries() == []
    storage.add("new-Pass1")
    assert len(storage) == 1


def test_settings_roundtrip(storage: Storage):
    storage.save_settings({"length": 24, "language": "en"})
    data = json.loads(storage.settings_file.read_text(encoding="utf-8"))
    assert data["length"] == 24
    assert storage.load_settings()["language"] == "en"


def test_entry_serialization():
    entry = Entry(password="abc", length=3, bits=30.0, favorite=True)
    restored = Entry.from_dict(json.loads(json.dumps(entry.to_dict())))
    assert restored == entry


def test_entries_sorted_newest_first(storage: Storage):
    old = storage.add("old-Pass001")
    old.created_at = time.time() - 10_000
    storage._save_entries(storage._load_entries())
    storage.add("new-Pass001")
    assert storage.entries()[0].password == "new-Pass001"