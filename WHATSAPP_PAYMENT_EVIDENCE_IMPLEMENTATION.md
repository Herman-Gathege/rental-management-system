# WhatsApp Payment-Evidence Reconciliation — Implementation Report & Partner Guide

## 1. What Was Implemented

### 1.1 Architecture Extension (NOT a parallel system)

We extended the **existing reconciliation boundary** (`PaymentReviewItem`) to accept WhatsApp as a new evidence source. No second payment system was created.

```
WhatsApp message
    → existing Message
    → existing Ticket
    → NEW PaymentReviewItem (source="whatsapp", status="pending_review")
        → existing apply_review_item() flow
            → Payment
                → Payment History
```

**Forbidden path (never created):**
```
WhatsApp → Payment  ❌
```

**Required path (enforced by code):**
```
WhatsApp → PaymentReviewItem → apply_review_item() → Payment  ✅
```

### 1.2 Files Created

| File | Purpose |
|------|---------|
| `backend/app/services/whatsapp_payment_parser.py` | Conservative parser for free-form WhatsApp payment messages |
| `backend/tests/services/test_whatsapp_payment_parser.py` | Parser tests (real-world examples, false positives, amount extraction) |
| `backend/tests/services/test_whatsapp_inbound_payment.py` | WhatsApp inbound flow tests |
| `backend/tests/services/test_payment_reconciliation_integrity.py` | Financial integrity tests (no direct Payment creation, duplicate protection) |
| `backend/tests/services/test_payment_batch_cross_source.py` | CSV ↔ WhatsApp matching tests |
| `backend/tests/conftest.py` | Shared test fixtures |
| `backend/alembic/versions/a1b2c3d4e5f6_add_whatsapp_evidence_fields.py` | Database migration for new columns |

### 1.3 Files Modified

| File | What Changed |
|------|-------------|
| `backend/app/models/payment_review_item.py` | Added WhatsApp evidence fields: `source`, `source_message_id`, `extracted_reference`, `extracted_amount`, `message_timestamp`, `payer_phone_hash` |
| `backend/app/services/messaging/inbound_handler.py` | Fixed tenant lookup to use encrypted PII (`phone_hash`/`blind_index`). Added payment-evidence detection and optional `PaymentReviewItem` creation after ticket commit. |
| `backend/app/services/payment_reconciliation_service.py` | Added `find_whatsapp_match()` helper. Extended `to_dict()` and `list_review_items()` with `source` filter. |
| `backend/app/services/payment_batch_service.py` | Fixed tenant lookup in CSV preview to use decrypted phone hashes instead of raw equality. |
| `backend/app/api/routes/payment_reconciliation.py` | Added `source` query param to list endpoint. Added `POST /find-whatsapp-match` endpoint. |
| `frontend/src/api/paymentReconciliation.js` | Added `findWhatsAppMatch()` API call. Updated `listReviewItems()` to accept `source` filter. |
| `frontend/src/features/payments/Reconciliation.jsx` | Added source tabs (All / WhatsApp / CSV). Shows WhatsApp evidence panel with parser details. |

---

## 2. Database Migration

**File:** `backend/alembic/versions/a1b2c3d4e5f6_add_whatsapp_evidence_fields.py`

Adds nullable columns to `payment_review_items`:
- `source` (String) — `"whatsapp"` or `"csv"`
- `source_message_id` (String, FK to `messages.id` with `SET NULL`)
- `extracted_reference` (String)
- `extracted_amount` (Numeric(10,2))
- `message_timestamp` (DateTime)
- `payer_phone_hash` (String(64), indexed)

**To apply:**
```bash
cd backend && alembic upgrade head
```

---

## 3. Test Guidance

### 3.1 Run All Tests

```bash
cd backend
python3 -m pytest tests/services/ -v
```

**Expected result:** 54 passed, 0 failed.

### 3.2 Test Files & Coverage

| Test File | What It Covers |
|-----------|---------------|
| `test_whatsapp_payment_parser.py` | 30+ parser tests: real-world examples, false positives, amount extraction, date exclusion, confidence levels |
| `test_whatsapp_inbound_payment.py` | Message + Ticket creation, PaymentReviewItem creation for payment evidence, ordinary messages don't create evidence, duplicate webhook protection, parser failure resilience, tenant resolution via `phone_hash` |
| `test_payment_reconciliation_integrity.py` | WhatsApp processing does NOT create Payment, `apply_review_item()` creates exactly one Payment, duplicate reference protection |
| `test_payment_batch_cross_source.py` | `find_whatsapp_match()` by reference, tenant, amount, date tolerance, end-to-end WhatsApp evidence → CSV matching |

