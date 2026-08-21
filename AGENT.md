# AlphaOne — Payment Reconciliation Iteration
## WhatsApp Tenant Payment Capture + Bank CSV Reconciliation

---

# 0. ROLE AND OBJECTIVE

You are working on the **AlphaOne Rental Property Management Tool**, a React/Vite application with a production SaaS backend supporting landlords, property managers, tenants, finance operations, payments, leases, and reporting.

The public website redesign has already been completed.

The current task is **NOT a UI redesign task**.

The objective is to implement a controlled iteration of the existing **batch payment reconciliation workflow**.

The business requirement is to improve how tenant payment information is captured before the landlord uploads the bank CSV.

The new workflow should allow tenants to submit payment-related messages through the existing WhatsApp integration.

The system should:

1. Receive a tenant's WhatsApp message.
2. Identify the authenticated/linked tenant who sent it.
3. Store the original message/payload.
4. Extract the likely payment reference from the message.
5. Store the extracted payment information as a **Pending Reconciliation Record**.
6. Preserve the tenant relationship from the WhatsApp sender.
7. Preserve the original message for audit/debugging.
8. Allow the landlord/user to upload the bank CSV through the existing reconciliation workflow.
9. Match bank transactions against the pending tenant-submitted records.
10. Use transaction reference, tenant identity, amount, dates/timestamps, phone number and other available evidence to determine the best match.
11. Automatically move confidently matched payments into official payment history.
12. Move unmatched or ambiguous records into an **Issues / Reconciliation Exceptions** area for manual resolution.
13. Never silently discard payment submissions or overwrite the original evidence.

The goal is to reduce dependence on inconsistent bank SMS/message formats while retaining the bank CSV as the authoritative transaction source.

---

# 1. CURRENT BUSINESS PROBLEM

The current batch reconciliation process expects the landlord/user to upload a CSV obtained from the bank.

The existing system attempts to identify:

- transaction/payment reference
- phone number

from the bank transaction information and then connect that transaction to an active tenant's payment record.

The problem is that banks do not consistently format transaction messages.

Examples include:

```text
02-Feb-2026
UAVO15EI8G 25479****032 - TIMOTHY **
03-Feb-2026
MPESA TO ACC 0100316372900 UB31M5J6YF TIMESTAMP: 254725342986 TO 0100316372900
04-Feb-2026
MPESA TO ACC 0100316372900 UB4P65OGQ8 TIMESTAMP: 254720891840 TO 0100316372900
06-Feb-2026
CASH DEP AT 2796 20:27:15 06022026 24625269 DEPOSIT 1212120000000000/0/020620270116
06-Feb-2026
29-Apr-2026
PESA 0007000220260429102657BCE6A459 ELIJAH MAKAMBI OMBEO 0007 DE4116FA5C6E4B52AD2365438BB530B1 RENT FOR MAY 2026 AND DEPOSIT
12-May-2026
UEAS8BMFQS 4601470 - KINGPIN SOLUTIO
07-Jul-2026
UG6HVA47T5 070****107 - CINDY IRAMWE
10-Jul-2026
MPESA TO ACC 0100316372900 UGAFKB0GXM TIMESTAMP: 254705073918 TO 0100316372900
11-Jul-2026
UGAS82J1LC 4601470 - KINGPIN SOLUTIO
11-Jul-2026
MPESA TO ACC 0100316372900 UGBAPB3X8W TIMESTAMP: 254707173178 TO 0100316372900 11/07/2026 UGAS82J1LC 4601470 - KINGPIN SOLUTIO
27-Jul-2026
MPESA TO ACC 0100316372900 UGQ930GXXD TIMESTAMP: 254111435559 TO 0100316372900
01-Aug-2026
MPESA TO ACC 0100316372900 UH1561L65S TIMESTAMP: 178556135482 TO 0100316372900

The exact format must NOT be assumed to be stable.

2. IMPORTANT BUSINESS DECISION

A previous idea was to require tenants to create tickets containing payment information.

This was rejected because it creates unnecessary UX friction.

The preferred workflow is now:

Tenant sends payment information through WhatsApp.

WhatsApp is already integrated into the platform and therefore provides a more natural tenant experience.

The tenant should not need to understand reconciliation, CSV files, transaction parsing, or payment matching.

They simply send the payment message/information.

The system handles the structured processing behind the scenes.

3. CORE DATA FLOW

The intended architecture is:

TENANT
   │
   │ sends WhatsApp message
   ▼
WHATSAPP INTEGRATION
   │
   │ identifies sender
   ▼
TENANT IDENTITY RESOLUTION
   │
   │ identifies linked active tenant
   ▼
MESSAGE/PAYMENT PARSER
   │
   ├── original message
   ├── sender phone
   ├── tenant ID
   ├── detected reference
   ├── detected amount (if available)
   ├── detected date/time (if available)
   └── parser metadata
   │
   ▼
PENDING RECONCILIATION RECORD
   │
   │ waits for bank CSV
   ▼
LANDLORD UPLOADS BANK CSV
   │
   ▼
BANK TRANSACTION PARSER
   │
   ▼
MATCHING ENGINE
   │
   ├── confident match
   │       ▼
   │   PAYMENT HISTORY
   │
   └── uncertain/unmatched
           ▼
      RECONCILIATION ISSUES
4. AUTHORITATIVE DATA PRINCIPLE

This distinction is critical.

Tenant WhatsApp message

The WhatsApp message is:

evidence
a payment claim
a source of tenant identity
a source of a possible transaction reference
a source of possible amount/date information

It is NOT the authoritative financial transaction.

Bank CSV

The bank CSV remains the authoritative financial transaction source.

Therefore:

WhatsApp submission
        +
Bank transaction
        ↓
Reconciled payment

A WhatsApp message alone MUST NOT automatically create a finalized payment in payment history.

The system must wait for reconciliation against a bank transaction.

5. PENDING RECONCILIATION RECORD

When a tenant sends a payment message, create a pending reconciliation record.

The exact schema must first be discovered from the existing application.

Do NOT invent a parallel payment system if the existing reconciliation/payment models can safely support the workflow.

The pending record should conceptually contain information such as:

id
tenant_id
sender_phone
original_message
extracted_reference
extracted_amount
message_date
message_timestamp
status
source
created_at
updated_at
matched_bank_transaction_id
match_confidence
match_reason

These are conceptual fields only.

Before implementation, inspect the existing models and determine:

what already exists
what can be reused
what needs to be added
how existing payment records are represented
how existing reconciliation records are represented
how tenants are represented
how leases are represented
how WhatsApp payloads are currently stored

Do NOT blindly create all of the above fields.

6. TENANT IDENTIFICATION

The WhatsApp sender should be the primary mechanism for associating the message with a tenant.

The system should resolve:

WhatsApp phone number
        ↓
Tenant
        ↓
Active lease
        ↓
Property/unit

Only tenants with an appropriate active lease/payment relationship should be eligible for automatic reconciliation.

Do NOT assume every WhatsApp sender is a tenant.

The existing tenant/account/phone-number architecture must be inspected first.

Normalize phone numbers before matching.

For example, the system should account for Kenyan formats such as:

0725xxxxxx
254725xxxxxx
+254725xxxxxx

without creating duplicate identities.

7. PAYMENT REFERENCE EXTRACTION

The parser must NOT assume one fixed bank format.

The system should attempt to identify transaction references from the tenant's submitted message.

Examples of references include:

UB31M5J6YF
UB4P65OGQ8
UG6HVA47T5
UGAS82J1LC
UGBAPB3X8W
UGQ930GXXD
UH1561L65S
UAVO15EI8G
UEAS8BMFQS

However:

DO NOT hard-code these specific examples as the only valid formats.

The implementation should first inspect the actual existing parser/reconciliation logic.

Use robust extraction strategies such as:

existing parser utilities
configurable patterns
transaction-reference heuristics
normalization
confidence scoring

Avoid replacing a working parser unnecessarily.

8. ORIGINAL MESSAGE MUST BE PRESERVED

Never discard the original WhatsApp message after extracting information.

Store the original payload/message where the existing architecture allows.

This is required for:

auditing
troubleshooting
manual reconciliation
improving parsing logic later
understanding bank-format variations

The system should be able to answer:

"What exactly did the tenant send?"

without reconstructing the message from extracted fields.

9. BANK CSV RECONCILIATION

The existing CSV upload workflow should remain the central reconciliation mechanism.

When the landlord uploads a bank CSV:

CSV transaction
        ↓
parse transaction
        ↓
extract reference / amount / date / phone / description
        ↓
compare against pending tenant submissions

The matching engine should consider multiple signals.

Potential signals include:

Strong signals
Transaction reference
Tenant identity where deterministically available
Exact amount
Transaction date/time
Supporting signals
Phone number
Sender phone
Bank transaction description
Lease/payment period
Other existing reconciliation metadata

Do not treat every signal as equally strong.

10. MATCHING SHOULD BE EVIDENCE-BASED

Do not simply match on:

reference == reference

if the existing business rules require more context.

The system should evaluate the available evidence.

Conceptually:

reference match
+
amount match
+
reasonable date/time proximity
+
tenant relationship
=
high-confidence reconciliation

A match should also account for payment timing.

For example:

A tenant may send a payment message near the end of one month for rent intended for the following month.

Therefore the system must distinguish:

transaction date
payment message date
payment period
lease period

Do not blindly equate:

transaction date == rent month
11. PAYMENT PERIOD

The reconciliation process must support cases such as:

29-Apr-2026
...
RENT FOR MAY 2026 AND DEPOSIT

This means the system must not assume that the month in which the transaction occurred is always the month being paid for.

Where the existing payment model supports payment periods, use it.

Where the WhatsApp message explicitly states a payment period, preserve that information as evidence.

Do not invent payment-period inference rules without inspecting the current payment logic.

12. MATCH RESULTS

Every reconciliation attempt should produce a clear outcome.

Recommended conceptual statuses:

PENDING
MATCHED
AMBIGUOUS
UNMATCHED
REVIEW_REQUIRED

Use the existing application's status conventions if they already exist.

MATCHED

The system has sufficient evidence to safely associate the bank transaction with a tenant/payment.

The transaction can proceed into official payment history according to existing business rules.

AMBIGUOUS

Multiple possible tenant/payment matches exist.

Do NOT automatically finalize it.

Send it to reconciliation issues for manual resolution.

UNMATCHED

No suitable tenant/payment match was found.

Send it to reconciliation issues.

REVIEW_REQUIRED

The parser found transaction information but confidence is insufficient.

Send it to reconciliation issues.

13. RECONCILIATION ISSUES TABLE

Payments that cannot be safely reconciled should NOT disappear.

Create or extend an existing reconciliation issues mechanism.

The table should provide enough information for a landlord/finance user to resolve the issue manually.

Useful information includes:

bank transaction
amount
transaction date
reference
bank description
candidate tenant
tenant-submitted reference
tenant phone
original WhatsApp message
reason for failure
match confidence
status

Again, inspect existing models/UI before creating new structures.

Do not duplicate existing functionality unnecessarily.

14. SUCCESSFUL RECONCILIATION

For a high-confidence match:

Bank transaction
        +
Pending tenant submission
        ↓
Validated payment
        ↓
Existing payment history

The implementation must use the existing payment-history creation flow if one exists.

Do NOT create a second parallel payment-history system.

The pending reconciliation record should retain a relationship to the finalized payment/reconciliation result for traceability.

15. DUPLICATE PROTECTION

Duplicate payment submissions must be handled safely.

Examples:

Tenant sends the same payment reference multiple times.

The same WhatsApp message is delivered more than once.

The same bank transaction appears more than once in an uploaded CSV.

The system should prevent duplicate finalized payments.

Use existing unique identifiers where available.

Potential deduplication signals include:

transaction reference
bank transaction ID
WhatsApp message ID
tenant ID
timestamp
amount

Do not assume any single field is globally unique unless the existing system guarantees it.

16. IDEMPOTENCY

WhatsApp/webhook integrations can deliver duplicate events.

The existing webhook implementation must be inspected.

If the integration already has message/event IDs, use them for idempotency.

A repeated webhook event should not create multiple pending reconciliation records.

17. WHATSAPP INTEGRATION

Before changing the WhatsApp integration:

Locate the webhook endpoint.
Inspect the incoming payload.
Determine how sender identity is currently resolved.
Determine how messages are stored.
Determine whether conversation history is already stored.
Determine whether message IDs are available.
Determine whether tenant/account association already exists.

Do not create a second WhatsApp integration.

Extend the existing integration where possible.

18. DO NOT OVERENGINEER THE MESSAGE PARSER

The parser should be robust but maintainable.

Avoid attempting to build a universal NLP system for arbitrary bank messages.

Start with:

normalization
reference extraction
amount extraction where available
date/time extraction where available
phone extraction where available
preservation of raw message
confidence scoring

Support known patterns while keeping the parser extensible.

The bank's inconsistent formats are expected.

19. IMPORTANT: DO NOT ASSUME THE EXAMPLE FORMATS ARE COMPLETE

The examples in this document are representative examples from the current business problem.

They are NOT a complete specification.

The agent MUST inspect:

existing parser code
current CSV reconciliation logic
WhatsApp integration
payment models
tenant models
lease models
payment history
existing reconciliation UI

before implementing.

20. EXISTING SYSTEM FIRST

Before making changes, identify:

WhatsApp integration
        ↓
Webhook
        ↓
Message storage
        ↓
Tenant identity
        ↓
Payment/reconciliation models
        ↓
CSV upload
        ↓
CSV parser
        ↓
Matching logic
        ↓
Payment history
        ↓
Reconciliation issues

Document the current implementation.

Then propose the smallest safe integration point.

Do NOT rewrite working reconciliation logic simply because a new workflow is being introduced.

21. PROTECTED AREAS

Unless explicitly required for this iteration, do NOT modify:

Authentication
Authorization
JWT
User roles
Tenant dashboard
Landlord dashboard
Property management
Lease management
Finance unrelated to reconciliation
Reports unrelated to reconciliation
Inspections
Maintenance
Notifications unrelated to WhatsApp payment capture
Public website
Public website CSS
Public website branding
Infrastructure
Docker configuration
Environment configuration

The public website is considered COMPLETE and should remain untouched.

22. PUBLIC WEBSITE IS NOW OUT OF SCOPE

The previous task was the AlphaOne public website redesign.

That work is complete.

For this iteration:

DO NOT redesign or modify the public website.

Do not modify:

frontend/src/pages/public/
frontend/src/components/public/

unless there is an explicitly approved integration requirement.

Do not change its visual system.

Do not change its branding.

Do not change its responsive behavior.

Do not change its CSS.

23. NO GIT OPERATIONS

You MUST NOT perform Git operations autonomously.

Do not:

git status
git add
git commit
git push
git pull
git checkout
git switch
git merge
git rebase
git reset
git restore
git stash
git branch

The human developer controls Git.

24. NO SUDO

Never run:

sudo ...

Do not install system packages.

Do not modify system services.

25. NO INFRASTRUCTURE CHANGES

Do not modify:

docker-compose.yml
Dockerfile
Caddyfile
nginx.conf
.env
.env.*

unless explicitly instructed.

26. NO UNRELATED REFACTORING

Do not:

clean up unrelated code
rename unrelated models
rewrite unrelated APIs
refactor dashboards
redesign existing tables
change authentication
upgrade dependencies
reorganize the project

Only implement the payment-reconciliation iteration.

27. DEVELOPMENT PROCESS

Follow this order.

PHASE 1 — READ ONLY DISCOVERY

Before changing anything, inspect:

WhatsApp
webhook route
payload schema
message storage
sender identity
message ID/idempotency
Tenants
tenant model
phone-number fields
active lease relationship
Payments
payment model
payment history
payment period
existing payment status
Reconciliation
CSV upload endpoint
CSV parser
reference extraction
phone extraction
matching logic
reconciliation result handling
existing issue handling
Frontend
current reconciliation page
payment history page
any existing reconciliation issues UI
Database
relevant Alembic migrations
foreign keys
uniqueness constraints
existing indexes

Do not code during discovery.

28. DISCOVERY REPORT

Before implementation, provide:

Current WhatsApp flow

Explain how incoming WhatsApp messages currently enter the system.

Current tenant resolution

Explain how a WhatsApp sender is connected to a tenant.

Current payment flow

Explain how payments are currently stored.

Current CSV reconciliation

Explain how the bank CSV is parsed and matched.

Current limitations

Identify exactly where the current implementation cannot support the new workflow.

Proposed integration points

Identify the smallest set of files/models/routes that should change.

Data model proposal

Show which existing tables/models can be reused and which new fields/table, if any, are necessary.

Risk assessment

Identify any risk of:

duplicate payments
incorrect tenant matching
incorrect payment period
webhook duplication
CSV duplication
data loss

Do not implement until the discovery report is complete.

29. IMPLEMENTATION PHASE

After discovery and approval:

Implement the smallest safe iteration.

Preferred sequence:

Add/reuse pending reconciliation storage.
Extend WhatsApp message handling.
Resolve tenant identity.
Extract payment reference.
Preserve original payload.
Store pending reconciliation record.
Extend bank CSV reconciliation.
Match pending records against bank transactions.
Create/update finalized payment through existing payment flow.
Route ambiguous/unmatched records to reconciliation issues.
Add or update UI only where required.
Add duplicate/idempotency protection.
Validate.
30. FRONTEND REQUIREMENTS

The frontend should only be changed where necessary to support the reconciliation workflow.

Potential UI areas:

Pending Reconciliation

Display:

tenant
phone
amount
extracted reference
message date
submitted date
status
original message/evidence
Reconciliation Issues

Display:

bank transaction
reference
amount
date
tenant candidate
original WhatsApp evidence
reason
status
action to resolve

Use the application's existing design system where appropriate.

Do NOT redesign the entire SaaS UI.

31. MANUAL RESOLUTION

The landlord/finance user must be able to resolve problematic records individually.

Possible actions:

assign tenant
confirm payment
reject payment
correct reference
correct payment period
link to existing tenant/payment
mark as resolved

Only implement actions supported by the existing authorization model and business rules.

Do not invent financial operations.

32. MATCHING PRIORITY

The implementation should prefer strong deterministic matches.

Conceptually:

Tier 1

Exact transaction reference + compatible tenant/payment context.

Tier 2

Exact reference + exact amount + compatible date/time.

Tier 3

Tenant identity + amount + compatible date/time.

Tier 4

Phone/reference/description evidence requiring review.

Tier 5

No reliable match → issue.

Do not automatically finalize low-confidence matches.

The exact algorithm should be based on the existing data model and reconciliation implementation discovered in Phase 1.

33. TIME-AWARE RECONCILIATION

The matching system must consider:

tenant message time
bank transaction time
payment date
payment period
lease period

It must support:

current-month rent
previous-month payments
advance rent
rent paid before the month starts
payments referencing a future rent period

Do not assume that:

payment date = rent month
34. AUDITABILITY

Every important reconciliation action should remain traceable.

The system should be able to determine:

Who submitted the payment evidence?
When was it submitted?
What was the original message?
What reference was extracted?
Which bank transaction matched it?
Why was it matched?
When was it finalized?
Who manually resolved it, if applicable?

Reuse the existing audit/logging infrastructure where possible.

35. VALIDATION

Run safe project-local validation.

Examples:

npm run build

and backend tests/lint/type checks where available.

Do NOT use Git commands.

Do NOT use sudo.

Do NOT modify infrastructure.

Validate at minimum:

WhatsApp
valid tenant message
unknown sender
duplicate webhook
malformed message
Parsing
reference extracted
reference absent
amount extracted
multiple possible references
unusual bank format
Reconciliation
exact match
amount mismatch
date mismatch
duplicate transaction
ambiguous match
unmatched transaction
Payment period
current month
previous month
future/advance payment
Finalization
matched payment enters existing payment history
unmatched payment remains visible
issue can be manually resolved
duplicate finalization is prevented
36. FAILURE HANDLING

Never silently discard:

WhatsApp messages
payment references
bank transactions
failed matches
ambiguous matches

If parsing fails:

RAW MESSAGE
     ↓
PENDING / REVIEW REQUIRED

If reconciliation fails:

BANK TRANSACTION
     ↓
RECONCILIATION ISSUE

The system should preserve enough information for manual resolution.

37. DO NOT INVENT BUSINESS RULES

If the existing code does not clearly define:

payment period rules
acceptable matching window
duplicate policy
tenant eligibility
payment status
manual resolution authority

STOP and report the ambiguity.

Do not silently invent a financial rule.

38. FINAL QUALITY STANDARD

The iteration should result in:

Tenant submits payment evidence naturally via WhatsApp
                    ↓
System identifies tenant
                    ↓
System extracts payment reference
                    ↓
Pending reconciliation record created
                    ↓
Landlord uploads bank CSV
                    ↓
Bank transaction becomes authoritative evidence
                    ↓
Matching engine reconciles the two
             ↙                 ↘
      High confidence       Uncertain
             ↓                 ↓
      Payment history     Reconciliation issue

The implementation must prioritize:

Financial correctness
Tenant identity correctness
Duplicate prevention
Auditability
Preservation of raw evidence
Accurate payment-period handling
Minimal changes to existing architecture
Maintainability
Security
SaaS stability
39. FINAL REPORT

When implementation is complete, provide:

Discovery
current WhatsApp architecture
current payment architecture
current reconciliation architecture
Created

List new files/models/migrations/components.

Modified

List only files genuinely required for this iteration.

Data model

Explain new fields/tables and relationships.

WhatsApp

Explain how tenant payment messages are captured.

Parsing

Explain reference extraction and normalization.

Matching

Explain matching priority and confidence handling.

Reconciliation

Explain how CSV transactions become finalized payments.

Issues

Explain how ambiguous/unmatched transactions are handled.

Duplicate protection

Explain idempotency and duplicate prevention.

Validation

Report tests/build checks and results.

Risks / Follow-up

List anything requiring explicit human approval.

FINAL COMMANDMENT

This is a payment reconciliation iteration, not a redesign.

The financial data flow must remain conservative.

Never turn tenant-submitted WhatsApp evidence directly into a finalized payment.

Always follow:

TENANT EVIDENCE → PENDING RECONCILIATION → BANK VERIFICATION → FINAL PAYMENT

When uncertain:

INSPECT EXISTING IMPLEMENTATION → PROPOSE → WAIT FOR APPROVAL

rather than:

ASSUME → REWRITE → RISK INCORRECT FINANCIAL DATA

Do not use Git.

Do not use sudo.

Do not modify infrastructure.

Do not redesign the public website.

Do not refactor unrelated SaaS functionality.

Study the existing payment and WhatsApp architecture first.

Then implement the smallest safe integration.