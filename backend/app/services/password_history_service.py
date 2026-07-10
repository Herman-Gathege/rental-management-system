#backend\app\services\password_history_service.py
"""
Password history — enforces "don't reuse recent passwords" (Sprint 7 MVP-1).

Two public functions:

  check_no_reuse(db, user_id, new_password)
      Raises HTTPException(400) if new_password matches any of the user's
      last KEEP_LAST stored bcrypt hashes. No-op if the user has no history
      yet (first-time password set).

  record(db, user_id, password_hash)
      Adds a new hash to the user's history and prunes older rows so only
      the last KEEP_LAST remain. Called every time a password is set —
      register, change-password, reset-password, invite acceptance.
      Caller is responsible for db.commit(); we only add + delete on the
      session.

Design notes:
  - Reuse detection runs verify_password() against each stored hash. bcrypt
    is intentionally slow (~100ms), so at KEEP_LAST=5 the whole loop is
    ~half a second — acceptable for a password-change interaction.
  - We store bcrypt hashes, NOT plaintext or a weaker hash. That way the
    history table has no more risk than the users table itself.
  - KEEP_LAST=5 follows NIST 800-63B guidance ("at least the previous 5").
    Bump higher for stricter compliance frameworks; 5 balances user
    memorability against cycling attacks.
"""
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.password_history import PasswordHistory
from app.core.security import verify_password


KEEP_LAST = 5


def check_no_reuse(db: Session, user_id: str, new_password: str) -> None:
    """Raise HTTPException(400) if new_password matches any of the user's
    last KEEP_LAST stored password hashes."""
    history = (
        db.query(PasswordHistory)
        .filter(PasswordHistory.user_id == user_id)
        .order_by(PasswordHistory.created_at.desc())
        .limit(KEEP_LAST)
        .all()
    )
    for entry in history:
        try:
            matches = verify_password(new_password, entry.password_hash)
        except Exception:
            # A corrupted stored hash shouldn't block the user; skip it.
            continue
        if matches:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"This password was used recently. Please choose one you "
                    f"haven't used in your last {KEEP_LAST} passwords."
                ),
            )


def record(db: Session, user_id: str, password_hash: str) -> None:
    """Append a new password hash to the user's history and prune older
    entries so only KEEP_LAST remain. Does NOT commit — caller commits
    alongside the user's password change so the two writes are atomic."""
    entry = PasswordHistory(
        id=str(uuid.uuid4()),
        user_id=user_id,
        password_hash=password_hash,
    )
    db.add(entry)
    db.flush()

    # Prune anything beyond KEEP_LAST for this user. Query the ids of the
    # newest KEEP_LAST rows, then delete everything else. bulk-delete uses
    # synchronize_session=False because we're not going to touch the deleted
    # rows again in this session — they're gone.
    keep_rows = (
        db.query(PasswordHistory.id)
        .filter(PasswordHistory.user_id == user_id)
        .order_by(PasswordHistory.created_at.desc())
        .limit(KEEP_LAST)
        .all()
    )
    ids_to_keep = [row[0] for row in keep_rows]
    if ids_to_keep:
        (
            db.query(PasswordHistory)
            .filter(
                PasswordHistory.user_id == user_id,
                ~PasswordHistory.id.in_(ids_to_keep),
            )
            .delete(synchronize_session=False)
        )