### 3.3 Key Test Scenarios to Verify

1. **Financial Integrity:**
   ```bash
   python3 -m pytest tests/services/test_payment_reconciliation_integrity.py -v
   ```
   - `test_whatsapp_does_not_create_payment` — WhatsApp never touches `Payment` table directly
   - `test_apply_review_item_creates_exactly_one_payment` — existing flow still works
   - `test_duplicate_reference_prevents_double_payment` — same reference cannot create two payments

2. **Parser Accuracy:**
   ```bash
   python3 -m pytest tests/services/test_whatsapp_payment_parser.py -v
   ```
   - All 12 real-world examples from the spec are validated
   - False positives: "Hello", "RENT IS DUE", "I will pay later" → `is_payment_evidence: false`
   - Amount extraction: DEPOSIT keyword, standalone numbers, date exclusion

3. **WhatsApp Inbound Flow:**
   ```bash
   python3 -m pytest tests/services/test_whatsapp_inbound_payment.py -v
   ```
   - Payment message → Message + Ticket + PaymentReviewItem
   - Ordinary message → Message + Ticket only
   - Duplicate webhook → no duplicate PaymentReviewItem
   - Parser crash → webhook still succeeds

4. **Cross-Source Matching:**
   ```bash
   python3 -m pytest tests/services/test_payment_batch_cross_source.py -v
   ```
   - Reference match finds WhatsApp evidence
   - Amount mismatch → no match (goes to review queue)
   - Date tolerance (±3 days)

---

## 4. How to Work with Meta (WhatsApp) Integration

### 4.1 Existing Flow (Preserved)

The existing Meta webhook flow is **unchanged**:

```
Meta webhook
    → POST /api/webhooks/whatsapp
    → handle_inbound_message()
    → Message (created)
    → Ticket (created)
    → ticket_received confirmation (sent to tenant)
```

### 4.2 New Additive Flow

After the ticket is committed, the system **additionally**:

1. Calls `parse_whatsapp_payment(body)`
2. If `is_payment_evidence == true`:
   - Resolves tenant via `phone_hash`/`alternative_phone_hash` (NOT raw `Tenant.phone`)
   - Resolves active lease (if exactly one)
   - Creates `PaymentReviewItem` with `source="whatsapp"`, `status="pending_review"`
3. If parsing fails or no evidence detected: **no error, webhook succeeds normally**

### 4.3 Meta Webhook Configuration

No changes needed to Meta webhook configuration. The existing `/api/webhooks/whatsapp` endpoint continues to work.

**Required Meta app settings (verify in Meta Developer Console):**
- Webhook URL: `https://your-domain.com/api/webhooks/whatsapp`
- Verify token: matches `META_VERIFY_TOKEN` in backend `.env`
- Subscribe to: `messages` field

### 4.4 Testing with Meta

**Option A: Use Meta's Webhook Testing Tool**
1. Go to Meta Developer Console → Your App → WhatsApp → Webhook
2. Use "Test" button to send sample messages
3. Check backend logs for `Created payment review item` or `Payment parser failed` messages

**Option B: Use curl to simulate webhook**
```bash
curl -X POST https://your-domain.com/api/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "object": "whatsapp_business_account",
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "254725123456",
            "type": "text",
            "text": {"body": "MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900"}
          }]
        }
      }]
    }]
  }'
```

**Option C: Use ngrok for local testing**
```bash
ngrok http 8000
# Update Meta webhook URL to ngrok URL
```

### 4.5 Sample WhatsApp Messages to Test

```
UAVO15EI8G 25479****032 - TIMOTHY **

MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900

PESA 0007000220260429102657BCE6A459 ELIJAH MAKAMBI OMBEO 0007 DE4116FA5C6E4B52AD2365438BB530B1 RENT FOR MAY 2026 AND DEPOSIT

CASH DEP AT 2796 DEPOSIT 15000

Hello, when is maintenance?  (should NOT create payment evidence)
```

---

## 5. How Reconciliation Works Now

### 5.1 Review Queue

Landlord visits **Reconciliation** page in the UI.

**New filters:**
- **Status tabs:** Pending | Applied | Rejected | All
- **Source tabs:** All sources | WhatsApp | CSV

