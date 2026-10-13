"""Core (UI-independent) logic of PastyNew password generator.

Modules:
    generator -- cryptographically secure password generation
    strength  -- entropy calculation and crack-time estimation
    storage   -- history / favourites / settings persistence (JSON, XDG paths)

Creator: PastyNew
"""

from .generator import (
    DIGITS,
    LOWERCASE,
    SYMBOLS,
    UPPERCASE,
    PasswordOptions,
    PasswordError,
    generate_many,
    generate_password,
    pool_size,
)
from .strength import (
    CrackScenario,
    Rating,
    crack_time,
    entropy_bits,
    rate_password,
    rate_pool,
)
from .storage import Entry, Storage

__all__ = [
    "DIGITS",
    "LOWERCASE",
    "SYMBOLS",
    "UPPERCASE",
    "CrackScenario",
    "Entry",
    "PasswordError",
    "PasswordOptions",
    "Rating",
    "Storage",
    "crack_time",
    "entropy_bits",
    "generate_many",
    "generate_password",
    "pool_size",
    "rate_password",
    "rate_pool",
]