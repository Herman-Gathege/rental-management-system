# Production Deployment Checklist — Deposit-Split Fix

**Deploying:** WhatsApp M-Pesa parser + batch upload deposit-first split
**Branch:** `tenant/deposit-first-payment` (or whichever you commit to)
**Prod:** alphaone.africa

**Ground rules:**
- All commands assume you're SSHed into the prod host and inside the project directory.
- If your prod container names differ (e.g. `rental_backend` vs `alphaone_backend`), swap accordingly.
- Adjust `rental_user` / `rental_db` if prod credentials differ.
- Work through phases top-to-bottom. Don't skip Phase 1 backup no matter how confident you are.
- If ANYTHING in Phase 3 fails, stop and rollback (Phase 10) before continuing.

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
- [ ] Your commits appear (parser fix + deposit split)

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
- [ ] If output says "Target database is not up to date" earlier — that's fine, it just means it applied pending ones

### 2.3 Rebuild and restart
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
docker ps
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

### 3.3 payment_review_items table exists
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "\dt payment_review_items"
```
- [ ] Table listed

### 3.4 Deployed commit matches expectation
```bash
git log --oneline -1
```
- [ ] Matches what you pulled in step 2.1

### 3.5 Login works
- [ ] Open alphaone.africa in browser
- [ ] Landlord login succeeds
- [ ] Dashboard loads

**STOP HERE if any of Phase 3 fails. Go to Phase 10 (rollback).**

---

## Phase 4 — WhatsApp inbound path

You're testing whether a forwarded M-Pesa SMS becomes a `PaymentReviewItem` with the tenant correctly linked.

### 4.1 Send a fresh test message
Use a real tenant's WhatsApp phone. Pick a NEW reference (Meta dedups on message ID; the code also dedups on reference — reusing an old ref will silently skip):

```
TESTREF001 Confirmed. Ksh20,000.00 sent to LANDLORD NAME for account 0100316372900 on 22/8/26 at 8:30 AM. New M-PESA balance is Ksh1,240.00. Transaction cost, Ksh0.00.
```

- [ ] Message sent from tenant's phone to Meta Business number

### 4.2 Confirm the raw message was received
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT phone_number, LEFT(content, 100) AS preview, created_at FROM messages WHERE channel='whatsapp' AND direction='incoming' AND created_at > NOW() - INTERVAL '10 minutes' ORDER BY created_at DESC LIMIT 3;"
```
- [ ] Row exists with your test message content
- [ ] `phone_number` is the tenant's phone in E.164 format (`+254...`)

If NO row exists → webhook isn't reaching prod. Check Caddy logs and Meta webhook config. Stop here and diagnose.

### 4.3 Confirm the PaymentReviewItem was created
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT reference, amount, tenant_id IS NOT NULL AS has_tenant, source, status, flag_reason, created_at FROM payment_review_items WHERE created_at > NOW() - INTERVAL '10 minutes' ORDER BY created_at DESC LIMIT 3;"
```
- [ ] Row exists with `reference='TESTREF001'`, `amount=20000`, `source='whatsapp'`, `status='pending_review'`
- [ ] `has_tenant = t` (this is critical — if `f`, phone-format bug hit us)

### 4.4 If `has_tenant = f`, fix the tenant's phone
```bash
# Find the tenant
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT id, full_name FROM tenants WHERE organization_id = '<ORG_UUID>';"
```
Then via the UI, edit the tenant and re-save phone as `+254704072784` (E.164 with `+`). Re-send the WhatsApp message with a new reference and re-check.

### 4.5 Auto-reply received
- [ ] Tenant received the `payment_evidence_received` WhatsApp message on their phone
- [ ] Message content mentions the amount and reference

If NOT received → template not approved in Meta yet. Submit `payment_evidence_received` in Meta WhatsApp Manager as a Utility template. Approval takes hours to days. Everything else can proceed while you wait.

---

## Phase 5 — CSV bridge

### 5.1 Prepare a test CSV
Create a file containing the same reference you tested in Phase 4:
```csv
Date,Transaction,Currency,Deposit
22/08/2026,"MPESA TO ACC 0100316372900 TESTREF001 TIMESTAMP: 174305489032 TO 0100316372900",KES,"20,000.00"
```

### 5.2 Upload via UI
- [ ] Navigate to Batch Payment Upload
- [ ] Upload CSV
- [ ] Preview shows: Row 1 status **Matched**, tenant name correct, lease matched

### 5.3 Verify duplicate detection
Re-upload the same CSV without committing.
- [ ] Row now shows **Already recorded** if you'd committed previously, OR still **Matched** if you hadn't

---

## Phase 6 — Deposit-split behavior

**Use a TEST tenant only.** Don't experiment on a real tenant's ledger. Ideally create a fresh test lease with rent=12000, deposit=12000.

### 6.1 Insufficient first payment
Send WhatsApp reference `TESTINSUF01` amount 8000, upload matching CSV row.
- [ ] Row shows **Deposit not covered**
- [ ] Checkbox disabled
- [ ] Hint says "Deposit balance is KES 12,000. First payment must cover it in full."

### 6.2 Exact deposit
Send WhatsApp reference `TESTEXACT01` amount 12000, upload matching CSV row.
- [ ] Row shows **Matched** with "Will apply to deposit" hint
- [ ] Commit → verify single payment:
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT amount, payment_type, reference FROM payments WHERE reference='TESTEXACT01';"
```
- [ ] Exactly ONE row, `payment_type='deposit'`, amount 12000

