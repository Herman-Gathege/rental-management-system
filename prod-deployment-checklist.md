# Production Deployment Checklist — Rental SaaS System

**Deploying:** WhatsApp environment-aware routing + M-Pesa parser + batch upload deposit-first split
**Branch:** `tenant/deposit-first-payment` (or whichever you commit to)
**Prod:** alphaone.africa

## Current deployment state

- WhatsApp currently runs in **Meta sandbox** (`WHATSAPP_ENV=sandbox`).
- Production routing architecture is implemented: `phone_number_id → WhatsAppIntegration → organization_id`.
- Database migration `f8a1b2c3d4e5` and WhatsApp integration seeding still require deployment verification.
- Automated tests: 123 passed, 1 warning (pre-existing SQLAlchemy FK cycle advisory).

## Pre-production vs production (WhatsApp)

| Aspect | Sandbox | Production |
|--------|---------|------------|
| `WHATSAPP_ENV` | `sandbox` | `production` |
| Credentials | Meta sandbox/test number | Live Meta Business number |
| Organization routing | DB lookup → `WHATSAPP_DEFAULT_ORG_ID` fallback | DB lookup only (`whatsapp_integrations`) |
| Unknown `phone_number_id` | Falls back to default org (if set) | Rejected for inbound; status updates still processed |
| `WHATSAPP_DEFAULT_ORG_ID` | Allowed as fallback | NOT used for routing |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | Optional | Required |
| Webhook signature | Skipped if `WHATSAPP_APP_SECRET` absent | MUST be present and validated |
| `whatsapp_integrations` row | Optional (fallback covers missing row) | MUST exist before enabling traffic |

## Do not do this

- Do not hardcode an organization ID in webhook code. Routing must go through `resolve_organization()`.
- Do not use `WHATSAPP_DEFAULT_ORG_ID` for production routing. It is a sandbox development aid only.
- Do not copy sandbox Meta credentials into production `.env` or secrets.
- Do not store raw Meta access tokens, app secrets, or encryption keys in the `whatsapp_integrations` table.
- Do not skip the database backup in Phase 1.
- Do not downgrade production migrations casually. Inspect first, prefer forward migration.
- Do not expose secrets in logs. `settings.whatsapp.describe()` returns booleans for presence, not values.
- Do not enable production WhatsApp traffic before a production `WhatsAppIntegration` row exists for the production `phone_number_id`.
- Do not change `WHATSAPP_ENV=production` and assume the system is production-ready. Production requires a DB-routed SaaS architecture, not an env-var single-org setup.

**Ground rules:**
- All commands assume you're SSHed into the prod host and inside the project directory.
- If your prod container names differ (e.g. `rental_backend` vs `alphaone_backend`), swap accordingly.
- Adjust `rental_user` / `rental_db` if prod credentials differ.
- Work through phases top-to-bottom. Don't skip Phase 1 backup no matter how confident you are.
- If ANYTHING in Phase 3 fails, stop and rollback (Phase 12) before continuing.

---

## Phase 1 — Before you deploy

### 1.1 Take a database backup
```bash
docker exec rental_postgres pg_dump -U rental_user rental_db > backup_before_deploy_$(date +%Y%m%d_%H%M%S).sql
ls -lh backup_before_deploy_*.sql
```
- [ ] Backup file exists and is > 1KB

### 1.2 Note current commit (your rollback target)
```bash
git log --oneline -1 > rollback_commit.txt
cat rollback_commit.txt
```
- [ ] Rollback commit hash noted

### 1.3 Confirm your fix is on origin
Run on your **local** machine first:
```bash
git log origin/tenant/deposit-first-payment --oneline -5
```
- [ ] Your commits appear (WhatsApp routing + parser fix + deposit split)

### 1.4 Confirm WhatsApp environment intent
- [ ] Confirm the intended `WHATSAPP_ENV` value for this deployment (`sandbox` or `production`).
- [ ] Confirm this is NOT a production deployment if `WHATSAPP_ENV=sandbox`.
- [ ] Confirm this IS a full production promotion if `WHATSAPP_ENV=production`.

