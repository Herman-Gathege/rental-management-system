#!/usr/bin/env python
"""
Server-side landlord onboarding (white-glove setup).

Creates a complete, immediately-usable landlord account:

    user (LANDLORD)  ->  organization (owner_id)  ->  organization_member

and seeds the organisation's default expense categories, so the new owner can
log in and start working without touching the public signup flow.

Why this exists
---------------
The self-service signup (`POST /auth/register`) creates the same three rows but
leaves `phone_verified = False` and sends a WhatsApp OTP. That is the right
flow for real customers, but it requires working WhatsApp credentials, and the
account is unusable until the owner completes the OTP step. For onboarding a
known owner (e.g. AlphaOne's own portfolio) we want the account live in one
step, so this script sets `phone_verified = True`.

Everything the app writes is written here too:
  - bcrypt password hash via `hash_password` (same as the API)
  - password history row, so the first password cannot be re-used later
  - audit log entry recording who was created and when
  - default expense categories for the new organisation

Idempotency
-----------
Safe to re-run. It refuses to touch an email or organisation name that already
exists and says exactly which one collided — no silent partial writes. Use
`--dry-run` to see what it would do without changing anything.

Usage (inside the backend container)
------------------------------------
    docker compose exec backend python scripts/onboard_landlord.py \
        --org-name "Sirali Property Group" \
        --full-name "Erick Sirali" \
        --email erick@alphaone.africa \
        --phone 0712345678

The password is prompted for (never passed on the command line, so it does not
land in shell history or process listings). Pass `--generate-password` to have
one generated and printed once.
"""
from __future__ import annotations

import argparse
import getpass
import os
import secrets
import string
import sys
import uuid
from pathlib import Path

# Make `app.*` importable when run as `python scripts/onboard_landlord.py` from
# the backend root (the container's WORKDIR is /app).
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

# The app reads its configuration at import time (app/core/config.py), so the
# environment has to be in place before any `app.*` module is imported. Loading
# the repo .env here means the script also works when run outside Docker, and
# it never overrides variables Docker Compose already injected.
REQUIRED_ENV = (
    "DATABASE_URL",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "PII_ENCRYPTION_KEY",
    "PII_BLIND_INDEX_KEY",
)


def bootstrap_environment() -> list[str]:
    """Load .env if present. Returns the list of still-missing required vars."""
    try:
        from dotenv import load_dotenv

        for candidate in (BACKEND_ROOT / ".env", BACKEND_ROOT.parent / ".env"):
            if candidate.exists():
                load_dotenv(candidate, override=False)
    except ImportError:  # python-dotenv is in requirements; tolerate its absence
        pass
    return [name for name in REQUIRED_ENV if not os.getenv(name)]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a landlord account, organisation and membership.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--org-name", required=True, help="Organisation / portfolio name")
    parser.add_argument("--full-name", required=True, help="Owner's full name")
    parser.add_argument("--email", required=True, help="Owner's login email address")
    parser.add_argument(
        "--phone",
        required=True,
        help="Owner's phone in local or +254 form (stored as +2547XXXXXXXX)",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Password. Prefer the interactive prompt (omit this flag).",
    )
    parser.add_argument(
        "--generate-password",
        action="store_true",
        help="Generate a strong password and print it once.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate everything and report what would be created, then exit.",
    )
    return parser.parse_args(argv)


def normalize_phone(raw: str) -> str:
    """Normalise a Kenyan number to +2547XXXXXXXX (matches the app's rules)."""
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    if digits.startswith("0"):
        digits = "254" + digits[1:]
    elif digits.startswith("7") or digits.startswith("1"):
        digits = "254" + digits
    if not digits.startswith("254") or len(digits) != 12:
        raise ValueError(
            f"'{raw}' is not a valid Kenyan phone number. "
            "Use 0712345678 or +254712345678."
        )
    return "+" + digits