### 6.3 Split payment (rent + deposit)
Send WhatsApp reference `TESTSPLIT01` amount 18000, upload matching CSV row.
- [ ] Row shows **Matched** with "Will split: KES 12,000 deposit + KES 6,000 rent"
- [ ] Commit → verify two payments:
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT amount, payment_type, reference FROM payments WHERE reference='TESTSPLIT01';"
```
- [ ] TWO rows: one `deposit` for 12000, one `rent` for 6000
- [ ] Both share reference `TESTSPLIT01`

### 6.4 Full month (deposit + one month rent)
Reference `TESTFULL01` amount 24000.
- [ ] Preview shows split: 12000 deposit + 12000 rent
- [ ] After commit: two payments, deposit charge status = paid, first rent charge status = paid

### 6.5 Post-deposit payment
On the same lease after deposit is paid, upload another row (reference `TESTAFTER01`, amount 12000).
- [ ] Row shows **Matched** (no split hint — deposit already paid)
- [ ] Commit → verify single payment:
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT amount, payment_type, reference FROM payments WHERE reference='TESTAFTER01';"
```
- [ ] ONE row, `payment_type='rent'`

### 6.6 Charges reflect settlement
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT amount, amount_paid, charge_type, status FROM charges WHERE lease_id='<TEST_LEASE_UUID>' ORDER BY charge_type, due_date;"
```
- [ ] Deposit charge: `amount_paid = amount`, `status = 'paid'`
- [ ] Rent charges reflect the correct amounts allocated

---

## Phase 7 — Downstream integrations

### 7.1 Audit logs
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT entity_type, action, description, created_at FROM audit_logs WHERE entity_type='payment' AND created_at > NOW() - INTERVAL '30 minutes' ORDER BY created_at DESC LIMIT 10;"
```
- [ ] Each committed payment has an audit entry
- [ ] Description mentions batch=True and payment_type

### 7.2 WhatsApp receipt sent
- [ ] For split payments: tenant received ONE `payment_receipt` message (not two)
- [ ] Amount in receipt equals the primary payment (deposit portion on splits)

### 7.3 Dashboard totals
```bash
# Rent collected (should exclude deposits)
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT COALESCE(SUM(amount),0) AS rent_collected FROM payments WHERE payment_type='rent' AND organization_id='<ORG_UUID>';"

# Deposits held
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT COALESCE(SUM(amount),0) AS deposits_held FROM payments WHERE payment_type='deposit' AND organization_id='<ORG_UUID>';"
```
- [ ] Dashboard "Rent Collected" matches the rent-only sum above
- [ ] Deposits held displayed separately (or per your dashboard design)
- [ ] Rent collected total does NOT include deposit amounts

### 7.4 Tenant dashboard
- [ ] Log in as tenant (or check tenant view)
- [ ] Current balance reflects the payments correctly
- [ ] Payment history shows the split payments distinguishable

---

## Phase 8 — Money integrity checks

**These are the ones that catch financial bugs. Never skip.**

### 8.1 No money lost or duplicated in split
For each split reference from Phase 6:
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT reference, SUM(amount) AS total_from_split FROM payments WHERE reference IN ('TESTSPLIT01','TESTFULL01') GROUP BY reference;"
```
- [ ] `total_from_split` for TESTSPLIT01 = 18000
- [ ] `total_from_split` for TESTFULL01 = 24000

### 8.2 No orphan payments with NULL payment_type
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT COUNT(*) FROM payments WHERE payment_type IS NULL;"
```
- [ ] Count = 0 (or acknowledge legacy count if any — none should be created going forward)