### 1.5 Confirm environment-specific Meta credentials
- [ ] Sandbox: confirm sandbox `phone_number_id`, `business_account_id`, `access_token`, `app_secret`, and `webhook_verify_token` are available.
- [ ] Production: confirm production `phone_number_id`, `business_account_id`, `access_token`, `app_secret`, and `webhook_verify_token` are available **separately** from sandbox.
- [ ] Confirm production is NOT using sandbox IDs or tokens.

### 1.6 Confirm secrets injection path
- [ ] Confirm secrets are injected through environment variables / secrets management (not hardcoded).
- [ ] Confirm `.env` is in `.gitignore` and not committed.

---

## Phase 2 — Deploy

### 2.1 Pull the fix on prod
```bash
git fetch origin
git checkout tenant/deposit-first-payment
git pull origin tenant/deposit-first-payment
git log --oneline -3
```
- [ ] Latest commits are on prod's working tree

### 2.2 Run migrations
```bash
docker compose run --rm backend alembic upgrade head
```
- [ ] Migrations complete without error
- [ ] Migration `f8a1b2c3d4e5` (adds `whatsapp_integrations` table) applies successfully
- [ ] If output says "Target database is not up to date" earlier — that's fine, it just means it applied pending ones

### 2.3 Verify `whatsapp_integrations` table exists
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "\dt whatsapp_integrations"
```
- [ ] Table listed

### 2.4 Verify table schema (optional but recommended)
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "\d whatsapp_integrations"
```
- [ ] Columns present: `id`, `organization_id`, `meta_phone_number_id`, `meta_business_account_id`, `environment`, `is_active`, `created_at`, `updated_at`
- [ ] Unique constraint `uniq_whatsapp_integrations_env_phone_number` on `(environment, meta_phone_number_id)`

### 2.5 Rebuild and restart
```bash
docker compose build backend frontend
docker compose up -d backend frontend
```
- [ ] Build completes without error
- [ ] `docker compose up` returns quickly

---

## Phase 3 — Post-deploy sanity

### 3.1 Containers healthy
```bash
docker compose ps
```
- [ ] `rental_backend` shows `Up X seconds (healthy)` — not restarting
- [ ] `rental_frontend` shows `Up`
- [ ] `rental_postgres` shows `Up (healthy)`

### 3.2 Backend logs clean
```bash
docker logs rental_backend --tail 80
```
- [ ] FastAPI startup message visible
- [ ] No import errors, no exception tracebacks
- [ ] No "column does not exist" errors

### 3.3 WhatsApp startup validation visible
```bash
docker logs rental_backend --tail 20 | grep -i "whatsapp"
```
- [ ] Log line shows `WhatsApp environment: sandbox` **OR** `WhatsApp environment: production`
- [ ] Log line shows `WhatsApp configuration: valid`
- [ ] If `INVALID` appears, the specific errors are listed — fix before proceeding

### 3.4 Verify configuration is valid (no secrets in logs)
- [ ] `settings.whatsapp.describe()` output (if logged) shows booleans for token/secret presence, not values
- [ ] No access tokens, app secrets, or database passwords appear in `docker logs`

### 3.5 payment_review_items table exists
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "\dt payment_review_items"
```
- [ ] Table listed

### 3.6 Deployed commit matches expectation
```bash
git log --oneline -1
```
- [ ] Matches what you pulled in step 2.1

### 3.7 Login works
- [ ] Open alphaone.africa in browser
- [ ] Landlord login succeeds
- [ ] Dashboard loads

**STOP HERE if any of Phase 3 fails. Go to Phase 12 (rollback).**

---

## Phase 4 — WhatsApp environment verification

### 4A. SANDBOX verification

**Expected:** `WHATSAPP_ENV=sandbox`

```bash
docker exec rental_backend printenv WHATSAPP_ENV
```
- [ ] Output is `sandbox`

#### 4A.1 Sandbox credentials present
```bash
docker exec rental_backend printenv WHATSAPP_PHONE_NUMBER_ID
docker exec rental_backend printenv WHATSAPP_BUSINESS_ACCOUNT_ID
docker exec rental_backend printenv WHATSAPP_ACCESS_TOKEN
docker exec rental_backend printenv WHATSAPP_APP_SECRET
docker exec rental_backend printenv WHATSAPP_WEBHOOK_VERIFY_TOKEN
```
- [ ] All sandbox credentials are non-empty
- [ ] Values are NOT production credentials

#### 4A.2 Sandbox integration row
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c \
  "SELECT id, environment, meta_phone_number_id, meta_business_account_id, organization_id, is_active, created_at FROM whatsapp_integrations WHERE environment='sandbox' ORDER BY created_at;"
```
- [ ] At least one row exists with `environment='sandbox'`
- [ ] `meta_phone_number_id` matches the current sandbox phone number ID
- [ ] `is_active` is `true`

