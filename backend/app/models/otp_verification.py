#backend\app\models\otp_verification.py
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class OtpVerification(Base):
    """
    One-time passcode records (Sprint 6.2 #6).

    Transient by nature: a row is created when a code is sent, updated as
    attempts are made, and stamped consumed_at once verified. Kept in its own
    table (not on users) so the same mechanism serves future OTP needs —
    password reset, tenant phone verification, etc. — via the `purpose` column.

    The code itself is never stored in plaintext: only its bcrypt hash.
    """
    __tablename__ = "otp_verifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # What this code is for. Defaults to phone verification at signup; other
    # flows (password_reset, ...) can reuse this table with a different purpose.
    purpose = Column(String, nullable=False, default="phone_verification")

    # Destination the code was sent to (the phone being verified).
    phone = Column(String, nullable=True)

    # bcrypt hash of the 6-digit code — never the code itself.
    code_hash = Column(String, nullable=False)

    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    last_sent_at = Column(DateTime, nullable=True)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