WhatsApp items show:
- Green "WhatsApp" badge
- Original message text
- Parser-extracted reference and amount
- Message timestamp

### 5.2 CSV Upload + WhatsApp Matching

When landlord uploads bank CSV:

1. `build_preview()` parses CSV rows
2. For each row, system checks `find_whatsapp_match()`:
   - Reference match?
   - Tenant match?
   - Amount match?
   - Date within ±3 days?
3. Matched items appear in review queue with `source="whatsapp"` metadata
4. **High confidence** (reference + tenant + amount + date match) → landlord can apply directly
5. **Low confidence** (reference matches but amount differs, or no active lease) → stays in review queue for manual resolution

### 5.3 API Endpoints

**New:**
```
POST /api/payments/reconciliation/find-whatsapp-match
Body: { reference?, tenant_id?, amount?, payment_date? }
Returns: [PaymentReviewItem]
```

**Updated:**
```
GET /api/payments/reconciliation?status=pending_review&source=whatsapp
```

---

## 6. Financial Integrity Guarantees

### 6.1 What the Code Enforces

1. **No direct WhatsApp → Payment path**
   - `parse_whatsapp_payment()` returns evidence only
   - `_create_payment_review_item()` creates `PaymentReviewItem` only
   - No `Payment` creation anywhere in WhatsApp inbound flow

2. **All Payments flow through `apply_review_item()`**
   - Existing service method unchanged
   - Same authorization, audit logging, settlement recomputation

3. **Duplicate protection (3 layers)**
   - Webhook: `provider_message_id` deduplication (existing)
   - Review item: `source_message_id` + `status="pending_review"` check
   - Payment: `reference` unique constraint + pre-check in `apply_review_item()`

4. **Tenant PII protection**
   - `Tenant.phone` is Fernet-encrypted
   - Lookup uses `blind_index()` against `phone_hash` / `alternative_phone_hash`
   - No raw phone equality comparison

### 6.2 Tests Proving Safety

Run:
```bash
python3 -m pytest tests/services/test_payment_reconciliation_integrity.py -v
```

Key assertions:
- `test_whatsapp_does_not_create_payment` — Payment count unchanged after WhatsApp message
- `test_apply_review_item_creates_exactly_one_payment` — +1 Payment only
- `test_duplicate_reference_prevents_double_payment` — second apply raises exception

---

## 7. Tenant Identity Resolution

### 7.1 How It Works

```
WhatsApp sender phone (e.g. "+254725123456" or "254725123456")
    ↓
_normalize_phone() → consistent format
    ↓
blind_index() → 64-char hex hash
    ↓
Compare against Tenant.phone_hash OR Tenant.alternative_phone_hash
    ↓
Tenant record (or None if no match)
```

### 7.2 Why Not `Tenant.phone == normalized`?

`Tenant.phone` is stored as Fernet ciphertext. Equality comparison against plaintext is meaningless. We use the existing blind-index/PII architecture.

### 7.3 Multiple Phone Formats Handled

| Incoming Format | Normalized | Hashes Compared |
|-----------------|------------|-----------------|
| `+254725123456` | `+254725123456` | hash(+254725123456), hash(254725123456) |
| `254725123456` | `254725123456` | hash(254725123456) |
| `0725123456` | `+254725123456` | hash(+254725123456), hash(254725123456) |

---

## 8. Parser Design & Limitations

### 8.1 Supported Formats

| Format | Example | Confidence |
|--------|---------|------------|
| M-Pesa ACC | `MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: ...` | High (reference + structure) |
| Standalone ref+phone | `UAVO15EI8G 25479****032 - TIMOTHY **` | Medium (reference only) |
| PESA longhex | `PESA 0007000220260429102657BCE6A459 ...` | High (reference + structure) |
| DEPOSIT keyword | `CASH DEP AT 2796 DEPOSIT 15000` | Low (no reference, amount only) |

### 8.2 Conservative Rules

- **Does NOT** invent references from random alphanumeric tokens
- **Does NOT** interpret phone numbers, timestamps, account numbers, or dates as amounts
- **Does NOT** treat every message with "RENT" or "PAYMENT" as evidence (requires structural context)
- **Does NOT** auto-apply payments — all go to `pending_review`

### 8.3 Known Limitations (Intentionally Left for Future)

- No payment-period inference ("RENT FOR MAY 2026" is preserved but not interpreted)
- No automatic lease selection for multiple active leases (flagged as `multiple_leases`)
- Parser confidence is simple (`high`/`medium`/`low`/`none`), not a ML score
- No batch WhatsApp evidence processing (one message → one review item)

