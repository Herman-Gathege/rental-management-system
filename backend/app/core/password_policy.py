#backend\app\core\password_policy.py
"""
Password strength policy (Sprint 7 MVP-1).

Practical subset of the guide's Module 1 rules — the ones that materially move
security without needing a wordlist file or new schema. What's included and
why:

  1. Length ≥ 10   — the single most effective control. 8 was the old floor;
                     10 pushes offline brute-force from hours to years for a
                     random password meeting the class rule below.

  2. Length ≤ 128  — prevents a bcrypt-hash-DoS. bcrypt slows quadratically
                     on very long inputs; letting anyone submit a 10MB
                     password would make hashing a request-killer.

  3. 3-of-4 classes: uppercase, lowercase, digit, symbol. NIST 800-63B
                     recommends this pattern over "all 4 required" because
                     the latter forces predictable substitutions ("P@ssw0rd!")
                     without adding entropy.

  4. Small bad list — the classics ("password", "12345678", "qwerty",
                     "letmein", "admin", "welcome"…). Anything on the list
                     is rejected regardless of whether it passes the class
                     rule (`Password1` would otherwise sneak through).

  5. No email derivative — the user's email local-part can't be the entire
                     password (Anne with email anne@x.com can't use
                     "Anne1234!!"). Cheap, catches a common weak choice.

What's deliberately NOT included, and would move to a Sprint 8 pass if we
see weak-password abuse in the wild:
  - Full top-10k common-password list (needs a shipped wordlist)
  - Dictionary-word detection
  - Password history / no-reuse rules (needs schema)

Public entry points:
  validate_password(password, email=None) -> None (raises HTTPException 400)
"""
import re
from typing import Optional

from fastapi import HTTPException


MIN_LEN = 10
MAX_LEN = 128
REQUIRED_CLASS_COUNT = 3

# A tiny, obviously-bad set. Kept small on purpose — a big blocklist belongs
# in a shipped file, not a source module. Lowercased for case-insensitive
# compare.
_BAD_PASSWORDS = {
    "password", "password1", "password123", "passw0rd",
    "12345678", "123456789", "1234567890", "1234567",
    "qwerty", "qwerty123", "qwertyui", "qwertyuiop",
    "abcdef", "abc12345", "abcdefgh",
    "letmein", "welcome", "welcome1", "welcome123",
    "admin", "administrator", "admin123", "root", "root123",
    "iloveyou", "monkey", "dragon", "master",
    "1qaz2wsx", "zaq12wsx",
    # Kenya-flavored bad picks worth catching:
    "kenya", "nairobi", "mombasa", "safaricom",
}

_UPPER_RE = re.compile(r"[A-Z]")
_LOWER_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"\d")
_SYMBOL_RE = re.compile(r"[^A-Za-z0-9]")


def _classes_matched(password: str) -> int:
    """Count how many of the 4 character classes are present."""
    return sum(
        1 for rx in (_UPPER_RE, _LOWER_RE, _DIGIT_RE, _SYMBOL_RE) if rx.search(password)
    )


def _email_local_part(email: Optional[str]) -> Optional[str]:
    if not email:
        return None
    return email.split("@", 1)[0].strip().lower() or None


def validate_password(password: str, *, email: Optional[str] = None) -> None:
    """
    Enforce the MVP password policy. Raises HTTPException(400) on failure with
    a message the frontend can show verbatim. Returns None on success.
    """
    if not isinstance(password, str) or not password:
        raise HTTPException(status_code=400, detail="Password is required.")

    if len(password) < MIN_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at least {MIN_LEN} characters.",
        )
    if len(password) > MAX_LEN:
        raise HTTPException(
            status_code=400,
            detail=f"Password must be at most {MAX_LEN} characters.",
        )

    if _classes_matched(password) < REQUIRED_CLASS_COUNT:
        raise HTTPException(
            status_code=400,
            detail=(
                "Password must include at least 3 of the following: "
                "uppercase letter, lowercase letter, digit, symbol."
            ),
        )

    lowered = password.lower()
    if lowered in _BAD_PASSWORDS:
        raise HTTPException(
            status_code=400,
            detail="This password is too common. Choose something less predictable.",
        )

    local = _email_local_part(email)
    if local and len(local) >= 3 and local in lowered:
        raise HTTPException(
            status_code=400,
            detail="Password must not contain your email address.",
        )
