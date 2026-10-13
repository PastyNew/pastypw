"""Entropy / crack-time estimation for generated passwords.

The model is intentionally conservative and simple: every character of a
password contributes ``log2(pool_size)`` bits, and an offline attacker is
assumed to be able to test ~1e10 (fast hash) or ~1e4 (slow hash) guesses per
second against a stolen database hash.

Creator: PastyNew
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .generator import PasswordOptions, pool_size

MIN_ENTROPY_BITS = 28.0
FAIR_ENTROPY_BITS = 60.0
STRONG_ENTROPY_BITS = 80.0
VERY_STRONG_ENTROPY_BITS = 100.0
EXCELLENT_ENTROPY_BITS = 120.0


class CrackScenario(IntEnum):
    """Common attacker models, in guesses per second."""

    ONLINE_THROTTLED = 100
    ONLINE_UNTHROTTLED = 10_000
    OFFLINE_SLOW_HASH = 10_000
    OFFLINE_FAST_HASH = 10_000_000_000


@dataclass(frozen=True)
class Rating:
    """Result of the strength analysis."""

    bits: float
    level: int  # 0..5, higher is better
    label_key: str
    color_key: str
    scenarios: dict[CrackScenario, float]  # seconds -> 0 means "instant"

    @property
    def percent(self) -> int:
        """0..100 position of the meter fill."""
        ceiling = EXCELLENT_ENTROPY_BITS * 1.25
        return max(2, min(100, round(self.bits / ceiling * 100)))


def entropy_bits(length: int, pool: int) -> float:
    """Bits of entropy of a random string of ``length`` chars from ``pool``."""
    if pool <= 1 or length <= 0:
        return 0.0
    return length * (pool.bit_length() and _log2(pool))


def _log2(value: float) -> float:
    import math

    return math.log2(value)


def rate_pool(bits: float) -> Rating:
    """Map a raw entropy value to a 0..5 rating."""
    scenarios = {
        scenario: 2 ** (bits - 1) / float(scenario) for scenario in CrackScenario
    }
    if bits < MIN_ENTROPY_BITS:
        level, label, color = 0, "strength.critical", "danger"
    elif bits < FAIR_ENTROPY_BITS:
        level, label, color = 1, "strength.weak", "warning"
    elif bits < STRONG_ENTROPY_BITS:
        level, label, color = 2, "strength.fair", "fair"
    elif bits < VERY_STRONG_ENTROPY_BITS:
        level, label, color = 3, "strength.strong", "good"
    elif bits < EXCELLENT_ENTROPY_BITS:
        level, label, color = 4, "strength.very_strong", "very_good"
    else:
        level, label, color = 5, "strength.excellent", "excellent"
    return Rating(
        bits=bits,
        level=level,
        label_key=label,
        color_key=color,
        scenarios=scenarios,
    )


def rate_password(password: str, options: PasswordOptions | None = None) -> Rating:
    """Analyse a concrete password.

    If ``options`` is omitted the pool is derived from the password itself,
    which slightly *overestimates* strength - pass the options used to
    generate the password for an honest measurement.
    """
    if options is not None:
        pool = pool_size(options)
    else:
        pool = _observed_pool(password)
    return rate_pool(entropy_bits(len(password), pool))


def _observed_pool(password: str) -> int:
    pool = 0
    for char in password:
        if char.isdigit():
            pool += 10
        elif char.isupper():
            pool += 26
        elif char.islower():
            pool += 26
        else:
            pool += 33
    return max(pool, 2)


def crack_time(bits: float, scenario: CrackScenario = CrackScenario.OFFLINE_FAST_HASH) -> float:
    """Seconds needed to brute-force a password with ``bits`` of entropy."""
    if bits <= 0:
        return 0.0
    return 2 ** (bits - 1) / float(scenario)