def generate_password() -> str:
    """A password that satisfies the platform policy (>=10 chars, 3 of 4 classes)."""
    alphabet = string.ascii_letters + string.digits
    body = "".join(secrets.choice(alphabet) for _ in range(14))
    return f"{body}9aA!"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    missing = bootstrap_environment()
    if missing:
        print(
            "[x] Missing required environment variables: "
            + ", ".join(missing)
            + "\n    Run this inside the backend container "
            "(docker compose exec backend ...), where the app's .env is loaded."
        )
        return 2

    # Imported lazily so `--help` and the env check work before the app (which
    # reads configuration at import time) is touched.
    from fastapi import HTTPException

    from app.core.password_policy import validate_password
    from app.core.roles import LANDLORD
    from app.core.security import hash_password
    from app.db.session import SessionLocal
    from app.models.organization import Organization
    from app.models.organization_member import OrganizationMember
    from app.models.role import Role
    from app.models.users import User
    from app.services import audit_service, password_history_service
    from app.services.checklist_seed import seed_checklist_for_org
    from app.services.expense_category_seed import seed_expense_categories_for_org

    try:
        email = args.email.strip().lower()
        phone = normalize_phone(args.phone)
    except ValueError as exc:
        print(f"[x] {exc}")
        return 2

    if "@" not in email or "." not in email.split("@")[-1]:
        print(f"[x] '{email}' is not a valid email address.")
        return 2

    # Resolve the password before touching the database.
    password = args.password
    generated = False
    if args.generate_password:
        password = generate_password()
        generated = True
    elif not password:
        try:
            password = getpass.getpass("Password for the new landlord: ")
            confirm = getpass.getpass("Confirm password: ")
        except EOFError:
            print(
                "[x] No terminal available for the password prompt.\n"
                "    Run this interactively, or pass --password '<value>' / "
                "--generate-password."
            )
            return 2
        if password != confirm:
            print("[x] Passwords do not match.")
            return 2

    try:
        validate_password(password, email=email)
    except HTTPException as exc:
        print(f"[x] Password rejected by policy: {exc.detail}")
        return 2

    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == LANDLORD).first()
        if not role:
            print(
                "[x] The LANDLORD role is missing. Start the backend once "
                "(it seeds roles) or run `python -m app.db.seed_roles`."
            )
            return 1

        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"[x] A user with {email} already exists (id {existing_user.id}).")
            print("    Use a different email, or reset that account's password instead.")
            return 1

        existing_org = (
            db.query(Organization).filter(Organization.name == args.org_name).first()
        )
        if existing_org:
            print(
                f"[x] An organisation named '{args.org_name}' already exists "
                f"(id {existing_org.id})."
            )
            print("    Pick a different --org-name, or add the owner as a member of it.")
            return 1

        if args.dry_run:
            print("[dry-run] No changes made. Would create:")
            print(f"  user       {email} ({args.full_name}, {phone})")
            print(f"  role       {LANDLORD}")
            print(f"  org        {args.org_name}")
            print(f"  membership {email} -> {args.org_name}")
            return 0

        # ── 1. Landlord user ────────────────────────────────────────────────
        password_hash = hash_password(password)
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            full_name=args.full_name.strip(),
            password_hash=password_hash,
            is_active=True,
            phone=phone,
            # Set true so the ProtectedRoute phone gate does not pin the owner
            # on /verify-phone (the gate applies to LANDLORD accounts only).
            phone_verified=True,
            role_id=role.id,
            failed_login_count=0,
        )
        db.add(user)
        db.flush()

        # Record the initial password so password_history can reject re-use.
        password_history_service.record(db, user.id, password_hash)

        # ── 2. Organisation owned by that user ──────────────────────────────
        org = Organization(
            id=str(uuid.uuid4()),
            name=args.org_name.strip(),
            owner_id=user.id,
        )
        db.add(org)
        db.flush()

        # ── 3. Membership carrying the LANDLORD role ────────────────────────
        db.add(
            OrganizationMember(
                id=str(uuid.uuid4()),
                user_id=user.id,
                organization_id=org.id,
                role_id=role.id,
            )
        )

        # ── 4. Defaults the app would otherwise create on first use ─────────
        categories = seed_expense_categories_for_org(db, org.id)
        checklist_items = seed_checklist_for_org(db, org.id)

        audit_service.log_action(
            db=db,
            organization_id=org.id,
            user_id=user.id,
            action="create",
            entity_type="organization",
            entity_id=org.id,
            description=f"Organisation and landlord account provisioned for {email}",
            new_values={
                "org_name": org.name,
                "owner_email": email,
                "role": LANDLORD,
                "source": "scripts/onboard_landlord.py",
            },
        )

        db.commit()

        print()
        print("=" * 68)
        print("LANDLORD ONBOARDED")
        print("=" * 68)
        print(f"Organisation   : {org.name}")
        print(f"Org ID         : {org.id}")
        print(f"Owner          : {user.full_name} <{user.email}>")
        print(f"User ID        : {user.id}")
        print(f"Phone          : {user.phone} (verified)")
        print(f"Role           : {LANDLORD}")
        print(f"Expense cats   : {categories} seeded")
        print(f"Checklist items: {checklist_items} seeded")
        if generated:
            print("-" * 68)
            print(f"Password       : {password}")
            print("Copy this now and share it securely — it is not stored in")
            print("plain text anywhere and cannot be shown again.")
        print("=" * 68)
        print("Next: sign in with this email + password. The landlord lands on")
        print("/dashboard, then continues onboarding in the app (add properties,")
        print("units, tenants, leases, and invite team members from Team).")
        print("=" * 68)
        return 0

    except Exception as exc:  # noqa: BLE001 - CLI must report, not traceback
        db.rollback()
        print(f"[x] Failed and rolled back: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
