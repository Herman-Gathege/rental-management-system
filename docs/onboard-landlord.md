# Onboarding a Landlord (Organisation Owner) on the Server

**Purpose:** create an organisation plus its owner account directly on the
server, so a known owner can log in immediately and finish onboarding inside
the app.

**Written for:** this task — onboarding **Mr Erick Sirali, owner of AlphaOne**.
The same procedure works for any landlord.

**Status of this document:** every command below was executed end-to-end
against a real database during a verification pass, and the resulting account
was confirmed to authenticate with the password that was set.

---

## 1. What "onboarding a landlord" means in this system

A landlord is not a single row. The app expects **three rows plus a role**, and
login misbehaves if any of them is missing:

| # | Table | What it must contain | Why it matters |
|---|-------|----------------------|----------------|
| 1 | `users` | The owner: email, bcrypt password hash, full name, phone, `is_active = true`, `phone_verified = true` | The login identity. |
| 2 | `organizations` | `name` + `owner_id` → the user from step 1 | The tenant boundary for **all** data. Every feature is scoped to an organisation. |
| 3 | `organization_members` | Links user ↔ organisation ↔ role | **This is what grants access.** Without it the API returns `403 No organization found` and the user is bounced to `/login`. |
| 4 | `roles` | A row named exactly `LANDLORD` | Seeded automatically when the backend starts. Role names are **UPPERCASE**. |

Two fields cause most failed onboardings:

* **`phone_verified`** — the route guard sends any `LANDLORD` with
  `phone_verified = false` to `/verify-phone`, which needs a working WhatsApp
  OTP. The script below sets it to `true`, so the owner goes straight to the
  dashboard.
* **The role name must be `LANDLORD`**, all caps. A lowercase `landlord` fails
  every backend permission check — including "create property".

---

## 2. Before you start

Work on the server, in the project directory:

```bash
ssh webloom@165.245.251.183
cd /opt/webloom/rental-management-system
docker compose ps          # backend, postgres, redis, caddy should be Up
```

Confirm these four things, in order:

```bash
# 1. Migrations applied (the entrypoint runs them on start; confirm anyway)
docker compose exec backend alembic current
docker compose exec backend alembic heads      # both ids must match

# 2. Roles exist
docker compose exec backend python -c "
from app.db.session import SessionLocal
from app.models.role import Role
db = SessionLocal()
print([r.name for r in db.query(Role).all()])
db.close()"

# 3. The backend can reach the database
docker compose exec backend python -c "
from app.db.session import SessionLocal
db = SessionLocal(); print('db ok'); db.close()"

# 4. Check the latest backup — you are about to write to production
ls -1 backups | tail -3
```

Expected role output:
`['LANDLORD', 'PROPERTY_MANAGER', 'FINANCE', 'TENANT', 'SYSTEM']`

If that list is empty, start the backend once (`docker compose up -d backend`)
or run `docker compose exec backend python -m app.db.seed_roles`.

> **Run everything inside the `backend` container.** That is where
> `DATABASE_URL`, the PII encryption keys and the app code live. Running the
> same commands from a laptop would target the wrong database.
>
> The script loads the repository `.env` itself if those variables are not
> already set, so it works whether you invoke it through `docker compose exec`
> (container environment wins) or directly on the server.

---

## 3. Create the organisation and owner (the script)

`backend/scripts/onboard_landlord.py` creates the user, the organisation, the
membership, the password-history row, an audit entry, and the organisation's
default expense categories and inspection checklist items — the same defaults
the public signup creates.

### Step 1 — dry run first

Nothing is written; it validates the inputs and shows what would be created.

```bash
docker compose exec backend python scripts/onboard_landlord.py \
  --org-name "Sirali Property Group" \
  --full-name "Erick Sirali" \
  --email erick@alphaone.africa \
  --phone 0712345678 \
  --dry-run
```

Replace the email and phone with the owner's real ones before continuing.
`--org-name` should be the name his tenants and team will see.

