# WhatsApp Configuration Guide

This document describes the environment-aware WhatsApp configuration system
that supports a clean transition from **Meta Sandbox** to **Meta Production**
without source-code changes.

---

## 1. Environment Model

The `WHATSAPP_ENV` environment variable selects which Meta integration
environment the application targets.

| Value         | Meaning                                                                 |
|---------------|-------------------------------------------------------------------------|
| `sandbox`     | Meta's WhatsApp Cloud API **test/sandbox** phone number. Default for local development. |
| `production`  | Live Meta credentials pointing at a real business phone number.          |

**Do not** use ambiguous values like `live`, `test`, `dev`, or `prod` —
the validation will reject them.

### Switching environments

The only change needed to move from sandbox to production is one line in `.env`:

```env
# Sandbox (.env)
WHATSAPP_ENV=sandbox

# Production (.env)
WHATSAPP_ENV=production
```

No Python source-code changes are required.

---

## 2. Centralized Configuration

All WhatsApp configuration flows through a single `WhatsAppSettings` object
accessible at `app.core.config.settings.whatsapp`:

```python
from app.core.config import settings

settings.whatsapp.environment          # "sandbox" | "production"
settings.whatsapp.phone_number_id      # Meta phone number ID
settings.whatsapp.business_account_id  # Meta business account ID
settings.whatsapp.access_token         # Meta access token
settings.whatsapp.app_secret           # Meta app secret (webhook signing)
settings.whatsapp.default_org_id       # SANDBOX FALLBACK ONLY
settings.whatsapp.webhook_verify_token # Webhook verify token
settings.whatsapp.use_templates        # bool
settings.whatsapp.default_country_code # e.g. "254"
```

The application **never** calls `os.getenv("WHATSAPP_*")` directly in service
code.  All env vars are read once at startup into `WhatsAppSettings`.

### Startup validation

On startup (`main.py`), the application logs the WhatsApp environment and
validates required configuration:

```
[startup] WhatsApp environment: sandbox
[startup] WhatsApp configuration: valid
```

If validation fails, each error is printed:

```
[startup] WhatsApp environment: production
[startup] WhatsApp configuration error: WHATSAPP_BUSINESS_ACCOUNT_ID is required for production
[startup] WhatsApp configuration: INVALID
```

**Secrets are never logged.**  `settings.whatsapp.describe()` returns a
non-sensitive summary (booleans for token/secret presence, not values).

---

## 3. Sandbox Configuration

### Meta sandbox credentials

In the Meta Developer Console (developers.facebook.com):

1. Create a Meta App with the **WhatsApp** product added.
2. Go to **WhatsApp → Getting Started** — the **sandbox** phone number and its
   credentials are displayed there.
3. In **WhatsApp → Configuration**, copy:
   - **Phone Number ID** → `WHATSAPP_PHONE_NUMBER_ID`
   - **WhatsApp Business Account ID** → `WHATSAPP_BUSINESS_ACCOUNT_ID`
4. Generate a **system user access token** with `business_management` and
   `whatsapp_messaging` scopes → `WHATSAPP_ACCESS_TOKEN`
5. In **App Settings → Basic**, copy the **App Secret** → `WHATSAPP_APP_SECRET`

These values are for the **sandbox** environment only and are non-production.

### Sandbox `.env` example

```env
WHATSAPP_ENV=sandbox

WHATSAPP_PHONE_NUMBER_ID=<sandbox phone number id>
WHATSAPP_BUSINESS_ACCOUNT_ID=<sandbox business account id>
WHATSAPP_ACCESS_TOKEN=<sandbox token>
WHATSAPP_APP_SECRET=<sandbox app secret>

# SANDBOX FALLBACK ONLY — see section 5
WHATSAPP_DEFAULT_ORG_ID=<sandbox test organization uuid>

WHATSAPP_WEBHOOK_VERIFY_TOKEN=<your verify token>
WHATSAPP_USE_TEMPLATES=false
WHATSAPP_DEFAULT_COUNTRY_CODE=254
```

### Sandbox organization mapping

```
Meta Sandbox
    ↓ (webhook payload: value.metadata.phone_number_id)
Sandbox WhatsApp Number
    ↓ (resolve_organization lookup in whatsapp_integrations table)
Sandbox/Test Organization
```

If no `WhatsAppIntegration` row exists for the sandbox phone number, the
resolver falls back to `WHATSAPP_DEFAULT_ORG_ID`.  This is a **controlled
sandbox fallback only** — it is never used for production routing.

### Testing a tenant payment message

1. Ensure your tenant's phone number is saved in E.164 format (e.g.
   `+254725123456`) in the tenant record.
2. From the tenant's WhatsApp, send a payment confirmation message to the
   sandbox phone number:

   ```
   MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900
   ```

3. The backend will:
   - Persist the inbound `Message`
   - Create a `Ticket` (source="whatsapp")
   - Parse payment evidence → create `PaymentReviewItem`
   - Send a `payment_evidence_received` confirmation (or `ticket_received`
     fallback)

