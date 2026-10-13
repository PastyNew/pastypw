"""Cryptographically secure password generation.

All randomness comes from :mod:`secrets` (the OS CSPRNG), never from
``random``.  Generated passwords are therefore unpredictable even if an
attacker knows the exact algorithm and length.

Creator: PastyNew
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass

DIGITS = "0123456789"
LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
UPPERCASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# Printable ASCII symbols that are safe to copy/paste everywhere.
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?/~"

MIN_LENGTH = 4
MAX_LENGTH = 256


class PasswordError(ValueError):
    """Raised when the requested options cannot produce a password."""


@dataclass(frozen=True)
class PasswordOptions:
    """Immutable description of what a password should look like."""

    length: int = 16
    use_digits: bool = True
    use_uppercase: bool = True
    use_lowercase: bool = True
    use_symbols: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.length, int):
            raise PasswordError("length must be an integer")
        if not (MIN_LENGTH <= self.length <= MAX_LENGTH):
            raise PasswordError(
                f"length must be between {MIN_LENGTH} and {MAX_LENGTH}"
            )

    @property
    def char_classes(self) -> tuple[str, ...]:
        """Character pools of every enabled class (empty ones excluded)."""
        classes = []
        if self.use_lowercase:
            classes.append(LOWERCASE)
        if self.use_uppercase:
            classes.append(UPPERCASE)
        if self.use_digits:
            classes.append(DIGITS)
        if self.use_symbols:
            classes.append(SYMBOLS)
        return tuple(classes)

    @property
    def alphabet(self) -> str:
        """Full alphabet built from the enabled classes."""
        return "".join(self.char_classes)

    @property
    def can_generate(self) -> bool:
        return bool(self.char_classes)

    @classmethod
    def from_mapping(cls, data: dict) -> "PasswordOptions":
        """Build options from a (possibly partial/foreign) mapping."""
        return cls(
            length=int(data.get("length", 16)),
            use_digits=bool(data.get("use_digits", True)),
            use_uppercase=bool(data.get("use_uppercase", True)),
            use_lowercase=bool(data.get("use_lowercase", True)),
            use_symbols=bool(data.get("use_symbols", True)),
        )


def pool_size(options: PasswordOptions) -> int:
    """Number of distinct characters the generator can produce."""
    return len(options.alphabet)


def _guaranteed_class_coverage(options: PasswordOptions) -> bool:
    """Every enabled class can be represented inside the requested length."""
    return options.length >= len(options.char_classes)


def generate_password(options: PasswordOptions) -> str:
    """Generate a single password that satisfies ``options``.

    When the length allows it, the result is guaranteed to contain at least
    one character from every enabled class (digits / lowercase / uppercase /
    symbols), and the positions are shuffled so the pattern is not obvious.
    """
    if not options.can_generate:
        raise PasswordError(
            "Select at least one character set (digits, letters or symbols)."
        )

    alphabet = options.alphabet
    length = options.length

    if _guaranteed_class_coverage(options):
        chars = [secrets.choice(cls) for cls in options.char_classes]
        chars.extend(
            secrets.choice(alphabet) for _ in range(length - len(chars))
        )
    else:
        chars = [secrets.choice(alphabet) for _ in range(length)]

    # Fisher-Yates with a CSPRNG so no predictable ordering leaks out.
    for i in range(len(chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        chars[i], chars[j] = chars[j], chars[i]
    return "".join(chars)


def generate_many(options: PasswordOptions, count: int = 1) -> list[str]:
    """Generate ``count`` unique passwords.

    Duplicates are re-rolled (up to a sane number of attempts) so that the
    batch view never shows the very same value twice.
    """
    if count < 1:
        raise PasswordError("count must be >= 1")

    results: list[str] = []
    seen: set[str] = set()
    attempts = 0
    max_attempts = max(32, count * 8)

    while len(results) < count:
        password = generate_password(options)
        attempts += 1
        if password in seen and attempts < max_attempts:
            continue
        seen.add(password)
        results.append(password)
    return results