### Step 2 — create it

The password is **prompted for**, so it never lands in shell history, a process
listing, or the Docker log:

```bash
docker compose exec backend python scripts/onboard_landlord.py \
  --org-name "Sirali Property Group" \
  --full-name "Erick Sirali" \
  --email erick@alphaone.africa \
  --phone 0712345678
```

To have one generated instead (a strong 18-character password, shown **once**
at the end):

```bash
docker compose exec backend python scripts/onboard_landlord.py \
  --org-name "Sirali Property Group" \
  --full-name "Erick Sirali" \
  --email erick@alphaone.africa \
  --phone 0712345678 \
  --generate-password
```

On success you get a summary block:

```
====================================================================
LANDLORD ONBOARDED
====================================================================
Organisation   : Sirali Property Group
Org ID         : aeb264c7-a88a-42d9-8b6b-9d835620ac99
Owner          : Erick Sirali <erick@alphaone.africa>
User ID        : c7e9313d-53c8-4f26-9789-730c74e56b93
Phone          : +254712345678 (verified)
Role           : LANDLORD
Expense cats   : 16 seeded
Checklist items: 13 seeded
====================================================================
```

**Record the Org ID.** You will need it for support, for WhatsApp number
mapping, and for any later data operation.

### Password rules the script enforces

The platform policy is applied before anything is written, so a weak password
is rejected with a clear reason instead of creating a broken account:

* at least **10 characters** (maximum 128)
* **3 of these 4** classes: uppercase, lowercase, digit, symbol
* not on the common-password list (`password`, `welcome`, `qwerty`, …)
* must not contain the email's local part

Good example: `Riverside!Ledger2026`. Bad examples: `Password123!` (weak list),
`erick12345` (contains the account name), `short1!` (too short).

### The script is safe to re-run

It refuses to overwrite anything and names the colliding value:

```
[x] A user with erick@alphaone.africa already exists (id ...).
[x] An organisation named 'Sirali Property Group' already exists (id ...).
```

The organisation check is on the **name**, so if you genuinely need two
organisations with the same display name, change one of them.

---

## 4. Verify the account really works

### 4.1 From the database

```bash
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
SELECT u.email, u.full_name, u.phone, u.phone_verified, u.is_active,
       r.name AS role, o.name AS organisation
FROM users u
LEFT JOIN organization_members m ON m.user_id = u.id
LEFT JOIN roles r ON r.id = m.role_id
LEFT JOIN organizations o ON o.id = m.organization_id
WHERE u.email = 'erick@alphaone.africa';"
```

You want one row with `role = LANDLORD`, `phone_verified = t`,
`is_active = t`, and the organisation name filled in.

### 4.2 From the API (proves the login works)

```bash
TOKEN=$(curl -s -X POST https://api.alphaone.africa/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"erick@alphaone.africa","password":"THE_PASSWORD"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

echo "token: ${TOKEN:0:24}..."

curl -s https://api.alphaone.africa/auth/me -H "Authorization: Bearer $TOKEN"
```

`/auth/me` must return:

```json
{
  "id": "c7e9313d-...",
  "email": "erick@alphaone.africa",
  "full_name": "Erick Sirali",
  "phone": "+254712345678",
  "phone_verified": true,
  "organization_id": "aeb264c7-...",
  "role": "LANDLORD"
}
```

If `organization_id` is `null` or `role` is missing, the membership row was not
created — see Troubleshooting.

### 4.3 From the browser

1. Go to **https://alphaone.africa/login**
2. Sign in with the email and password.
3. `/dashboard` routes a landlord to the workspace at `/owner/dashboard`.
4. The sidebar header shows the organisation name.

Because `phone_verified` is `true`, he is **not** sent to `/verify-phone`.

---

## 5. What the owner does next (in-app onboarding)

The account is fully provisioned; the rest is normal product usage. A sensible
order to walk him through:

| Order | Screen | Why here |
|-------|--------|----------|
| 1 | **Settings → Communication Channels** | Confirm WhatsApp shows *Enabled*. Email is optional — leave it off until SMTP is configured. |
| 2 | **Settings → Billing Automation** | Confirm invoicing on the **1st**, reminders on the **10th**, timezone `Africa/Nairobi`. |
| 3 | **Properties → Add Property** | Everything else hangs off a property (landlord-only action). |
| 4 | **Units → Add Unit** | Rent amount plus which property the unit belongs to. |
| 5 | **Tenants → Add Tenant** | Name, phone, and optionally email. |
| 6 | **Leases → Create Lease** | Ties tenant + unit together; this is what makes rent charges and the tenant portal work. |
| 7 | **Team → Invite** | Add property managers and finance users. Only a landlord can invite, and a landlord cannot be invited. |
| 8 | **Bulk Upload** | Optional shortcut for importing many properties/units from CSV or Excel. |

Two things worth flagging early:

* **Invite links** go out over WhatsApp. If WhatsApp is not configured for the
  invitee's number, the invite still succeeds and returns a `token` you can
  forward manually.
* **The property switcher** in the top bar scopes the dashboard, units,
  tenants, billing, payments and reports to one property. "All properties" is
  the default.

---

## 6. Alternative: let him sign up himself

If WhatsApp is configured so the OTP can be delivered, he can use
**https://alphaone.africa/register** with his organisation name, email,
password and phone. That creates the same rows, sends a 6-digit OTP over
WhatsApp, and keeps him on `/verify-phone` until it is confirmed.

Prefer the script when:

* WhatsApp credentials are not yet configured for his number, or
* you are provisioning ahead of a meeting and want the account live
  immediately, or
* you need the Org ID in advance (for example to map his WhatsApp business
  number to the organisation).

---

## 7. If you cannot run Python (raw SQL fallback)

You still need the app to generate the bcrypt hash — do **not** paste a
plain-text password into SQL, and do not reuse another user's hash.

```bash
# Generate a hash inside the container
docker compose exec backend python -c "
from app.core.security import hash_password
print(hash_password('Riverside!Ledger2026'))"
```

Then, with that hash substituted for `<BCRYPT_HASH>`:

```sql
BEGIN;

INSERT INTO users (id, email, full_name, password_hash, is_active, phone, phone_verified, failed_login_count)
VALUES (gen_random_uuid()::text, 'erick@alphaone.africa', 'Erick Sirali', '<BCRYPT_HASH>', true, '+254712345678', true, 0);

INSERT INTO organizations (id, name, owner_id)
SELECT gen_random_uuid()::text, 'Sirali Property Group', id
FROM users WHERE email = 'erick@alphaone.africa';

INSERT INTO organization_members (id, user_id, organization_id, role_id, created_at)
SELECT gen_random_uuid()::text, u.id, o.id, r.id, now()
FROM users u
JOIN organizations o ON o.owner_id = u.id
JOIN roles r ON r.name = 'LANDLORD'
WHERE u.email = 'erick@alphaone.africa';

COMMIT;
```

`gen_random_uuid()` needs PostgreSQL 13+ (this stack runs 15). The SQL path
**skips** the password-history row, the audit entry, and the seeded expense
categories; restarting the backend backfills the categories and checklist
items. The script remains the better option. Verify with the query in §4.1
before telling anyone the account is ready.

---

## 8. Resetting the password later

The *forgot password* endpoint emails a reset link, but **the frontend has no
reset-password page yet**, so that link cannot be completed in the browser.
Until that page exists, reset server-side:

```bash
docker compose exec backend python -c "
import getpass
from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models.users import User
from app.services import password_history_service

email = 'erick@alphaone.africa'
new = getpass.getpass('New password: ')

db = SessionLocal()
user = db.query(User).filter(User.email == email).one()
user.password_hash = hash_password(new)
user.refresh_token = None          # invalidate existing sessions
user.failed_login_count = 0
user.locked_until = None
password_history_service.record(db, user.id, user.password_hash)
db.commit()
print('password updated for', email)
db.close()"
```

