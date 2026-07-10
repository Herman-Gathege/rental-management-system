#backend\app\services\account_lockout_service.py
"""
Account lockout (Sprint 7 MVP-1 follow-up).

Locks a user account after MAX_FAILURES=5 wrong-password login attempts.
The lock is temporary (15 minutes) and clears automatically when the
window elapses. A successful login resets the counter so a user who
typos then succeeds isn't left with strikes on their record.

State is stored on two columns of the users table:
  - failed_login_count (int, default 0)
  - locked_until       (datetime, nullable)

Not tracked in Redis: locks should survive a Redis flush. A cache miss
must not "reopen" a locked account to an attacker.

Callers (see app/api/routes/auth.py::login):
  1. is_locked() — before the password check. If True, deny with the
     same generic 400 as any other invalid attempt (no user-enumeration
     signal to the caller).
  2. record_failure() — on wrong password. Returns True iff THIS failure
     is the one that crossed the threshold; caller uses that to queue
     a one-time notification.
  3. record_success() — on successful login. Resets counter + clears
     any previously-set lock (including one that's already expired but
     hasn't been cleaned up).
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.users import User


MAX_FAILURES = 5
LOCK_DURATION_MINUTES = 15


def is_locked(user: User) -> bool:
    """True iff the user is currently inside their lockout window.

    Returns False for a lock whose window has already elapsed — the DB
    column can be stale until the next record_failure/record_success
    call cleans it up.
    """
    if user.locked_until is None:
        return False
    return user.locked_until > datetime.utcnow()


def record_failure(db: Session, user: User) -> bool:
    """Increment the failed-login counter. If it crosses MAX_FAILURES,
    set locked_until = now + LOCK_DURATION.

    Returns True iff THIS failure is the one that pushed the user over
    the threshold — the caller uses that signal to fire a one-time
    lockout notification. Repeated failures inside an existing lock
    return False so we don't spam alerts.

    Does NOT commit. Caller commits alongside its audit write so the
    two land atomically.
    """
    # Already locked: don't re-lock, don't re-notify. The lock stays a
    # fixed 15 minutes from when it was first set (not sliding).
    if is_locked(user):
        return False

    # Previous lock has already expired but was never cleared. Start
    # fresh so this failure counts as attempt #1, not attempt #6.
    if user.locked_until and user.locked_until <= datetime.utcnow():
        user.failed_login_count = 0
        user.locked_until = None

    user.failed_login_count = (user.failed_login_count or 0) + 1

    if user.failed_login_count >= MAX_FAILURES:
        user.locked_until = datetime.utcnow() + timedelta(minutes=LOCK_DURATION_MINUTES)
        return True

    return False


def record_success(db: Session, user: User) -> None:
    """Reset the failure counter and clear any lock (including expired-
    but-not-yet-cleaned ones). Does NOT commit — caller commits."""
    if user.failed_login_count or user.locked_until:
        user.failed_login_count = 0
        user.locked_until = None
