#backend\app\db\types.py
"""
SQLAlchemy custom column types (Sprint 7 MVP-1).

EncryptedString: a TypeDecorator that wraps String. Values are encrypted on
write and decrypted on read, so the rest of the code can treat `tenant.phone`
as a plain string — the encryption is invisible above this layer.

Usage in a model:
    from app.db.types import EncryptedString
    phone = Column(EncryptedString, nullable=False)

Notes:
  - Fernet ciphertext is base64 urlsafe, ~100 bytes for typical inputs. We
    back it with plain String (unbounded) rather than a fixed length; Postgres
    stores TEXT for that which handles the growth without waste.
  - Blind-index hash columns aren't a TypeDecorator — they're a separate hex
    String column populated by SQLAlchemy event listeners on the model. Keeps
    the plumbing where it can be seen.
"""
from sqlalchemy.types import String, TypeDecorator

from app.core.encryption import decrypt_value, encrypt_value


class EncryptedString(TypeDecorator):
    """
    Fernet-encrypted string column. Reads decrypt, writes encrypt. None passes
    through as SQL NULL, empty string as empty string (see encryption module
    for why).

    cache_ok=True tells SQLAlchemy this type is safe to cache in statement
    compilation — it is, because encryption behavior is stateless from the
    ORM's perspective.
    """
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        # Called when writing to the DB (INSERT/UPDATE).
        return encrypt_value(value)

    def process_result_value(self, value, dialect):
        # Called when reading from the DB.
        return decrypt_value(value)