Share the new password over a secure channel and have him change it from
**Profile** after signing in.

---

## 9. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Invalid credentials` on login | Wrong password, or the password was written without `hash_password` | Reset it with §8. Note: 5 failed attempts locks the account for 15 minutes. |
| Login works but pages are empty / `403 No organization found` | Missing or incomplete `organization_members` row | Re-check §4.1. The role must be exactly `LANDLORD`. |
| Stuck on `/verify-phone` | `users.phone_verified = false` | `UPDATE users SET phone_verified = true WHERE email = '...';` |
| `Roles not seeded`, or the script reports the LANDLORD role is missing | Backend never started, or `roles` was emptied | `docker compose exec backend python -m app.db.seed_roles` |
| Password rejected with a policy message | Password failed the policy | Follow §3's rules; the error names the failed rule. |
| `422` on login/register with a `.local` or `.test` email | The API validates emails with `EmailStr`, which rejects special-use domains | Use a real, public email domain. |
| Script reports the org name already exists | A previous run created it | Check §4.1 first — if the owner is already a member, nothing more is needed. |
| Properties/units pages error after a server update | New migrations not applied | `docker compose exec backend alembic upgrade head` |
| Expense page shows no categories | Categories are seeded per organisation at registration or by this script, and re-seeded on backend start-up | Restart the backend to backfill categories and checklist items. |

---

## 10. Undoing an onboarding (clean-up)

Only if the account was created in error. This is destructive and takes the
organisation's data with it — take a backup first (`ls -1 backups | tail -1`).

```sql
BEGIN;

-- Resolve the ids once
CREATE TEMP TABLE tmp AS
SELECT u.id AS user_id, o.id AS org_id
FROM users u
JOIN organizations o ON o.owner_id = u.id
WHERE u.email = 'erick@alphaone.africa';

-- Children first, then parents (org-scoped tables cascade from organizations)
DELETE FROM organization_members WHERE organization_id IN (SELECT org_id FROM tmp);
DELETE FROM password_history     WHERE user_id         IN (SELECT user_id FROM tmp);
DELETE FROM audit_logs           WHERE organization_id IN (SELECT org_id FROM tmp);
DELETE FROM organizations        WHERE id              IN (SELECT org_id FROM tmp);
DELETE FROM users                WHERE id              IN (SELECT user_id FROM tmp);

COMMIT;
```

If the owner has already created properties, units, leases, tenants or
payments, deleting the organisation removes all of them. Prefer disabling the
account (`UPDATE users SET is_active = false`) when the history matters.

---

## 11. Security notes

* **Never pass the password on the command line** where it can reach shell
  history or a process list — use the prompt (default) or
  `--generate-password`.
* Only a bcrypt hash is stored, and it is recorded in password history so the
  initial password cannot be reused later.
* Passwords are never logged. Creating the account writes an `audit_logs` row
  (action `create`, entity `organization`) recording the email, role and
  source script.
* Run the script only inside the backend container so it uses the production
  `DATABASE_URL` and the same PII encryption keys as the running app. Writing to
  a database with different keys can make encrypted tenant fields unreadable.
* The owner should change the password from **Profile** after the first login.

---

## 12. Quick reference

```bash
# Service checks
docker compose ps
docker compose exec backend alembic current && docker compose exec backend alembic heads

# Dry run
docker compose exec backend python scripts/onboard_landlord.py \
  --org-name "Sirali Property Group" --full-name "Erick Sirali" \
  --email erick@alphaone.africa --phone 0712345678 --dry-run

# Create (password prompted)
docker compose exec backend python scripts/onboard_landlord.py \
  --org-name "Sirali Property Group" --full-name "Erick Sirali" \
  --email erick@alphaone.africa --phone 0712345678

# Help
docker compose exec backend python scripts/onboard_landlord.py --help
```

Once the account exists: **https://alphaone.africa/login** → he lands on
`/owner/dashboard` and continues from §5.