#### 4A.3 Sandbox fallback org (if configured)
```bash
docker exec rental_backend printenv WHATSAPP_DEFAULT_ORG_ID
```
- [ ] If set, confirm the fallback organization exists and is intended for sandbox use
- [ ] If not set, confirm the sandbox `WhatsAppIntegration` row maps the `phone_number_id` to the correct organization

#### 4A.4 Tenant belongs to mapped organization
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c \
  "SELECT t.id, t.full_name, t.phone_number, t.organization_id FROM tenants t WHERE t.organization_id = '<SANDBOX_ORG_UUID>' LIMIT 5;"
```
- [ ] Test tenant belongs to the same organization as the sandbox integration row

### 4B. PRODUCTION verification

**Expected:** `WHATSAPP_ENV=production`

```bash
docker exec rental_backend printenv WHATSAPP_ENV
```
- [ ] Output is `production`

#### 4B.1 Production credentials present
```bash
docker exec rental_backend printenv WHATSAPP_PHONE_NUMBER_ID
docker exec rental_backend printenv WHATSAPP_BUSINESS_ACCOUNT_ID
docker exec rental_backend printenv WHATSAPP_ACCESS_TOKEN
docker exec rental_backend printenv WHATSAPP_APP_SECRET
docker exec rental_backend printenv WHATSAPP_WEBHOOK_VERIFY_TOKEN
```
- [ ] All production credentials are non-empty
- [ ] Values are NOT sandbox credentials

#### 4B.2 Production integration row exists
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c \
  "SELECT id, environment, meta_phone_number_id, meta_business_account_id, organization_id, is_active, created_at FROM whatsapp_integrations WHERE environment='production' ORDER BY created_at;"
```
- [ ] At least one row exists with `environment='production'`
- [ ] `meta_phone_number_id` matches the production phone number ID
- [ ] `is_active` is `true`

#### 4B.3 Production organization mapping correct
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c \
  "SELECT id, name FROM organizations WHERE id = '<PRODUCTION_ORG_UUID>';"
