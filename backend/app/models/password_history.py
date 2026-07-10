#backend\app\models\password_history.py
"""
Password history (Sprint 7 MVP-1 follow-up).

One row per previous password hash per user. Written whenever a user sets a
new password (via /auth/register, /auth/change-password, /auth/reset-password,
or /organizations/register-invite). Older rows beyond KEEP_LAST are pruned
at write time by password_history_service.record().

Stores bcrypt hashes (same format as users.password_hash) — never plaintext.
Reuse check compares a candidate password against each stored hash via
verify_password(); a match blocks the change with a 400.

Foreign key uses ondelete=CASCADE so deleting a user also drops their
history (they can't come back to a reused-password check).
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey

from app.db.base import Base


class PasswordHistory(Base):
    __tablename__ = "password_history"

    id = Column(String, primary_key=True)
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
