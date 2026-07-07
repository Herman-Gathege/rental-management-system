#backend\app\services\otp_service.py
"""
OTP service (Sprint 6.2 #6) — phone verification via WhatsApp.

Flow:
  generate_and_send()  create/refresh an OTP row, send the code over WhatsApp
  verify()             check a submitted code (expiry + attempt limit)

Security:
  - Codes are 6 random digits, stored ONLY as a bcrypt hash.
  - 10-minute expiry.
  - Max 5 attempts per code, then the user must request a new one.
  - 60-second resend throttle to prevent WhatsApp spam / cost abuse.

The code is sent as a free-form WhatsApp message (dev mode). In production this
would move to a Meta-approved template; send_freeform_message is the same helper
the invite/notification flows use.
"""
import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.otp_verification import OtpVerification
from app.models.users import User
from app.services.messaging import send_freeform_message

CODE_TTL_MINUTES = 10
MAX_ATTEMPTS = 5
RESEND_COOLDOWN_SECONDS = 60
DEFAULT_PURPOSE = "phone_verification"


def _generate_code() -> str:
    """A cryptographically-random 6-digit code (zero-padded)."""
    return f"{secrets.randbelow(1_000_000):06d}"


def _active_otp(db: Session, user_id: str, purpose: str) -> OtpVerification | None:
    """Most recent unconsumed OTP for this user+purpose, if any."""
    return (
        db.query(OtpVerification)
        .filter(
            OtpVerification.user_id == user_id,
            OtpVerification.purpose == purpose,
            OtpVerification.consumed_at.is_(None),
        )
        .order_by(OtpVerification.created_at.desc())
        .first()
    )


def generate_and_send(
    db: Session,
    user: User,
    *,
    organization_id: str,
    phone: str,
    purpose: str = DEFAULT_PURPOSE,
    enforce_cooldown: bool = True,
):
    """
    Create (or replace) an OTP for this user and send it via WhatsApp.

    Reuses a single active row per user+purpose: each send overwrites the code
    hash, resets attempts, and pushes out the expiry — so a resend invalidates
    the previous code. Caller is responsible for db.commit().
    """
    if not phone:
        raise HTTPException(status_code=400, detail="A phone number is required to send a verification code.")

    now = datetime.utcnow()
    otp = _active_otp(db, user.id, purpose)

    # Resend throttle.
    if otp and enforce_cooldown and otp.last_sent_at:
        elapsed = (now - otp.last_sent_at).total_seconds()
        if elapsed < RESEND_COOLDOWN_SECONDS:
            wait = int(RESEND_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {wait} seconds before requesting another code.",
            )

    code = _generate_code()

    if otp is None:
        otp = OtpVerification(user_id=user.id, purpose=purpose)
        db.add(otp)

    otp.phone = phone
    otp.code_hash = hash_password(code)
    otp.expires_at = now + timedelta(minutes=CODE_TTL_MINUTES)
    otp.attempts = 0
    otp.last_sent_at = now
    otp.consumed_at = None

    # Send over WhatsApp (free-form, dev mode). Best-effort: the message row
    # records failures; we surface a soft note rather than blocking signup.
    body = (
        f"Your verification code is {code}. "
        f"It expires in {CODE_TTL_MINUTES} minutes. "
        f"If you didn't request this, ignore this message."
    )
    send_freeform_message(
        db=db,
        organization_id=organization_id,
        phone_number=phone,
        body=body,
        triggered_by_user_id=user.id,
        message_type="otp",
    )

    db.flush()
    return otp


def verify(
    db: Session,
    user: User,
    *,
    code: str,
    purpose: str = DEFAULT_PURPOSE,
) -> bool:
    """
    Verify a submitted code. On success, marks the OTP consumed and sets
    user.phone_verified = True. Raises HTTP 400 with a clear reason otherwise.
    Caller is responsible for db.commit().
    """
    code = (code or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Enter the verification code.")

    otp = _active_otp(db, user.id, purpose)
    if otp is None:
        raise HTTPException(status_code=400, detail="No verification code found. Request a new one.")

    now = datetime.utcnow()
    if otp.expires_at < now:
        raise HTTPException(status_code=400, detail="This code has expired. Request a new one.")

    if otp.attempts >= MAX_ATTEMPTS:
        raise HTTPException(
            status_code=400,
            detail="Too many incorrect attempts. Request a new code.",
        )

    if not verify_password(code, otp.code_hash):
        otp.attempts += 1
        remaining = MAX_ATTEMPTS - otp.attempts
        db.flush()
        if remaining <= 0:
            raise HTTPException(
                status_code=400,
                detail="Incorrect code. Too many attempts — request a new code.",
            )
        raise HTTPException(
            status_code=400,
            detail=f"Incorrect code. {remaining} attempt(s) remaining.",
        )

    # Success.
    otp.consumed_at = now
    if purpose == DEFAULT_PURPOSE:
        user.phone_verified = True
    db.flush()
    return True