```
- [ ] Production organization exists
- [ ] `whatsapp_integrations.organization_id` matches this organization

#### 4B.4 No reliance on `WHATSAPP_DEFAULT_ORG_ID`
```bash
docker exec rental_backend printenv WHATSAPP_DEFAULT_ORG_ID
```
- [ ] Either unset/empty, or if set, explicitly documented as unused for production routing
- [ ] Production routing must resolve from `whatsapp_integrations` table only

#### 4B.5 Production rejects unknown `phone_number_id`
- [ ] Backend logs confirm: unknown production `phone_number_id` events are logged as errors and ignored for inbound routing
- [ ] Status updates are still processed for unknown numbers (org-agnostic)

---

## Phase 5 — Webhook verification

### 5.1 GET verification handshake
```bash
curl -s "http://alphaone.africa/webhooks/whatsapp?hub.mode=subscribe&hub.challenge=test123&hub.verify_token=<SANDBOX_OR_PROD_VERIFY_TOKEN>"
```
- [ ] Returns raw `test123` when verify token matches
- [ ] Returns `403` when verify token does not match

### 5.2 POST webhook signature validation
- [ ] `WHATSAPP_APP_SECRET` is configured in the target environment
- [ ] Production: `X-Hub-Signature-256` validation is active (no development bypass)
- [ ] Invalid or missing signature returns `401`
- [ ] Valid signature passes through to event processing

### 5.3 Verify no development bypass in production
```bash
docker logs rental_backend --tail 50 | grep -i "skipping signature verification"
```
- [ ] This warning MUST NOT appear in production logs

---

## Phase 6 — WhatsApp inbound path

You're testing whether a forwarded M-Pesa SMS becomes a `PaymentReviewItem` with the tenant correctly linked through the new organization resolver.

### 6.1 Send a fresh test message
Use a real tenant's WhatsApp phone. Pick a NEW reference (Meta dedups on message ID; the code also dedups on reference — reusing an old ref will silently skip):

```
TESTREF001 Confirmed. Ksh20,000.00 sent to LANDLORD NAME for account 0100316372900 on 22/8/26 at 8:30 AM. New M-PESA balance is Ksh1,240.00. Transaction cost, Ksh0.00.
```

- [ ] Message sent from tenant's phone to Meta Business number

### 6.2 Confirm the raw message was received
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT phone_number, LEFT(content, 100) AS preview, created_at FROM messages WHERE channel='whatsapp' AND direction='incoming' AND created_at > NOW() - INTERVAL '10 minutes' ORDER BY created_at DESC LIMIT 3;"
```
- [ ] Row exists with your test message content
- [ ] `phone_number` is the tenant's phone in E.164 format (`+254...`)

If NO row exists → webhook isn't reaching prod. Check Caddy logs and Meta webhook config. Stop here and diagnose.

### 6.3 Confirm the `phone_number_id` routing resolved correctly
```bash
docker logs rental_backend --tail 100 | grep -i "resolve_organization"
```
- [ ] Log shows `phone_number_id '<SANDBOX_OR_PROD_PHONE_NUMBER_ID>' → organization <ORG_UUID>`
- [ ] For sandbox: log may show `SANDBOX FALLBACK` if no integration row exists
- [ ] For production: log must show DB resolution, NOT sandbox fallback

### 6.4 Confirm the PaymentReviewItem was created
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT reference, amount, tenant_id IS NOT NULL AS has_tenant, source, status, flag_reason, created_at FROM payment_review_items WHERE created_at > NOW() - INTERVAL '10 minutes' ORDER BY created_at DESC LIMIT 3;"
```
- [ ] Row exists with `reference='TESTREF001'`, `amount=20000`, `source='whatsapp'`, `status='pending_review'`
- [ ] `has_tenant = t` (this is critical — if `f`, phone-format bug hit us)

### 6.5 If `has_tenant = f`, fix the tenant's phone
```bash
# Find the tenant
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT id, full_name FROM tenants WHERE organization_id = '<ORG_UUID>';"
```
Then via the UI, edit the tenant and re-save phone as `+254704072784` (E.164 with `+`). Re-send the WhatsApp message with a new reference and re-check.

### 6.6 Confirm tenant belongs to resolved organization
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c \
  "SELECT t.id, t.full_name, t.organization_id, o.name AS org_name FROM tenants t JOIN organizations o ON o.id = t.organization_id WHERE t.phone_number = '<tenant_e164_phone>' LIMIT 1;"
```
- [ ] `t.organization_id` matches the organization resolved from `phone_number_id`

### 6.7 Auto-reply received
- [ ] Tenant received the `payment_evidence_received` WhatsApp message on their phone
- [ ] Message content mentions the amount and reference

If NOT received → template not approved in Meta yet. Submit `payment_evidence_received` in Meta WhatsApp Manager as a Utility template. Approval takes hours to days. Everything else can proceed while you wait.

---

## Phase 7 — PaymentReviewItem persistence

These checks verify the new transaction isolation and duplicate-handling behavior.

### 7.1 First inbound payment creates PaymentReviewItem
- [ ] Phase 6 confirmed `PaymentReviewItem` created on first webhook

### 7.2 Duplicate Meta webhook does not create a second PaymentReviewItem
- [ ] Replay the same Meta webhook (or resend the same WhatsApp message with the same reference)
- [ ] Verify no duplicate `PaymentReviewItem` row exists for the same `source_message_id` or `reference`