---

## 9. Deployment Checklist

### 9.1 Pre-Deployment

- [ ] Apply Alembic migration: `cd backend && alembic upgrade head`
- [ ] Verify `.env` has `META_VERIFY_TOKEN`, `META_APP_SECRET`, `WHATSAPP_PHONE_NUMBER_ID`
- [ ] Verify Meta webhook URL points to production domain
- [ ] Verify `PII_ENCRYPTION_KEY` and `PII_BLIND_INDEX_KEY` are set (required for tenant lookup)

### 9.2 Post-Deployment

- [ ] Send test WhatsApp message from a known tenant phone
- [ ] Verify `PaymentReviewItem` appears in reconciliation queue with `source="whatsapp"`
- [ ] Upload test CSV with matching reference
- [ ] Verify `find_whatsapp_match()` returns the WhatsApp evidence
- [ ] Apply a review item and verify `Payment` is created exactly once

### 9.3 Monitoring

Watch for these log patterns:
```
INFO - Created payment review item <id> for WhatsApp message <id>
INFO - Payment parser failed for message <id>  (parser errors are safe)
INFO - Payment review item creation failed for message <id>  (creation errors are safe)
```

---

## 10. Working with This Codebase

### 10.1 Key Files to Understand

| File | Why |
|------|-----|
| `backend/app/services/whatsapp_payment_parser.py` | Entry point for parsing WhatsApp messages |
| `backend/app/services/messaging/inbound_handler.py` | Webhook → Message → Ticket → PaymentReviewItem |
| `backend/app/services/payment_reconciliation_service.py` | `find_whatsapp_match()`, `apply_review_item()` |
| `backend/app/models/payment_review_item.py` | Schema for WhatsApp evidence storage |
| `backend/app/api/routes/payment_reconciliation.py` | API endpoints for matching |

### 10.2 Common Tasks

**Add a new parser pattern:**
Edit `backend/app/services/whatsapp_payment_parser.py`:
1. Add regex pattern in module-level constants
2. Add extraction logic in `parse_whatsapp_payment()`
3. Add test case in `tests/services/test_whatsapp_payment_parser.py`

**Adjust matching tolerance:**
Edit `backend/app/services/payment_reconciliation_service.py`:
- `find_whatsapp_match()` line with `timedelta(days=3)` — change tolerance

**Add more evidence fields:**
1. Add column in `backend/app/models/payment_review_item.py`
2. Add migration in `backend/alembic/versions/`
3. Update `to_dict()` in `payment_reconciliation_service.py`
4. Update frontend `Reconciliation.jsx`

### 10.3 Running Tests Continuously

```bash
cd backend
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/services/test_whatsapp_payment_parser.py -v

# Run with coverage (if pytest-cov installed)
python3 -m pytest tests/ --cov=app.services --cov-report=term-missing
```

---

## 11. Git Status

Current branch: `batch-uplods`

All changes committed. Working tree clean.

To see what changed from main:
```bash
git diff main..HEAD --stat
```

---

## 12. Known Issues & Future Work

| Issue | Status | Notes |
|-------|--------|-------|
| Venv files committed | ⚠️ | `backend/venv/` added to `.gitignore`. Existing commit still has them. |
| Amount float vs Decimal | ⚠️ | `find_whatsapp_match()` uses float for amount filter. Should use `Decimal` for exact comparison. |
| Parser coverage | 📋 | More real-world formats may emerge. Parser is designed to be extended conservatively. |
| Payment period inference | 📋 | Not implemented. "RENT FOR MAY 2026" is preserved but not auto-interpreted. |
| Multi-tenant organization support | 📋 | Currently scoped to single org per webhook. Multi-org webhook routing may need future work. |

---

## 13. Partner Quick-Start

If your partner wants to:
1. **Run tests:** `cd backend && python3 -m pytest tests/services/ -v`
2. **Send a test WhatsApp message:** Use curl command in Section 4.4
3. **Check reconciliation queue:** Frontend → Reconciliation page → "WhatsApp" source tab
4. **Test CSV matching:** Upload CSV with reference matching a WhatsApp message
5. **Debug parser:** `python3 -c "from app.services.whatsapp_payment_parser import parse_whatsapp_payment; print(parse_whatsapp_payment('YOUR MESSAGE'))"`

---

*Generated: 2026-08-18*
*Branch: batch-uplods*
*Tests: 54 passed*
