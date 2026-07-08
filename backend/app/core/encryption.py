#backend\app\core\encryption.py
"""
PII encryption + blind indexes (Sprint 7 MVP-1).

Application-level encryption of sensitive tenant fields. Uses Fernet
(AES-128-CBC + HMAC-SHA256 authenticated encryption from the `cryptography`
library) for the encrypted payloads. Uses a separate HMAC-SHA256 with its own
key for blind indexes — deterministic hashes stored alongside encrypted
columns so we can still enforce uniqueness and do exact-match lookups.

Two env vars must be set:
  PII_ENCRYPTION_KEY   — Fernet key (base64 urlsafe, 32 bytes when decoded).
                         Generate with Fernet.generate_key().decode().
  PII_BLIND_INDEX_KEY  — hex string, 64 chars (32 bytes) for HMAC.
                         Generate with secrets.token_hex(32).

The two keys are SEPARATE by design. If the blind-index key alone were
compromised, an attacker could do a dictionary attack against the hashes
("hash '0712345678' and see if it matches any row") but couldn't decrypt
anything. If the Fernet key alone were compromised, an attacker with a DB
dump could decrypt everything but couldn't precompute hashes to search for
specific values without also having the blind-index key. Layered.

The module refuses to import if the keys aren't set — that's intentional. A
missing key is a "you'll silently corrupt data on next write" bug, so failing
loud at startup is the right behavior.
"""
import hashlib
import hmac
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


class MissingEncryptionKeyError(RuntimeError):
    """Raised at module import when PII_ENCRYPTION_KEY / PII_BLIND_INDEX_KEY
    aren't set. Failing here means the backend won't start rather than start
    and corrupt data on the next write."""


def _require_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise MissingEncryptionKeyError(
            f"{name} is not set. PII encryption cannot function without it. "
            f"Add it to your .env file (see app/core/encryption.py docstring)."
        )
    return v


_FERNET_KEY = _require_env("PII_ENCRYPTION_KEY").encode()
_BLIND_INDEX_KEY = bytes.fromhex(_require_env("PII_BLIND_INDEX_KEY"))

# One Fernet instance for the whole process. Thread-safe.
_fernet = Fernet(_FERNET_KEY)


def encrypt_value(plaintext: Optional[str]) -> Optional[str]:
    """
    Encrypt a string with Fernet. Returns the token as a str (Fernet outputs
    base64 urlsafe bytes; we decode so SQLAlchemy stores a normal TEXT value).

    None and empty strings pass through unchanged — encrypting empty strings
    is wasteful and using None for absent values keeps the DB semantics clean.
    """
    if plaintext is None:
        return None
    if plaintext == "":
        return ""
    if not isinstance(plaintext, str):
        plaintext = str(plaintext)
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: Optional[str]) -> Optional[str]:
    """
    Decrypt a Fernet token. Returns the plaintext string.

    Passes None/empty through unchanged (mirror of encrypt_value). If the
    ciphertext isn't a valid Fernet token — e.g. a legacy plaintext value
    that predates the migration — we return it AS-IS rather than crashing.
    That's a pragmatic choice: it lets the app keep working during the
    in-place migration window when some rows are encrypted and some aren't.
    Once the migration is done the fallback path never fires.
    """
    if ciphertext is None:
        return None
    if ciphertext == "":
        return ""
    if not isinstance(ciphertext, str):
        ciphertext = str(ciphertext)
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        # Not a valid token — assume it's legacy plaintext and return as-is.
        # This path should not fire once the migration completes.
        return ciphertext


def blind_index(value: Optional[str]) -> Optional[str]:
    """
    Deterministic HMAC-SHA256 of a normalized value. Same input always produces
    the same hash, so we can store this alongside the encrypted column and use
    it for uniqueness checks and exact-match lookups.

    Normalization:
      - None/empty → None (no hash stored for blanks)
      - stripped of surrounding whitespace
      - lowercased (so 'Anne@X.com' and 'anne@x.com' collide as intended;
                    phones/IDs are typically ASCII already so lowercasing is a
                    no-op for them but harmless)

    Output is a 64-char hex string.
    """
    if value is None:
        return None
    v = str(value).strip().lower()
    if not v:
        return None
    return hmac.new(_BLIND_INDEX_KEY, v.encode(), hashlib.sha256).hexdigest()
