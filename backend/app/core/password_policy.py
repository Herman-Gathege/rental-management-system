#backend\app\core\password_policy.py
"""
Password strength policy (Sprint 7 MVP-1).

Practical subset of the guide's Module 1 rules — the ones that materially move
security without needing a wordlist file. What's included and why:

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

  4. Weak-password blocklist — exact-match lookup against ~80 classics
                     ("password", "12345678", "qwerty", "letmein", "admin",
                     "welcome"…) plus common first-name / sports-team /
                     pop-culture picks that show up repeatedly in breach
                     corpora. Anything on the list is rejected regardless
                     of whether it passes the class rule ("Password1"
                     would otherwise sneak through).

  5. Dominant common-word check — reject passwords where a common weak
                     word ("password", "welcome", "sunshine"…) takes up
                     50% or more of the length. Catches "Password2024!"
                     and "Sunshine123" without being over-strict on
                     "MyGardenIsGreat2024!" (garden is small % of length).

  6. No email derivative — the user's email local-part can't be the entire
                     password (Anne with email anne@x.com can't use
                     "Anne1234!!"). Cheap, catches a common weak choice.

Password history (no-reuse) is enforced separately by
app.services.password_history_service — the check runs against a database
table, so it lives outside this pure-validation module. Auth routes call
check_no_reuse() before accepting a new password.

What's still deliberately NOT included, and would move to a Sprint 8+ pass:
  - Full top-10k common-password list (needs a shipped wordlist file)
  - Leetspeak-aware detection (would catch "P4ssw0rd" — currently sneaks
    through since "password" isn't a raw substring of "p4ssw0rd")
  - Password expiry / rotation (needs a schema for last_changed_at)

Public entry points:
  validate_password(password, email=None) -> None (raises HTTPException 400)
"""
import re
from typing import Optional

from fastapi import HTTPException


MIN_LEN = 10
MAX_LEN = 128
REQUIRED_CLASS_COUNT = 3

# Threshold at which a common word inside a password is considered
# "dominant". 50% means "MyPassword123!" (password = 8/14 = 57%) is rejected
# but "MyPasswordIsStrong2024!" (password = 8/23 = 35%) is fine.
_DOMINANT_WORD_THRESHOLD = 0.5

# Exact-match blocklist. Anything here is rejected outright regardless of
# whether it passes the class rule.
# Sources: SecLists rockyou top-N, HaveIBeenPwned frequently-seen list, plus
# region-specific picks (Kenya, East Africa) unlikely to appear in generic
# lists. Kept in-source deliberately — a proper multi-thousand-entry list
# would ship as a data file loaded at startup.
_BAD_PASSWORDS = {
    # "Password" variants
    "password", "password1", "password12", "password123",
    "passw0rd", "p@ssword", "p@ssw0rd", "password!",
    # Sequential digits
    "12345678", "123456789", "1234567890", "1234567",
    "87654321", "01234567",
    # Repeated digits
    "11111111", "22222222", "00000000", "88888888",
    "111111", "222222", "000000", "666666", "999999",
    # Keyboard walks
    "qwerty", "qwerty123", "qwertyui", "qwertyuiop",
    "asdfghjkl", "zxcvbnm", "qazwsx", "asdfgh",
    "1qaz2wsx", "zaq12wsx", "1q2w3e4r", "1q2w3e4r5t",
    # Alpha sequences
    "abcdef", "abcdefg", "abcdefgh", "abc12345", "abcd1234",
    "a1b2c3d4",
    # "Let me in / welcome / admin" classics
    "letmein", "letmein1", "letmein123",
    "welcome", "welcome1", "welcome123", "welcome!",
    "admin", "administrator", "admin123", "admin!",
    "root", "root123", "rootroot",
    "changeme", "changeit", "temppass",
    # Emotion classics
    "iloveyou", "iloveyou1", "iloveyou123", "iloveu",
    "loveyou", "lovelove",
    # Fantasy / pop-culture
    "monkey", "dragon", "master", "shadow", "starwars",
    "batman", "superman", "harry", "harrypotter",
    "trustno1", "sunshine", "princess", "computer",
    # Sports
    "football", "baseball", "soccer", "basketball",
    # Common first names
    "michael", "jennifer", "jessica", "michelle", "ashley",
    "matthew", "nicholas", "anthony", "andrew",
    # Test/demo accounts
    "test1234", "demo1234", "guest123", "user1234",
    # Kenya-flavored bad picks
    "kenya", "nairobi", "mombasa", "kisumu", "eldoret",
    "safaricom", "kenyapower", "harambee", "jomokenyatta",
}

# Dominant-word substrings. If any of these appears in the password
# (case-insensitive) AND takes up ≥ _DOMINANT_WORD_THRESHOLD of the length,
# reject with a hint. All entries are ≥5 chars — shorter words would match
# too many legitimate passwords and give false positives.
#
# Some entries overlap with _BAD_PASSWORDS (e.g. "password", "kenya"). That's
# intentional: exact-match rejects the bare word, and the substring rule
# catches trivial-suffix variants like "Password2024!" or "kenya1234!".
_COMMON_WORD_SUBSTRINGS = {
    # Password-topic words that dominate weak choices
    "password", "welcome", "admin", "login", "secret", "account", "system",
    "computer", "internet", "letmein", "qwerty", "changeme",
    # Pop culture / fantasy
    "dragon", "monkey", "master", "shadow", "sunshine", "princess",
    "iloveyou", "superman", "batman", "spiderman", "starwars", "harry",
    # Sports
    "football", "baseball", "soccer", "basketball", "cricket",
    # Seasons / time
    "summer", "winter", "spring", "autumn",
    # Feelings / abstract
    "freedom", "forever", "whatever", "trustno",
    # Brands / tech
    "google", "apple", "microsoft", "amazon", "netflix",
    # Nature
    "garden", "mountain", "ocean", "rainbow",
    # Kenya-flavored
    "kenya", "nairobi", "mombasa", "safaricom", "harambee",
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


def _find_dominant_word(password: str) -> Optional[str]:
    """Return the first common word that appears in `password` and takes up
    at least _DOMINANT_WORD_THRESHOLD (50%) of its length. None if the
    password doesn't contain any dominant common word.

    Case-insensitive; matches against the curated _COMMON_WORD_SUBSTRINGS
    list. This is NOT a full-dictionary check — it only catches passwords
    that are mostly a single well-known weak word plus trivial padding.
    """
    length = len(password)
    if length == 0:
        return None
    lowered = password.lower()
    for word in _COMMON_WORD_SUBSTRINGS:
        if word in lowered and len(word) / length >= _DOMINANT_WORD_THRESHOLD:
            return word
    return None


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

    # Sprint 7 follow-up: dominant common-word check. Catches trivial
    # variants like "Password2024!" or "Sunshine123" that would pass the
    # exact-match check.
    dominant = _find_dominant_word(password)
    if dominant:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Password is too predictable — most of it is the word "
                f"'{dominant}'. Try mixing in more unrelated characters."
            ),
        )

    local = _email_local_part(email)
    if local and len(local) >= 3 and local in lowered:
        raise HTTPException(
            status_code=400,
            detail="Password must not contain your email address.",
        )