### 7.3 Duplicate webhook still gets payment evidence processing
- [ ] If the first webhook created the `Message` but failed before creating the `PaymentReviewItem`, the duplicate webhook continues processing
- [ ] Verify the `PaymentReviewItem` is eventually created

### 7.4 PaymentReviewItem survives confirmation-send failure
- [ ] `PaymentReviewItem` is committed to the database **before** the confirmation WhatsApp message is sent
- [ ] A provider API failure during confirmation does NOT roll back the `PaymentReviewItem`

### 7.5 `source_message_id` idempotency works
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c \
  "SELECT source_message_id, COUNT(*) FROM payment_review_items WHERE reference = '<REF>' GROUP BY source_message_id HAVING COUNT(*) > 1;"
```
- [ ] Returns 0 rows (no duplicate `source_message_id` for the same reference)

### 7.6 Tenant/org isolation remains intact
- [ ] A `PaymentReviewItem` from one organization is never visible to or processed by another organization
- [ ] All WhatsApp inbound processing is scoped to the resolved `organization_id`

---

## Phase 8 — CSV bridge

### 8.1 Prepare a test CSV
Create a file containing the same reference you tested in Phase 6:
```csv
Date,Transaction,Currency,Deposit
22/08/2026,"MPESA TO ACC 0100316372900 TESTREF001 TIMESTAMP: 174305489032 TO 0100316372900",KES,"20,000.00"
```

### 8.2 Upload via UI
- [ ] Navigate to Batch Payment Upload
- [ ] Upload CSV
- [ ] Preview shows: Row 1 status **Matched**, tenant name correct, lease matched

### 8.3 Verify duplicate detection
Re-upload the same CSV without committing.
- [ ] Row now shows **Already recorded** if you'd committed previously, OR still **Matched** if you hadn't

---

## Phase 9 — Deposit-split behavior

**Use a TEST tenant only.** Don't experiment on a real tenant's ledger. Ideally create a fresh test lease with rent=12000, deposit=12000.

### 9.1 Insufficient first payment
Send WhatsApp reference `TESTINSUF01` amount 8000, upload matching CSV row.
- [ ] Row shows **Deposit not covered**
- [ ] Checkbox disabled
- [ ] Hint says "Deposit balance is KES 12,000. First payment must cover it in full."

### 9.2 Exact deposit
Send WhatsApp reference `TESTEXACT01` amount 12000, upload matching CSV row.
- [ ] Row shows **Matched** with "Will apply to deposit" hint
- [ ] Commit → verify single payment:
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT amount, payment_type, reference FROM payments WHERE reference='TESTEXACT01';"
```
- [ ] Exactly ONE row, `payment_type='deposit'`, amount 12000

### 9.3 Split payment (rent + deposit)
Send WhatsApp reference `TESTSPLIT01` amount 18000, upload matching CSV row.
- [ ] Row shows **Matched** with "Will split: KES 12,000 deposit + KES 6,000 rent"
- [ ] Commit → verify two payments:
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT amount, payment_type, reference FROM payments WHERE reference='TESTSPLIT01';"
```
- [ ] TWO rows: one `deposit` for 12000, one `rent` for 6000
- [ ] Both share reference `TESTSPLIT01`

### 9.4 Full month (deposit + one month rent)
Reference `TESTFULL01` amount 24000.
- [ ] Preview shows split: 12000 deposit + 12000 rent
- [ ] After commit: two payments, deposit charge status = paid, first rent charge status = paid

### 9.5 Post-deposit payment
On the same lease after deposit is paid, upload another row (reference `TESTAFTER01`, amount 12000).
- [ ] Row shows **Matched** (no split hint — deposit already paid)
- [ ] Commit → verify single payment:
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT amount, payment_type, reference FROM payments WHERE reference='TESTAFTER01';"
```
- [ ] ONE row, `payment_type='rent'`