4. Verify in the Reconciliation UI that the item appears with `source="whatsapp"`.

---

## 4. Production Configuration

### Production `.env` example

```env
WHATSAPP_ENV=production

WHATSAPP_PHONE_NUMBER_ID=<production phone number id>
WHATSAPP_BUSINESS_ACCOUNT_ID=<production business account id>
WHATSAPP_ACCESS_TOKEN=<production token>
WHATSAPP_APP_SECRET=<production app secret>

# NOT USED for production routing — organization is resolved via DB
# WHATSAPP_DEFAULT_ORG_ID=<do not set in production>

WHATSAPP_WEBHOOK_VERIFY_TOKEN=<your verify token>
WHATSAPP_USE_TEMPLATES=true
WHATSAPP_DEFAULT_COUNTRY_CODE=254
```

### Production organization mapping (DB-driven)

```
Meta Production
    ↓ (webhook payload: value.metadata.phone_number_id)
whatsapp_integrations table
    ↓ (environment='production' + meta_phone_number_id + is_active=true)
organization_id
    ↓
Tenant → Lease → PaymentReviewItem
```

Production **must** resolve the organization from the `whatsapp_integrations`
table.  If the `phone_number_id` is not found in the table, the event is
logged as an error and **safely ignored** — it is never silently routed to
an arbitrary organization.

### Onboarding a new SaaS organization (production)

To register a new organization's WhatsApp business number:

```python
integration = WhatsAppIntegration(
    organization_id=org.id,
    meta_phone_number_id="<phone_number_id from Meta>",
    meta_business_account_id="<business_account_id from Meta>",
    environment="production",
    is_active=True,
)
db.add(integration)
db.commit()
```

### Webhook configuration

- **Webhook URL**: `https://your-domain.com/api/webhooks/whatsapp`
- **Verify token**: matches `WHATSAPP_WEBHOOK_VERIFY_TOKEN` in `.env`
- **Subscribed fields**: `messages`

Each Meta phone number in production must have its own webhook subscription
pointing to this URL.

---

## 5. Sandbox vs Production Resolution

The `resolve_organization()` function in
`app/services/messaging/organization_resolver.py` implements the resolution
strategy:

### Sandbox

```
phone_number_id
      ↓
try WhatsAppIntegration lookup (environment='sandbox', is_active=true)
      ↓
if found → use mapped organization_id
      ↓
otherwise → WHATSAPP_DEFAULT_ORG_ID  (SANDBOX FALLBACK ONLY)
```

### Production

```
phone_number_id
      ↓
WhatsAppIntegration lookup (environment='production', is_active=true)
      ↓
found → use mapped organization_id
      ↓
not found → log error, return None, event ignored
```

The sandbox fallback (`WHATSAPP_DEFAULT_ORG_ID`) is explicitly documented as
**SANDBOX FALLBACK ONLY** in both code and configuration.  Production never
uses it.

---

## 6. `phone_number_id` Extraction

The webhook payload from Meta includes the destination phone number in
`value.metadata.phone_number_id`.  The `parse_message_payload()` function
now retains this in each parsed message:

```python
parsed = {
    "provider_message_id": ...,
    "from_phone": ...,
    "message_type": ...,
    "body": ...,
    "timestamp": ...,
    "phone_number_id": "123456789012345",  # from value.metadata
}
```

This is required for the eventual DB-driven organization routing.  The
webhook route uses it to call `resolve_organization(db, phone_number_id)`
before dispatching to `handle_inbound_message()`.

---

## 7. Payment Review Item Reliability

### Duplicate webhook handling

Meta may retry webhook delivery.  The system handles this idempotently:

1. **Message persistence** is idempotent on `provider_message_id` — no
   duplicate `Message` rows.
2. **Ticket creation** is skipped for duplicate messages — no duplicate
   `Ticket` rows.
3. **PaymentReviewItem creation** has a duplicate guard on
   `source_message_id` (any status) and on `reference` (pending only) —
   no duplicate review items.
4. **Incomplete payment processing can be retried**: if the first webhook
   created the message but failed before creating the review item, the
   duplicate webhook continues processing and creates the review item.

### Transaction isolation

The `PaymentReviewItem` is committed to the database **before** the
confirmation WhatsApp message is sent.  This means:

- A provider API failure during confirmation **does not** roll back the
  `PaymentReviewItem`.
- The `PaymentReviewItem` is never deleted by a downstream notification failure.
- The outgoing confirmation `Message` row is either committed (sent or
  failed) or rolled back independently.

---

## 8. Secrets Safety

- All Meta credentials live in environment variables / `.env` (never in source).
- `.env` is in `.gitignore` and is never committed.
- Secrets are never logged.  `settings.whatsapp.describe()` returns booleans
  for presence checks, not values.
- The `whatsapp_integrations` table stores **no raw credentials** — only Meta
  phone number IDs, business account IDs, environment, and the mapping to
  `organization_id`.