### 8.3 Every settled deposit charge has a matching deposit payment
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT c.lease_id, c.amount_paid AS deposit_settled, COALESCE(SUM(p.amount), 0) AS deposit_paid FROM charges c LEFT JOIN payments p ON p.lease_id=c.lease_id AND p.payment_type='deposit' WHERE c.charge_type='deposit' AND c.amount_paid > 0 GROUP BY c.lease_id, c.amount_paid HAVING c.amount_paid > COALESCE(SUM(p.amount), 0);"
```
- [ ] Returns 0 rows (no deposit charge is settled beyond what deposit payments cover)

### 8.4 Rent collection matches rent payments (no leakage from deposit pool)
```bash
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT c.charge_type, SUM(c.amount_paid) AS settled FROM charges c GROUP BY c.charge_type;"
docker exec -it rental_postgres psql -U rental_user -d rental_db -c "SELECT payment_type, SUM(amount) AS total FROM payments GROUP BY payment_type;"
```
- [ ] Sum of rent settlements ≈ sum of rent payments (may differ if unpaid rent charges exist — that's expected)
- [ ] Sum of deposit settlements ≈ sum of deposit payments (should be exact)

---

## Phase 9 — Regression checks

### 9.1 Manual RecordPayment still works
- [ ] Log in, go to Record Payment
- [ ] Pick a real tenant (with deposit already paid)
- [ ] Form defaults to "Rent" and rent amount
- [ ] Submit → payment created with `payment_type='rent'`
- [ ] Pick a different tenant (with deposit still unpaid)
- [ ] Form defaults to "Deposit" and deposit amount
- [ ] Submit → payment created with `payment_type='deposit'`

### 9.2 Batch upload without deposits works as before
- [ ] Upload a CSV with rows for tenants who already have deposit paid
- [ ] All rows should show Matched with no split hint
- [ ] Commit → single rent payments per row

### 9.3 Reconciliation queue unaffected
- [ ] Navigate to Reconciliation page
- [ ] Existing pending review items still visible
- [ ] Try to apply one → should work exactly as before

### 9.4 Existing payments display correctly
- [ ] Payment history for an old tenant still displays
- [ ] No display errors on `payment_type=NULL` legacy rows

---

## Phase 10 — Rollback plan (if needed)

**Only rollback if you can't fix forward within 15 minutes.**

### 10.1 Rollback code
```bash
cat rollback_commit.txt  # get the hash from Phase 1.2
git checkout <hash-from-rollback_commit.txt>
docker compose build backend frontend
docker compose up -d backend frontend
docker ps
docker logs rental_backend --tail 30
```

### 10.2 Rollback migrations (only if migration itself is bad)
```bash
docker compose run --rm backend alembic downgrade -1
```
Do NOT do this unless you're sure the migration is the cause. Rolling back schema on prod is risky.

### 10.3 Restore database (last resort)
```bash
# Stop backend so nothing writes during restore
docker compose stop backend

# Restore from backup
cat backup_before_deploy_<timestamp>.sql | docker exec -i rental_postgres psql -U rental_user -d rental_db

# Restart
docker compose up -d backend
```

Anything committed to the DB between deploy and restore will be lost. Only do this if data corruption is worse than losing recent activity.

---

## Post-deploy notes

### Payments created before this fix
Any batch payments from before the fix are still typed `rent` in the DB and their deposit charges are unpaid. This fix doesn't retroactively correct old data. If needed, fix per-tenant manually via the UI, or ask for a one-off migration script.

### Meta template approval
The `payment_evidence_received` template needs Meta approval before it will send in production. Submit in WhatsApp Manager as Utility category. Until approved, the auto-reply silently fails for tenants forwarding M-Pesa SMS — check `docker logs rental_backend` for "Failed to send payment_evidence_received" warnings if you're not sure it's approved.

### Known limitation
Anne Doe's phone must be stored in E.164 format (`+254...`) in her tenant record. If saved as local format (`0704...`), the phone-hash lookup fails and review items get created with `tenant_id=NULL` — invisible to CSV bridge. Same issue affects OTP delivery. Fix per-tenant by editing the phone field via UI.

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

# Backend logs (tail)
docker logs rental_backend --tail 100 --follow

# Restart backend without rebuilding
docker compose restart backend
```