### 9.6 Charges reflect settlement
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT amount, amount_paid, charge_type, status FROM charges WHERE lease_id='<TEST_LEASE_UUID>' ORDER BY charge_type, due_date;"
```
- [ ] Deposit charge: `amount_paid = amount`, `status = 'paid'`
- [ ] Rent charges reflect the correct amounts allocated

---

## Phase 10 — Downstream integrations

### 10.1 Audit logs
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT entity_type, action, description, created_at FROM audit_logs WHERE entity_type='payment' AND created_at > NOW() - INTERVAL '30 minutes' ORDER BY created_at DESC LIMIT 10;"
```
- [ ] Each committed payment has an audit entry
- [ ] Description mentions batch=True and payment_type

### 10.2 WhatsApp receipt sent
- [ ] For split payments: tenant received ONE `payment_receipt` message (not two)
- [ ] Amount in receipt equals the primary payment (deposit portion on splits)

### 10.3 Dashboard totals
```bash
# Rent collected (should exclude deposits)
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT COALESCE(SUM(amount),0) AS rent_collected FROM payments WHERE payment_type='rent' AND organization_id='<ORG_UUID>';"

# Deposits held
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT COALESCE(SUM(amount),0) AS deposits_held FROM payments WHERE payment_type='deposit' AND organization_id='<ORG_UUID>';"
```
- [ ] Dashboard "Rent Collected" matches the rent-only sum above
- [ ] Deposits held displayed separately (or per your dashboard design)
- [ ] Rent collected total does NOT include deposit amounts

### 10.4 Tenant dashboard
- [ ] Log in as tenant (or check tenant view)
- [ ] Current balance reflects the payments correctly
- [ ] Payment history shows the split payments distinguishable

---

## Phase 11 — Money integrity checks

**These are the ones that catch financial bugs. Never skip.**

### 11.1 No money lost or duplicated in split
For each split reference from Phase 9:
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT reference, SUM(amount) AS total_from_split FROM payments WHERE reference IN ('TESTSPLIT01','TESTFULL01') GROUP BY reference;"
```
- [ ] `total_from_split` for TESTSPLIT01 = 18000
- [ ] `total_from_split` for TESTFULL01 = 24000

### 11.2 No orphan payments with NULL payment_type
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT COUNT(*) FROM payments WHERE payment_type IS NULL;"
```
- [ ] Count = 0 (or acknowledge legacy count if any — none should be created going forward)

### 11.3 Every settled deposit charge has a matching deposit payment
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT c.lease_id, c.amount_paid AS deposit_settled, COALESCE(SUM(p.amount), 0) AS deposit_paid FROM charges c LEFT JOIN payments p ON p.lease_id=c.lease_id AND p.payment_type='deposit' WHERE c.charge_type='deposit' AND c.amount_paid > 0 GROUP BY c.lease_id, c.amount_paid HAVING c.amount_paid > COALESCE(SUM(p.amount), 0);"
```
- [ ] Returns 0 rows (no deposit charge is settled beyond what deposit payments cover)

### 11.4 Rent collection matches rent payments (no leakage from deposit pool)
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT c.charge_type, SUM(c.amount_paid) AS settled FROM charges c GROUP BY c.charge_type;"
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT payment_type, SUM(amount) AS total FROM payments GROUP BY payment_type;"
```
- [ ] Sum of rent settlements ≈ sum of rent payments (may differ if unpaid rent charges exist — that's expected)
- [ ] Sum of deposit settlements ≈ sum of deposit payments (should be exact)

---

## Phase 12 — Regression checks

### 12.1 Manual RecordPayment still works
- [ ] Log in, go to Record Payment
- [ ] Pick a real tenant (with deposit already paid)
- [ ] Form defaults to "Rent" and rent amount
- [ ] Submit → payment created with `payment_type='rent'`
- [ ] Pick a different tenant (with deposit still unpaid)
- [ ] Form defaults to "Deposit" and deposit amount
- [ ] Submit → payment created with `payment_type='deposit'`

### 12.2 Batch upload without deposits works as before
- [ ] Upload a CSV with rows for tenants who already have deposit paid
- [ ] All rows should show Matched with no split hint
- [ ] Commit → single rent payments per row

### 12.3 Reconciliation queue unaffected
- [ ] Navigate to Reconciliation page
- [ ] Existing pending review items still visible
- [ ] Try to apply one → should work exactly as before

### 12.4 Existing payments display correctly
- [ ] Payment history for an old tenant still displays
- [ ] No display errors on `payment_type=NULL` legacy rows

---

## Phase 13 — Rollback plan (if needed)

**Only rollback if you can't fix forward within 15 minutes.**

### 13.1 Rollback code
```bash
cat rollback_commit.txt  # get the hash from Phase 1.2
git checkout <hash-from-rollback_commit.txt>
docker compose build backend frontend
docker compose up -d backend frontend
docker compose ps
docker logs rental_backend --tail 30
```
- [ ] Backend healthy after rollback
- [ ] Startup logs show previous WhatsApp environment

### 13.2 Rollback migrations (only if migration itself is bad)
```bash
docker compose run --rm backend alembic downgrade -1
```
Do NOT do this unless you're sure the migration is the cause. Rolling back schema on prod is risky.

### 13.3 Restore database (last resort)
```bash
# Stop backend so nothing writes during restore
docker compose stop backend

# Restore from backup
cat backup_before_deploy_<timestamp>.sql | docker exec -i rental_postgres psql -U rental_user -d rental_db

# Restart
docker compose up -d backend
```

Anything committed to the DB between deploy and restore will be lost. Only do this if data corruption is worse than losing recent activity.

### 13.4 WhatsApp-specific rollback guidance

**If code deployment is bad:**
- Rollback application commit, rebuild/restart.

**If migration is bad:**
- Do NOT blindly downgrade production.
- Inspect migration first.
- Backup before schema changes.
- Prefer forward migration when possible.

**If WhatsApp production routing is bad:**
- Do NOT point production traffic at a sandbox organization.
- Correct the `WhatsAppIntegration` row/configuration.
- If necessary, temporarily disable WhatsApp processing rather than routing traffic incorrectly.

**If switching from production back to sandbox:**
- Explicitly set `WHATSAPP_ENV=sandbox`.
- Restore sandbox Meta credentials.
- Restore sandbox integration/fallback configuration.
- Restart backend.
- Verify startup configuration.
- Perform sandbox test.

---

## WhatsApp Sandbox → Production Promotion

This is a controlled checklist. Complete ALL sandbox verification (Phase 4A, Phase 5, Phase 6, Phase 7) before proceeding.

### Pre-promotion checks

- [ ] All sandbox WhatsApp tests pass.
- [ ] 123+ automated tests pass.
- [ ] Migration verified on real database.
- [ ] `whatsapp_integrations` table exists.
- [ ] Sandbox integration row verified.
- [ ] Sandbox payment flow verified end-to-end.
- [ ] Duplicate webhook behavior verified.
- [ ] `PaymentReviewItem` transaction isolation verified.
- [ ] Tenant/org isolation verified.

### Production provisioning

- [ ] Production Meta WABA/phone number is provisioned.
- [ ] Production webhook configuration is ready (URL, verify token, subscribed fields).
- [ ] Production `WhatsAppIntegration` row is created:
```sql
INSERT INTO whatsapp_integrations (id, organization_id, meta_phone_number_id, meta_business_account_id, environment, is_active)
VALUES (
    gen_random_uuid()::text,
    '<PRODUCTION_ORG_UUID>',
    '<PRODUCTION_PHONE_NUMBER_ID>',
    '<PRODUCTION_WABA_ID>',
    'production',
    true
);
```
- [ ] Production environment variables/secrets are configured (NOT copied from sandbox).
- [ ] `WHATSAPP_ENV=production`.
- [ ] `WHATSAPP_DEFAULT_ORG_ID` is NOT relied upon for routing.
- [ ] Production `phone_number_id` maps to the intended organization.
- [ ] Production access token is valid.
- [ ] Production webhook verify token matches Meta.
- [ ] Production app secret is configured.
- [ ] No sandbox credentials are present in production.
- [ ] Logs do not expose credentials.
- [ ] A controlled production test tenant is available.
- [ ] Rollback plan has been tested/understood.

### WARNING

**DO NOT switch `WHATSAPP_ENV=production` until a production `WhatsAppIntegration` row exists for the production `phone_number_id`.**

**DO NOT simply replace the sandbox `phone_number_id` in `.env` and assume the system is production-ready.**

The production architecture is DB-routed SaaS, not env-var-routed single-org.

---

## Post-deploy notes

### Payments created before this fix
Any batch payments from before the fix are still typed `rent` in the DB and their deposit charges are unpaid. This fix doesn't retroactively correct old data. If needed, fix per-tenant manually via the UI, or ask for a one-off migration script.

### Meta template approval
The `payment_evidence_received` template needs Meta approval before it will send in production. Submit in WhatsApp Manager as Utility category. Until approved, the auto-reply silently fails for tenants forwarding M-Pesa SMS — check `docker logs rental_backend` for "Failed to send payment_evidence_received" warnings if you're not sure it's approved.

### Known limitation
Anne Doe's phone must be stored in E.164 format (`+254...`) in her tenant record. If saved as local format (`0704...`), the phone-hash lookup fails and review items get created with `tenant_id=NULL` — invisible to CSV bridge. Same issue affects OTP delivery. Fix per-tenant by editing the phone field via UI.

### Database verification note
Database verification (including migration `f8a1b2c3d4e5` and `whatsapp_integrations` table inspection) was not completed during implementation because `rental_postgres` was not running. This checklist must be executed against a live database to confirm schema health.

---

## Definition of Done

A production deployment is complete when:

- [ ] Database backup taken and verified (Phase 1.1).
- [ ] Code deployed and containers healthy (Phase 3.1–3.2).
- [ ] WhatsApp startup validation reports `valid` for the target environment (Phase 3.3).
- [ ] `whatsapp_integrations` table exists with correct schema (Phase 2.3–2.4).
- [ ] For sandbox: sandbox integration row verified and test tenant payment works end-to-end.
- [ ] For production: production integration row exists, `WHATSAPP_ENV=production`, and production test tenant payment works end-to-end.
- [ ] Deposit-split behavior verified (insufficient, exact, split, full month, post-deposit).
- [ ] Money integrity checks pass (no lost/duplicated money, no orphan NULL payment_types, deposit/payment reconciliation matches).
- [ ] Regression checks pass (manual payments, batch upload, reconciliation, legacy payments).
- [ ] All automated tests pass (123+).
- [ ] No secrets exposed in logs.
- [ ] Rollback plan documented and understood.

---

## Quick reference: common queries during testing

```bash
# Latest 10 inbound WhatsApp messages
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT phone_number, LEFT(content, 80), created_at FROM messages WHERE channel='whatsapp' AND direction='incoming' ORDER BY created_at DESC LIMIT 10;"

# Latest 10 review items
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT reference, amount, tenant_id IS NOT NULL AS has_tenant, source, status FROM payment_review_items ORDER BY created_at DESC LIMIT 10;"

# All payments for a reference (see if split worked)
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT amount, payment_type, reference FROM payments WHERE reference='<REF>';"

# Charges for a lease (see settlement state)
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT amount, amount_paid, charge_type, status, due_date FROM charges WHERE lease_id='<LEASE_UUID>' ORDER BY due_date;"

# whatsapp_integrations table (all environments)
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT id, environment, meta_phone_number_id, meta_business_account_id, organization_id, is_active, created_at FROM whatsapp_integrations ORDER BY environment, created_at;"

# Sandbox integration row
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT * FROM whatsapp_integrations WHERE environment='sandbox' AND meta_phone_number_id='<SANDBOX_PHONE_NUMBER_ID>';"

# Production integration row
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT * FROM whatsapp_integrations WHERE environment='production' AND meta_phone_number_id='<PRODUCTION_PHONE_NUMBER_ID>';"

# Backend logs (tail)
docker logs rental_backend --tail 100 --follow

# Restart backend without rebuilding
docker compose restart backend
```
