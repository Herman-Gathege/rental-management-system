# UX/UI Reconnaissance Report — Rental Property Management System

**Date:** 2026-08-25
**Scope:** Full frontend + targeted backend inspection
**Status:** Reconnaissance only — NO files modified

---

## 1. Executive Summary

The application is a **React 19 + Vite SPA** with a **hand-rolled CSS design system** (no third-party component library). The backend is **FastAPI + SQLAlchemy + PostgreSQL** with a **hybrid pagination model**: some endpoints return bare arrays, others return `{items, total, limit, offset}` envelopes when `limit` is passed.

**All six UX objectives can be implemented incrementally without architectural changes.** The main findings:

- **Global Search:** No global search exists. Only tenant search has a `search` param. A new backend `GET /search/` endpoint is required. RBAC scoping is consistent (`organization_id` filter on every route), making this safe to add. Tenant phone/email/ID fields are encrypted (no substring search possible), so search must rely on `ilike` for names and blind-index hashes for exact match.

- **Pagination:** Only 4 of 35+ list views have server-side pagination (Payments, Tickets, History, Billing). The rest fetch unbounded arrays. The `useServerPagination` hook + `<Pagination>` component are already built and can be reused. Most backend endpoints can accept `limit`/`offset` with minimal changes.

- **Bulk Upload Cancel:** No bulk upload flow has a Cancel button. Payment batch has a "Clear" button (reset state only, no abort). No `AbortController` exists anywhere. Cancel can be added purely on the frontend (reset local state + abort in-flight axios requests).

- **Payment XLSX:** The payment batch flow uses stdlib `csv` only. The entity bulk uploads already use `openpyxl` via shared `bulk_upload_service._read_spreadsheet`. The smallest change is to add XLSX support to the payment batch route using the same library, with the same PK magic-byte detection pattern.

- **Dashboard:** The Owner dashboard (`DashboardContent.jsx`) contains the Ticket Overview at lines 220-283. It fetches via `GET /tickets/metrics/summary` as a best-effort secondary call. Commenting it out is a low-risk, single-file change.

- **Auth Pages:** Login and Register have significant UX gaps (alert() for errors, no loading state on login, no forgot password, no labels, .error-text CSS missing). The backend already supports password reset.

---

## 2. Current Frontend Architecture

### Framework & Tooling
- **React 19** with **Vite** bundler
- **React Router v7** for routing
- **Axios** for HTTP (with silent JWT refresh interceptor)
- **Context API** for state (AuthContext, PropertyContext, TenantPropertyContext)
- **No Redux** (authSlice.js is an empty dead file)
- **No UI library** (no MUI, Ant Design, Chakra, shadcn, etc.)
- **No CSS-in-JS / Tailwind** — plain global CSS files

### Styling/Design System
- Global CSS files imported in `App.jsx`:
  - `base.css` — CSS variables (colors, spacing, radius)
  - `layout.css` — auth-page, dashboard layout
  - `components.css` — buttons, inputs, cards, modals, tables, badges
  - `utilities.css` — text/spacing helpers
  - `dashboard.css`, `properties.css`, `customers.css`, `team.css`, `inspection.css`, etc.
- CSS variables in `base.css`: `--primary:#2563eb`, `--danger:#ef4444`, `--radius:12px`, etc.
- Color palette is **not centralized** — many hardcoded greens, ambers, reds throughout

### Folder Structure
```
frontend/src/
  api/                # Axios API functions per entity
  components/
    ui/               # Dashboard widgets (NotificationsCard, TicketsSummaryCard, MobileCardList)
    Modal.jsx         # Generic modal
    Pagination.jsx     # Reusable pager
    PropertySwitcher/
    public/           # PublicNavbar, PublicFooter
  config/
    navigation.js      # Role-based nav config (single source for Sidebar + Navbar)
  context/
    AuthContext.jsx    # Auth state, session restore, login/register/logout
    PropertyContext.jsx
  features/
    auth/              # Login, Register, RegisterInvite, VerifyPhone
    bulk-upload/       # BulkUpload.jsx (Properties/Units/Tenants panels)
    dashboard/         # Role-based dashboards + layout + widgets
    payments/          # Payments, BatchPayments, Reconciliation
    properties/, units/, tenants/, leases/, tickets/, expenses/, etc.
  hooks/
    useServerPagination.jsx  # Server pagination hook
    usePagination.jsx        # Client pagination (UNUSED dead code)
  routes/
    AppRoutes.jsx
    ProtectedRoute.jsx
  styles/              # Global CSS files
  utils/
    passwordStrength.js
```

### Component Architecture
- **Feature-based** organization (each domain in `features/`)
- **No shared DataTable/Table component** — every page hand-rolls its own `<table>`
- **Reusable components are limited:** Modal, Pagination, MobileCardList, PropertySwitcher, NotificationsCard, TicketsSummaryCard, CollapsibleSection
- **Tables:** Native HTML `<table>` with CSS classes `.properties-table`, `.staff-table`, `.customers-table`, `.team-table`
- **Mobile pattern:** Desktop `<table>` (`.hidden-mobile`) + mobile card list (`.hidden-desktop`) via `MobileCardList`
- **Notifications:** In-app notification center only — no toast/snackbar library

### API Layer
- `api/client.js` — Axios instance with Bearer token interceptor + silent 401 refresh
- Per-entity files: `api/auth.js`, `api/payments.js`, `api/tickets.js`, `api/dashboard.js`, etc.
- Response shapes vary: bare arrays vs paginated envelopes (no standardization)

### State Management
- **Context API** (AuthContext for user/session, PropertyContext for active property)
- **Local component state** (useState) for page-level data
- **No global store** — data fetching is per-page via useEffect

### Route Structure
- Public: `/`, `/about`, `/contact`, `/featured`, `/login`, `/register`, `/accept-invite/:token`, `/register-invite/:token`
- Protected role-based groups:
  - `/owner/*` (LANDLORD) → DashboardLayout
  - `/manager/*` (PROPERTY_MANAGER) → StaffLayout
  - `/finance/*` (FINANCE) → DashboardLayout
  - `/tenant/*` (TENANT) → DashboardLayout
  - `/super-admin/*` (SYSTEM) → SuperAdminLayout
- `/verify-phone` — Protected with `skipPhoneGate` (phone verification gate for LANDLORD)
- All protected routes use `<ProtectedRoute allowedRoles={[...]}>`

### RBAC Model
- 5 roles: LANDLORD, PROPERTY_MANAGER, FINANCE, TENANT, SYSTEM
- Backend: `get_user_org()` resolves `OrganizationMember`, every query filters by `organization_id`
- PM/Finance scoped to assigned properties via `PropertyManager`/`PropertyFinanceManager` tables
- Frontend: `ProtectedRoute` with `allowedRoles` prop, plus per-component role checks

---

## 3. Global Search Assessment (Ctrl+K)

### What Currently Exists
- **Global search:** None. No `/search/` endpoint, no command palette, no keyboard shortcut.
- **Tenant search:** `GET /tenants/?search=` — searches `full_name` via `ilike`, exact match on phone/email/ID via blind-index hashes. This is the ONLY search implementation.
- **Report filters:** `ReportFilters.jsx` — props-driven filter bar (search + dates), reusable but only used in Reports.
- **Inline search boxes:** Tenants page, SuperAdminDashboard — each hand-rolled.

### APIs That Could Support Search
| Entity | Searchable Fields | Notes |
|--------|-------------------|-------|
| Properties | `name`, `address`, `city`, `country` | Plaintext, `ilike` works |
| Units | `name`, `description` | Plaintext |
| Tenants | `full_name` | Phone/email/ID encrypted (exact match only via blind index) |
| Leases | `status` | Limited search value |
| Tickets | `title`, `description`, `category`, `source_phone` | Plaintext |
| Expenses | `title`, `description`, `reference_number` | Plaintext |
| Payments | `reference`, `payment_method` | Plaintext |
| Charges | `status`, `charge_type` | Limited |

### Recommended Architecture
1. **New backend endpoint:** `GET /search/?q=&types=property,unit,tenant&limit=5`
   - Resolves org via `get_user_org()` (consistent with all other routes)
   - Applies role/property scoping (PM/Finance see only assigned properties)
   - Executes parallel ILIKE queries across selected entity tables
   - Returns grouped results: `{ properties: [...], units: [...], tenants: [...], ... }`
   - Each result includes `id`, `label`, `subtitle`, `route` (for navigation)
2. **New frontend components:**
   - `CommandPalette.jsx` — modal with search input, grouped results, keyboard navigation
   - `useKeyboardShortcut` hook — listen for `Ctrl/Cmd+K`
   - Search trigger button in Navbar
3. **Navigation:** Use existing React Router paths (all entity detail routes already exist)

### RBAC/Security Considerations
- Every query must filter by `organization_id` (standard pattern)
- PM/Finance must be scoped to assigned properties (use existing `_scoped_query` pattern)
- Tenant search already demonstrates the correct pattern (`get_user_org` → filter)
- Results should only include entities the role has permission to see

### Estimated Complexity
- **Backend:** Medium — new endpoint + service function, but follows established patterns
- **Frontend:** Medium — new command palette component + keyboard hook, no library needed (or add a lightweight one like `cmdk`)
- **Risk:** Low if scoped to plaintext fields only (avoid encrypted field search)

### Files Likely to Change
| File | Reason |
|------|--------|
| `backend/app/api/routes/search.py` (new) | Global search endpoint |
| `backend/app/services/search_service.py` (new) | Search logic per entity |
| `frontend/src/components/CommandPalette.jsx` (new) | Search UI |
| `frontend/src/hooks/useKeyboardShortcut.js` (new) | Ctrl+K handler |
| `frontend/src/features/dashboard/layout/Navbar.jsx` | Add search trigger button |
| `frontend/src/api/search.js` (new) | Search API function |

---

## 4. Pagination Assessment

### Pagination Support Matrix

| Screen | File | API | Current Behavior | Pagination | Recommended Change | Backend Change? | Risk |
|--------|------|-----|------------------|------------|-------------------|-----------------|------|
| **Payments (owner)** | `features/payments/Payments.jsx` | `GET /payments/` | Server-paginated (`useServerPagination`, 25/page) | Yes Server | None needed | No | Low |
| **Tickets** | `features/tickets/Tickets.jsx` | `GET /tickets/` | Server-paginated (25/page) | Yes Server | None needed | No | Low |
| **History/Audit** | `features/history/History.jsx` | `GET /audit/` | Server-paginated (50/page) | Yes Server | None needed | No | Low |
| **Billing/Charges** | `features/billing/Billing.jsx` | `GET /charges/` | Server-paginated (25/page) | Yes Server | None needed | No | Low |
| **Properties** | `features/properties/Properties.jsx` | `GET /properties/` | Fetch all, bare array | None | Add server pagination | Yes (add limit/offset) | Medium |
| **Units** | `features/units/Units.jsx` | `GET /units/` | Fetch all, bare array | None | Add server pagination | Yes (add limit/offset) | Medium |
| **Tenants** | `features/tenants/Tenants.jsx` | `GET /tenants/` | Fetch all + search | None | Add server pagination | Yes (add limit/offset) | Medium |
| **Leases** | `features/leases/Leases.jsx` | `GET /leases/` | Fetch all + status filter | None | Add server pagination | Yes (add limit/offset) | Medium |
| **Expenses** | `features/expenses/Expenses.jsx` | `GET /expenses/` | Fetch all + filters | None | Add server pagination | Yes (add limit/offset) | Medium |
| **Reconciliation** | `features/payments/Reconciliation.jsx` | `GET /payments/reconciliation` | Fetch all (array), no envelope | None | Add server pagination | Yes (wrap response) | Medium |
| **Notifications** | `features/notifications/Notifications.jsx` | `GET /notifications/` | Fetch all | None | Add server pagination | Maybe (low volume) | Low |
| **Organizations (super)** | `features/superadmin/Organizations.jsx` | `/api/super-admin/organizations` | Client paginated (5/page) | Yes Client | Keep as-is | No | Low |
| **SuperAdmin Dashboard** | `features/superadmin/SuperAdminDashboard.jsx` | `/api/super-admin/organizations` | Client paginated + search | Yes Client | Keep as-is | No | Low |
| **Bulk Upload results** | `features/bulk-upload/BulkUpload.jsx` | Various | Result counts | N/A | No pagination needed | No | Low |
| **Reports** | `features/reports/Reports.jsx` | `/reports/*` | Server-filtered | None | Consider if datasets grow | Maybe | Low |
| **Manager lists** | `features/dashboard/Manager*.jsx` | `/dashboard/manager/*` | Fetch all | None | Add if PM has many | Maybe | Low |
| **Tenant dashboard** | `features/dashboard/TenantDashboard.jsx` | `/dashboard/tenant/*` | Fetch all (filtered client-side) | None | Likely unnecessary (1 tenant) | No | Low |

### Key Findings
- **4 views already paginated** with reusable `useServerPagination` hook + `<Pagination>` component
- **Backend pattern:** Endpoints that accept `limit` param return `{items, total, limit, offset}` envelope; without `limit`, return bare array (backward compatible)
- **Recommended approach:** Extend the same `limit`/`offset` pattern to remaining list endpoints
- **Frontend changes:** Replace `useState` + `useEffect` fetch-all with `useServerPagination` + `<Pagination>` (consistent pattern already established)
- **Backend changes:** Add `limit`/`offset` Query params to route handlers, apply to query, return envelope

---

## 5. Bulk Upload Assessment

### Upload Flow Comparison

| Upload | CSV | XLSX | Preview | Cancel/Clear | Validation | Shared Infrastructure |
|--------|-----|------|---------|--------------|------------|----------------------|
| **Properties** | Yes | Yes | No (Direct upload) | None | Backend per-row skip | `BulkUploadPanel` + `bulk_upload_service` |
| **Units** | Yes | Yes | No (Direct upload) | None | Backend per-row skip | `BulkUploadPanel` + `bulk_upload_service` |
| **Tenants** | Yes | Yes | Yes (Read-only preview) | None (new file clears state) | Backend + preview validation | `TenantBulkUploadPanel` + `bulk_upload_service` |
| **Payments (batch)** | Yes | No | Yes (Review table) | "Clear" (reset only) | Preview + commit validation | `BatchPayments` standalone + `payment_batch_service` |

### Cancel Button Analysis

| Flow | Current State | Cancel Needed? | Behavior |
|------|--------------|----------------|----------|
| Properties upload | No cancel | Yes | Reset file input, result, error states |
| Units upload | No cancel | Yes | Reset file input, result, error states |
| Tenant upload | No cancel | Yes | Reset file input, preview, result, error |
| Payment batch | "Clear" button | Improve | Currently resets state but doesn't abort in-flight request; disabled during flight |

**Key findings:**
- **No `AbortController`** exists anywhere in the codebase
- All axios requests are non-cancellable
- Cancel can be implemented as: (1) reset local state, (2) AbortController for in-flight request
- The "Clear" button in payment batch already demonstrates the correct state-reset pattern (resets `file`, `preview`, `selected`, `leaseChoice`, `result`, `saveResult`, `error` + clears DOM input value)
- **Cancel is purely a frontend concern** — backend uploads are synchronous within the request lifecycle; once committed, data is persisted

### Payment XLSX Support — Recommended Implementation

**Current state:**
- Payment batch: `accept=".csv"` in frontend, `.csv` enforced in backend route
- Uses `payment_batch_service.parse_statement` with stdlib `csv` only
- Entity bulk uploads: accept `.csv,.xlsx`, use `openpyxl` via `bulk_upload_service._read_spreadsheet`

**Smallest safe change:**

1. **Frontend (`BatchPayments.jsx`):**
   - Change `accept=".csv"` to `accept=".csv,.xlsx"`
   - Add loading state for XLSX (similar to `xlsxLoading` in `BulkUploadPanel`)

2. **Backend route (`payment_batch.py`):**
   - Replace `.csv`-only enforcement with format detection (check magic bytes: `PK` → XLSX, else CSV)
   - Add size cap (currently no cap on preview; add e.g., 5 MB for safety)

3. **Backend service (`payment_batch_service.py`):**
   - Add `import openpyxl`
   - Create `_read_upload` helper that dispatches to `_read_csv` or `_read_excel` based on magic bytes (same pattern as `bulk_upload_service._read_spreadsheet`)
   - Refactor `parse_statement` to accept already-parsed rows (list of dicts) instead of raw file
   - This decouples parsing from source format — same validation/matching/preview logic

4. **Reuse from `bulk_upload_service`:**
   - `_read_csv` (with utf-8-sig BOM handling, header normalization)
   - `_read_excel` (openpyxl with datetime normalization)
   - `_clean` (cell value normalization)
   - These could be extracted to a shared `backend/app/services/spreadsheet_utils.py` (future refactoring, not required now)

**Alternative (even smaller):** Add a separate `POST /payments/batch/preview-xlsx` endpoint that converts XLSX to CSV in-memory, then pipes through the existing `parse_statement`. This avoids touching the CSV parser but adds a second endpoint.

**Recommended:** Unified parser — it's the cleanest and follows the existing `bulk_upload_service` pattern. The change is additive and doesn't break CSV behavior.

---

## 6. Dashboard/Homepage Assessment

### Current Dashboard Components

| Role | Component | Location |
|------|-----------|----------|
| Owner/Landlord | `DashboardContent.jsx` | `/owner/dashboard` |
| Property Manager | `StaffDashboard.jsx` | `/manager/dashboard` |
| Finance | `FinanceDashboard.jsx` | `/finance/dashboard` |
| Tenant | `TenantDashboard.jsx` | `/tenant` |
| Super Admin | `SuperAdminDashboard.jsx` | `/super-admin/dashboard` |

### Owner Dashboard (`DashboardContent.jsx`) — Component Hierarchy

```
DashboardContent
+-- Welcome greeting
+-- Property switcher indicator
+-- Statistics Cards Grid (11 cards)
|   +-- Properties, Units, Occupied, Vacant
|   +-- Active Leases, Tenants
|   +-- Expected Rent, Collected, Outstanding
|   +-- Deposits Expected, Deposits Collected
+-- Ticket Overview (portfolio-wide)  <-- TO BE COMMENTED OUT
|   +-- Stats: Open, Closed, Critical/High, Avg resolution
|   +-- Tickets by Category (bars)
|   +-- Top Properties by Ticket Volume (bars)
+-- TicketsSummaryCard (compact recent/urgent)
+-- NotificationsCard
+-- Recent Payments (4-row preview)
```

### Current Data Dependencies (Owner Dashboard)

| Data | API | Blocking? | Notes |
|------|-----|-----------|-------|
| Summary stats | `GET /dashboard/owner/summary` | Yes (with payments) | Parallel via Promise.all |
| Recent payments | `GET /dashboard/finance/recent-payments` | Yes (with summary) | Parallel via Promise.all |
| Ticket metrics | `GET /tickets/metrics/summary` | No (best-effort) | Silent catch, null on failure |
| Tickets (summary card) | `GET /tickets/` | No | Independent component |
| Notifications | `GET /notifications/?unread_only=true` | No | Independent component |

### Ticket Overview Location
- **File:** `frontend/src/features/dashboard/DashboardContent.jsx`
- **Lines:** 220-283
- **Condition:** `{metrics && (...)}` — only renders if ticket metrics fetch succeeds
- **API:** `GET /tickets/metrics/summary` (via `api/ticketMetrics.js`)
- **Position:** Below statistics cards, above TicketsSummaryCard

### Current Layout
- Single-column stack of panels
- Statistics grid: `grid-template-columns: repeat(auto-fit, minmax(180px, 1fr))`
- Ticket Overview is a full-width `dash-panel` with CSS bars (no chart library)
- Recent Payments capped at 4 rows with "View all" link

### Performance Considerations
- **3 parallel API call groups** on mount (summary+payments together, ticket metrics separate, plus TicketsSummaryCard + NotificationsCard independent)
- Ticket metrics failure is silently caught (good — doesn't block dashboard)
- No skeleton/loading spinners — uses text "Loading your dashboard…"
- All stats cards render in one grid (11 cards) — could be overwhelming on mobile

### Responsive Considerations
- Dashboard grid uses `auto-fit, minmax(180px, 1fr)` — adapts to viewport
- Tables swap to card view at <768px via `MobileCardList`
- Bottom nav appears on mobile (<768px)
- No dedicated tablet breakpoint

---

## 7. Reusable Components We Should Leverage

| Category | Component | Path | Reuse For |
|----------|-----------|------|-----------|
| **Modal** | `Modal.jsx` | `components/Modal.jsx` | Search results, confirmations |
| **Pagination** | `Pagination.jsx` | `components/Pagination.jsx` | All paginated tables |
| **Pagination Hook** | `useServerPagination.js` | `hooks/useServerPagination.jsx` | Server-paginated lists |
| **Mobile List** | `MobileCardList.jsx` | `components/ui/MobileCardList.jsx` | Mobile card views |
| **Notifications** | `NotificationsCard.jsx` | `components/ui/NotificationsCard.jsx` | Dashboard widget |
| **Tickets Card** | `TicketsSummaryCard.jsx` | `components/ui/TicketsSummaryCard.jsx` | Dashboard widget |
| **Property Switcher** | `PropertySwitcher.jsx` | `components/PropertySwitcher/` | Dashboard navbar |
| **Page Filters** | `ReportFilters.jsx` | `features/reports/ReportFilters.jsx` | Reusable filter bar |
| **SEO** | `SEO.jsx` | `components/SEO.jsx` | All pages |
| **CollapsibleSection** | `CollapsibleSection.jsx` | `components/CollapsibleSection.jsx` | Form sections |

### CSS Classes (established patterns)
- **Buttons:** `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.btn-ghost`, `.btn-sm`
- **Inputs:** `.input` (text only, no Select/Textarea component)
- **Cards:** `.card`, `.dash-panel`, `.detail-card`, `.stat-card-r`
- **Tables:** `.properties-table`, `.staff-table`, `.customers-table`, `.team-table`
- **Banners:** `.info-banner`, `.info-banner-warning`, `.success-banner`
- **Badges:** `.status-pill`, `.role-badge`, `.condition-badge`, `.audit-action-badge`
- **States:** `.empty-state`, `.text-muted`, `.text-error`, `.text-success`
- **Layout:** `.dash-grid`, `.dashboard-bottom-grid`, `.hidden-mobile`, `.hidden-desktop`

### What's Missing (gaps to fill carefully)
- No `Button` component (CSS-only)
- No `Input/Select/Textarea` component (each form hand-rolls)
- No `EmptyState` component (inline per page)
- No `Spinner/Skeleton` component (inline "Loading…" text)
- No `Badge` component (5+ fragmented badge styles)
- No `Toast/Snackbar` (in-app notifications only)
- No `ConfirmDialog` (uses `window.confirm`)
- No `Tabs` component
- No `Tooltip` component
- No `Drawer` component
- No `SearchInput` component

---

## 8. Auth Pages Assessment

### Login Page (`features/auth/Login.jsx`)
| Aspect | Current State | Issue |
|--------|--------------|-------|
| Error handling | `alert("Login failed")` | Blocking, non-specific, discards server error |
| Loading state | None | Button always enabled, no feedback |
| Labels | Placeholder only | Accessibility failure (no `<label>`) |
| Forgot password | Missing | Backend `/auth/forgot-password` exists but unwired |
| Remember me | Missing | No persistence option |
| Navigation to Register | Missing | User stranded on Login |
| Password toggle | Missing | No show/hide |
| Branding | None | No logo, no navbar, bare card |

### Register Page (`features/auth/Register.jsx`)
| Aspect | Current State | Issue |
|--------|--------------|-------|
| Error handling | `{error && <div className="error-text">{error}</div>}` | `.error-text` CSS undefined — errors invisible (default color) |
| Loading state | Yes (`submitting` state with button label change) | Well implemented |
| Labels | Placeholder only | Accessibility failure |
| Password strength | Yes (Live gauge + checklist) | Well implemented, mirrors backend |
| Navigation to Login | Missing | User stranded on Register |
| `.error-text` CSS | Undefined | Used in 25+ components, no red color |

### VerifyPhone Page (`features/auth/VerifyPhone.jsx`)
| Aspect | Current State |
|--------|--------------|
| Error handling | Yes (Inline with `.error-text` — still undefined CSS) |
| Loading state | Yes (`submitting` state) |
| Resend cooldown | Yes (60s timer with live countdown) |
| Phone display | Yes (Masked) |
| Input | Yes (`inputMode="numeric"`, maxLength=6, digit sanitization) |
| Sign out | `.btn-link` CSS undefined — renders as heavy button |

### Critical CSS Gaps
- `.error-text` — **NOT DEFINED** in any stylesheet. Used in 25+ components. Errors render in default text color (#111827) instead of red (#ef4444).
- `.btn-link` — **NOT DEFINED**. Used in VerifyPhone "Sign out". Renders as full-height button instead of text link.

### Dead Files
- `features/auth/authSlice.js` — 0 bytes, empty (Redux leftover, Context API used instead)
- `features/auth/AuthForm.module.css` — defined but never imported
- `pages/Home.jsx` — legacy, not routed (PublicHome is used)
- `pages/Home.module.css` + `styles/home.css` — styles for orphaned page

### Recommended Auth UX Improvements
1. **Add `.error-text` CSS** — single-line fix in `components.css`
2. **Add `.btn-link` CSS** — text-style link without button chrome
3. **Login page fixes:** Replace `alert()` with inline error, add loading state, add "Forgot password?" link, add "Don't have an account? Register" link, add `<label>` elements
4. **Register page fixes:** Add "Already have an account? Login" link, add `<label>` elements
5. **New pages:** `ForgotPassword.jsx`, `ResetPassword.jsx` (backend endpoints already exist)
6. **AuthLayout wrapper** — shared chrome with logo/branding/footer links

---

## 9. Files Likely to Change

### Frontend — Global Search
| File | Reason |
|------|--------|
| `frontend/src/components/CommandPalette.jsx` (new) | Search modal with grouped results |
| `frontend/src/hooks/useKeyboardShortcut.js` (new) | Ctrl+K handler |
| `frontend/src/api/search.js` (new) | Search API function |
| `frontend/src/features/dashboard/layout/Navbar.jsx` | Add search trigger button |

### Frontend — Pagination
| File | Reason |
|------|--------|
| `frontend/src/features/properties/Properties.jsx` | Add server pagination |
| `frontend/src/features/units/Units.jsx` | Add server pagination |
| `frontend/src/features/tenants/Tenants.jsx` | Add server pagination |
| `frontend/src/features/leases/Leases.jsx` | Add server pagination |
| `frontend/src/features/expenses/Expenses.jsx` | Add server pagination |
| `frontend/src/features/payments/Reconciliation.jsx` | Add server pagination |
| `frontend/src/features/notifications/Notifications.jsx` | Add server pagination (optional) |

### Frontend — Bulk Upload Cancel
| File | Reason |
|------|--------|
| `frontend/src/features/bulk-upload/BulkUpload.jsx` | Add Cancel to Properties, Units, Tenants panels |
| `frontend/src/features/payments/BatchPayments.jsx` | Enhance "Clear" to also abort in-flight |

### Frontend — Payment XLSX
| File | Reason |
|------|--------|
| `frontend/src/features/payments/BatchPayments.jsx` | Change accept to `.csv,.xlsx` |

### Frontend — Dashboard
| File | Reason |
|------|--------|
| `frontend/src/features/dashboard/DashboardContent.jsx` | Comment out Ticket Overview + rearrange layout |

### Frontend — Auth Pages
| File | Reason |
|------|--------|
| `frontend/src/features/auth/Login.jsx` | Inline errors, loading state, forgot link, labels |
| `frontend/src/features/auth/Register.jsx` | Add login link, labels |
| `frontend/src/features/auth/ForgotPassword.jsx` (new) | Password reset request |
| `frontend/src/features/auth/ResetPassword.jsx` (new) | Password reset confirmation |
| `frontend/src/components/AuthLayout.jsx` (new) | Shared auth page wrapper with branding |
| `frontend/src/styles/components.css` | Add `.error-text` and `.btn-link` definitions |
| `frontend/src/routes/AppRoutes.jsx` | Add `/forgot-password`, `/reset-password` routes |

### Backend — Global Search
| File | Reason |
|------|--------|
| `backend/app/api/routes/search.py` (new) | Search endpoint |
| `backend/app/services/search_service.py` (new) | Search logic per entity with RBAC |

### Backend — Pagination
| File | Reason |
|------|--------|
| `backend/app/api/routes/properties.py` | Add limit/offset |
| `backend/app/api/routes/units.py` | Add limit/offset |
| `backend/app/api/routes/tenants.py` | Add limit/offset |
| `backend/app/api/routes/leases.py` | Add limit/offset |
| `backend/app/api/routes/expenses.py` | Add limit/offset |
| `backend/app/api/routes/payment_reconciliation.py` | Wrap response in envelope |

### Backend — Payment XLSX
| File | Reason |
|------|--------|
| `backend/app/api/routes/payment_batch.py` | Accept XLSX, add size cap |
| `backend/app/services/payment_batch_service.py` | Add openpyxl, unified parser |

### Backend — Auth
| File | Reason |
|------|--------|
| (none needed) | `/auth/forgot-password` and `/auth/reset-password` already exist |

### Tests
| File | Reason |
|------|--------|
| `backend/tests/services/test_search_service.py` (new) | Search logic tests |
| `backend/tests/services/test_payment_batch_xlsx.py` (new) | XLSX parsing tests |
| `backend/tests/api/test_pagination.py` (new) | Pagination integration tests |
| `frontend/src/components/CommandPalette.test.jsx` (new) | Command palette behavior |

---

## 10. Risk Assessment

| Change | Risk | Explanation |
|--------|------|-------------|
| **Global Search (backend)** | Medium | New endpoint, but follows established RBAC patterns. Must respect org + property scoping. |
| **Global Search (frontend)** | Low | New components, no existing code affected. |
| **Pagination (backend)** | Medium | Adding `limit`/`offset` to endpoints. Must maintain backward compatibility (bare array when no limit). Risk of breaking existing frontend calls if response shape changes unconditionally. |
| **Pagination (frontend)** | Medium | Changing data-fetching logic on 6+ pages. Must ensure loading/error states handle empty pages. Low if reuse `useServerPagination` pattern. |
| **Bulk Upload Cancel** | Low | Purely additive frontend change. Reset state + AbortController. No backend changes. |
| **Payment XLSX (backend)** | Medium | Adding openpyxl parsing to payment flow. Must not break CSV path. Deposit-first split logic must work identically. |
| **Payment XLSX (frontend)** | Low | Change `accept` attribute only. |
| **Dashboard Ticket Overview removal** | Low | Comment out one block. No functional change to tickets. |
| **Dashboard layout rearrange** | Medium | Visual change only, but affects first impression. Must preserve all data fetching. |
| **Auth `.error-text` CSS fix** | Low | Add missing CSS class. No logic change. |
| **Auth Login page fixes** | Medium | Replacing `alert()` with inline errors requires care to not leak sensitive info. Loading state is safe. |
| **Auth ForgotPassword/ResetPassword pages** | Low | New pages using existing backend endpoints. No existing code affected. |
| **Dead file cleanup** | Low | Remove unused files. Must verify nothing imports them first. |

### Rollback Considerations
- **Backend pagination:** Add `limit`/`offset` as optional params. When absent, return current bare array format. Frontend can be updated independently.
- **Search:** New endpoint — can be removed without affecting anything else.
- **Dashboard:** Use comments (not deletion) so restoration is a single uncomment.
- **XLSX:** Keep CSV path identical. Feature-detect file type; if anything fails, fall back to CSV behavior.

---

## 11. Recommended Implementation Order

### Phase 1: Foundation (Low Risk, High Value)
| Step | Change | Rationale |
|------|--------|-----------|
| 1.1 | Add `.error-text` and `.btn-link` CSS | Fixes invisible errors across 25+ components, including auth pages |
| 1.2 | Add shared `AbortController` utility | Foundation for cancellable requests (used by bulk upload + future features) |
| 1.3 | Remove dead files (`authSlice.js`, `AuthForm.module.css`) | Clean foundation |

### Phase 2: Auth Page UX (Low Risk, User-Facing)
| Step | Change | Rationale |
|------|--------|-----------|
| 2.1 | Fix Login: inline errors, loading state, labels | Critical UX gap — alert() is blocking |
| 2.2 | Fix Register: add login link, labels | Navigation + accessibility |
| 2.3 | Create ForgotPassword + ResetPassword pages | Backend already supports this — wire it up |
| 2.4 | Create AuthLayout wrapper with branding | Consistent auth experience |

### Phase 3: Bulk Upload Cancel (Low Risk, Predictable)
| Step | Change | Rationale |
|------|--------|-----------|
| 3.1 | Add Cancel to Properties/Units/Tenants panels | Straightforward state reset |
| 3.2 | Enhance payment batch "Clear" to abort in-flight | Use AbortController from Phase 1 |

### Phase 4: Payment XLSX (Medium Risk, Feature Parity)
| Step | Change | Rationale |
|------|--------|-----------|
| 4.1 | Add `openpyxl` + unified parser to payment batch service | Reuse pattern from `bulk_upload_service` |
| 4.2 | Update frontend accept attribute | Single-line change |
| 4.3 | Add tests for XLSX parsing + CSV regression | Ensure no breakage |

### Phase 5: Pagination Infrastructure (Medium Risk, Scalability)
| Step | Change | Rationale |
|------|--------|-----------|
| 5.1 | Add `limit`/`offset` to 6 backend endpoints | Follow existing payments/charges pattern |
| 5.2 | Update 6 frontend list pages to use `useServerPagination` | Consistent pattern reuse |

### Phase 6: Global Search (Medium Risk, High Impact)
| Step | Change | Rationale |
|------|--------|-----------|
| 6.1 | Create `GET /search/` endpoint + service | Backend foundation |
| 6.2 | Create CommandPalette component + Ctrl/K hook | Frontend UI |
| 6.3 | Add search trigger to Navbar | Discoverability |

### Phase 7: Dashboard Reorganization (Medium Risk, Visual)
| Step | Change | Rationale |
|------|--------|-----------|
| 7.1 | Comment out Ticket Overview section | Preserve code, remove from view |
| 7.2 | Rearrange dashboard layout | Cleaner hierarchy, responsive grid |

### Phase 8: Regression & Verification
| Step | Change | Rationale |
|------|--------|-----------|
| 8.1 | Full regression test of all bulk uploads | Ensure cancel + XLSX don't break flows |
| 8.2 | Pagination interaction with filters | Ensure page resets when filters change |
| 8.3 | Mobile responsiveness verification | Auth pages, dashboard, tables |
| 8.4 | RBAC verification for search | PM/Finance scoped correctly |

---

## 12. Testing Strategy

### Unit Tests
- Search service: correct scoping, entity grouping, result limiting
- Payment batch XLSX parser: same output as CSV for equivalent data
- Pagination hook: page calculation, total/limit/offset

### Integration Tests
- Search endpoint: RBAC scoping (PM sees only assigned properties)
- Pagination endpoints: backward compatibility (bare array when no limit)
- Payment batch preview + commit with XLSX files
- Auth forgot-password -> reset-password flow

### E2E / Manual Testing Checklist
| Area | What to Test |
|------|-------------|
| **Global Search** | Ctrl+K opens palette, Esc closes, arrow navigation, click result navigates, empty state for no results |
| **Search RBAC** | PM only sees assigned properties, tenant sees own data |
| **Pagination** | Prev/Next buttons, page number click, page resets on filter change, mobile card view |
| **Pagination Filters** | Applying filter resets to page 1, correct total count |
| **Bulk Upload Cancel** | Cancel resets file selection, cancel clears preview, cancel doesn't delete data |
| **Bulk Upload XLSX** | XLSX file accepted, same validation as CSV, same preview, same commit |
| **Payment Flow** | Deposit-first split still works, duplicate detection, save-for-review |
| **Auth Login** | Error displays inline (not alert), loading state, redirect on success |
| **Auth Register** | Password strength gating, redirect to verify-phone, error display |
| **Auth Forgot Password** | Email sent, reset link works, new password accepted |
| **Dashboard** | Loads without Ticket Overview, stats correct, responsive layout |
| **Mobile** | Auth pages usable, dashboard cards stack, tables become cards |
| **Regression** | All existing bulk uploads work, all list views render, all detail pages load |

### Critical Regression Tests
1. Tenant bulk upload with lease onboarding (recently added, must not break)
2. Payment batch deposit-first splitting (core business logic)
3. WhatsApp receipt sending after payment commit
4. Phone verification flow (OTP cooldown, resend, verification)
5. Role-based route protection (all 5 roles)
6. Property switcher context propagation

---

## 13. Proposed Implementation Plan

### Phase 1: CSS Foundation + Cleanup

**Objective:** Fix invisible errors, add missing utilities, clean dead code

| File | Change | Risk |
|------|--------|------|
| `frontend/src/styles/components.css` | Add `.error-text { color: #ef4444; font-size: 0.875rem; }` and `.btn-link { background: none; border: none; color: var(--primary); cursor: pointer; padding: 0; font: inherit; }` | Low |
| `frontend/src/features/auth/authSlice.js` | Delete (0 bytes, unused) | Low |
| `frontend/src/features/auth/AuthForm.module.css` | Delete (unused) | Low |

**Tests:** Visual verification of error styling across auth pages.

---

### Phase 2: Auth Page UX Improvements

**Objective:** Wire up missing auth UX, fix Login/Register gaps

| File | Change | Risk |
|------|--------|------|
| `frontend/src/features/auth/Login.jsx` | Replace `alert()` with inline error state, add `submitting` state (disable button + "Signing in…" text), add `<label>` elements or `aria-label`, add "Forgot password?" link, add "Don't have an account? Register" link | Medium |
| `frontend/src/features/auth/Register.jsx` | Add `<label>` elements, add "Already have an account? Login" link | Low |
| `frontend/src/features/auth/ForgotPassword.jsx` (new) | New page: email input -> `POST /auth/forgot-password` -> success message | Low |
| `frontend/src/features/auth/ResetPassword.jsx` (new) | New page: token from URL, password input -> `POST /auth/reset-password` -> redirect to login | Low |
| `frontend/src/routes/AppRoutes.jsx` | Add `/forgot-password` and `/reset-password` routes | Low |
| `frontend/src/components/AuthLayout.jsx` (new) | Optional: shared wrapper with logo + branding + footer links | Low |

**Tests:** Login with invalid credentials (inline error), login loading state, forgot password flow end-to-end, register link navigation.

---

### Phase 3: Bulk Upload Cancel

| File | Change | Risk |
|------|--------|------|
| `frontend/src/utils/abortController.js` (new) | Utility to create/manage AbortControllers | Low |
| `frontend/src/features/bulk-upload/BulkUpload.jsx` | Add Cancel button to BulkUploadPanel + TenantBulkUploadPanel (reset file/result/error/preview, abort in-flight) | Low |
| `frontend/src/features/payments/BatchPayments.jsx` | Enhance existing "Clear" to also abort in-flight AbortController | Low |

**Tests:** Cancel during upload (request aborted, UI resets), cancel clears preview (tenant), cancel doesn't affect already-persisted data.

---

### Phase 4: Payment XLSX

| File | Change | Risk |
|------|--------|------|
| `backend/app/services/payment_batch_service.py` | Add `_read_csv`, `_read_excel`, `_read_spreadsheet` (magic-byte dispatch). Refactor `parse_statement` to accept parsed rows. | Medium |
| `backend/app/api/routes/payment_batch.py` | Accept `.csv` and `.xlsx` extensions, add size cap (5 MB) | Medium |
| `frontend/src/features/payments/BatchPayments.jsx` | Change `accept=".csv"` to `accept=".csv,.xlsx"` | Low |

**Tests:** XLSX file produces identical preview to CSV, commit works with XLSX, CSV still works (regression), datetime/float normalization correct.

---

### Phase 5: Pagination

| File | Change | Risk |
|------|--------|------|
| `backend/app/api/routes/properties.py` | Add `limit`/`offset` Query params, return `{items, total}` envelope when limit provided | Medium |
| `backend/app/api/routes/units.py` | Same | Medium |
| `backend/app/api/routes/tenants.py` | Same | Medium |
| `backend/app/api/routes/leases.py` | Same | Medium |
| `backend/app/api/routes/expenses.py` | Same | Medium |
| `backend/app/api/routes/payment_reconciliation.py` | Wrap response in `{items, total}` envelope | Medium |
| `frontend/src/features/properties/Properties.jsx` | Use `useServerPagination` + `<Pagination>` | Medium |
| `frontend/src/features/units/Units.jsx` | Same | Medium |
| `frontend/src/features/tenants/Tenants.jsx` | Same | Medium |
| `frontend/src/features/leases/Leases.jsx` | Same | Medium |
| `frontend/src/features/expenses/Expenses.jsx` | Same | Medium |
| `frontend/src/features/payments/Reconciliation.jsx` | Same | Medium |

**Tests:** Each paginated page: page navigation works, filter change resets to page 1, mobile card view still works, backward compat (no limit = all items).

---

### Phase 6: Global Search

| File | Change | Risk |
|------|--------|------|
| `backend/app/services/search_service.py` (new) | Per-entity ILIKE queries with RBAC scoping | Medium |
| `backend/app/api/routes/search.py` (new) | `GET /search/` endpoint | Medium |
| `frontend/src/api/search.js` (new) | Search API function | Low |
| `frontend/src/components/CommandPalette.jsx` (new) | Search modal with grouped results | Low |
| `frontend/src/hooks/useKeyboardShortcut.js` (new) | Ctrl+K / Cmd+K handler | Low |
| `frontend/src/features/dashboard/layout/Navbar.jsx` | Add search trigger button | Low |

**Tests:** Search returns results for each entity type, RBAC scoping works, keyboard navigation works, empty state for no results.

---

### Phase 7: Dashboard Reorganization

| File | Change | Risk |
|------|--------|------|
| `frontend/src/features/dashboard/DashboardContent.jsx` | Comment out Ticket Overview (lines 220-283), rearrange remaining sections | Medium |

**Tests:** Dashboard loads without Ticket Overview, all stats still render, responsive layout works, no console errors from removed section.

---

### Phase 8: Full Regression & Verification

| Area | Tests |
|------|-------|
| **Bulk Uploads** | All 4 flows (Properties, Units, Tenants, Payments) — CSV + XLSX where applicable |
| **Payments** | Batch preview, commit, deposit-first split, save-for-review, reconciliation |
| **Auth** | Login, Register, VerifyPhone, ForgotPassword, ResetPassword, logout |
| **RBAC** | All 5 roles — route access, data scoping, property assignment |
| **Pagination** | All newly paginated pages — navigation, filter interaction, mobile |
| **Search** | Global search — all entity types, RBAC scoping, keyboard nav |
| **Dashboard** | All 5 role dashboards — load, stats, responsive |
| **Mobile** | All pages — auth, dashboard, tables, forms |
| **Regression** | Tenant+lease bulk upload, WhatsApp receipts, phone verification, property switcher |

---

## Appendix A: Key File Paths Reference

### Frontend Structure
```
frontend/src/
├── api/
│   ├── auth.js              # loginUser, registerUser, getMe, verifyOtp, resendOtp
│   ├── client.js            # Axios instance + JWT refresh interceptor
│   ├── dashboard.js         # getOwnerSummary, getFinanceSummary, etc.
│   ├── payments.js          # getPayments, commitBatch, etc.
│   ├── tickets.js           # getTickets
│   ├── bulkUploads.js       # uploadPropertiesCSV, uploadTenantsCSV, etc.
│   └── ...
├── components/
│   ├── Modal.jsx            # Generic modal (title, children, onClose)
│   ├── Pagination.jsx       # Reusable pager (currentPage, totalPages, onPageChange)
│   ├── ui/
│   │   ├── MobileCardList.jsx    # Generic mobile card renderer
│   │   ├── NotificationsCard.jsx # Dashboard notifications widget
│   │   └── TicketsSummaryCard.jsx # Dashboard tickets widget
│   ├── PropertySwitcher/
│   └── public/
│       ├── PublicNavbar.jsx # Marketing site navbar
│       └── PublicFooter.jsx
├── config/
│   └── navigation.js        # Role-based nav config
├── context/
│   ├── AuthContext.jsx      # Auth state, session restore
│   └── PropertyContext.jsx  # Active property state
├── features/
│   ├── auth/
│   │   ├── Login.jsx         # Login page (alert() — needs fix)
│   │   ├── Register.jsx      # Register page (password strength gauge)
│   │   ├── RegisterInvite.jsx
│   │   ├── VerifyPhone.jsx   # OTP verification (strongest auth page)
│   │   ├── authSlice.js      # DEAD FILE (0 bytes)
│   │   └── AuthForm.module.css # DEAD FILE (unused)
│   ├── bulk-upload/
│   │   └── BulkUpload.jsx    # Properties/Units/Tenants panels
│   ├── dashboard/
│   │   ├── Dashboard.jsx     # Role-based router
│   │   ├── DashboardContent.jsx # Owner dashboard (Ticket Overview at 220-283)
│   │   ├── StaffDashboard.jsx
│   │   ├── FinanceDashboard.jsx
│   │   ├── TenantDashboard.jsx
│   │   ├── SuperAdminDashboard.jsx
│   │   ├── ManagerProperties.jsx
│   │   ├── ManagerUnits.jsx
│   │   ├── ManagerTenants.jsx
│   │   ├── ManagerLeases.jsx
│   │   ├── TenantCharges.jsx
│   │   ├── TenantPayments.jsx
│   │   ├── TenantLease.jsx
│   │   ├── TenantInspections.jsx
│   │   └── layout/
│   │       ├── DashboardLayout.jsx
│   │       ├── Sidebar.jsx
│   │       └── Navbar.jsx
│   ├── payments/
│   │   ├── Payments.jsx       # Paginated payment history
│   │   ├── BatchPayments.jsx  # CSV batch upload (needs XLSX)
│   │   └── Reconciliation.jsx # Review queue
│   ├── properties/
│   │   ├── Properties.jsx     # Property list (needs pagination)
│   │   └── PropertyDetail.jsx
│   ├── units/
│   │   ├── Units.jsx          # Unit list (needs pagination)
│   │   └── UnitDetail.jsx
│   ├── tenants/
│   │   ├── Tenants.jsx        # Tenant list + search (needs pagination)
│   │   ├── CreateTenant.jsx
│   │   └── EditTenant.jsx
│   ├── leases/
│   │   ├── Leases.jsx         # Lease list (needs pagination)
│   │   ├── CreateLease.jsx
│   │   └── LeaseDetail.jsx
│   ├── tickets/
│   │   ├── Tickets.jsx        # Paginated tickets
│   │   ├── CreateTicket.jsx
│   │   └── TicketDetail.jsx
│   ├── expenses/
│   │   ├── Expenses.jsx       # Expense list (needs pagination)
│   │   ├── CreateExpense.jsx
│   │   └── ExpenseDetail.jsx
│   ├── reports/
│   │   ├── Reports.jsx
│   │   ├── ReportFilters.jsx  # Reusable filter bar
│   │   ├── RentRollTable.jsx
│   │   ├── CollectionTable.jsx
│   │   ├── VendorTable.jsx
│   │   └── ProfitTable.jsx
│   ├── notifications/
│   │   └── Notifications.jsx
│   ├── history/
│   │   └── History.jsx        # Paginated audit log
│   ├── billing/
│   │   └── Billing.jsx        # Paginated charges
│   ├── settings/
│   │   ├── VendorsSettings.jsx
│   │   ├── ExpenseCategoriesSettings.jsx
│   │   └── ChecklistTemplate.jsx
│   ├── team/
│   │   ├── Team.jsx
│   │   └── AcceptInvitation.jsx
│   └── superadmin/
│       ├── Organizations.jsx       # Client-paginated
│       └── SuperAdminDashboard.jsx # Client-paginated + search
├── hooks/
│   ├── useServerPagination.jsx  # Server pagination hook (REUSE)
│   └── usePagination.jsx         # Client pagination (UNUSED dead code)
├── routes/
│   ├── AppRoutes.jsx            # All routes + guards
│   └── ProtectedRoute.jsx       # Auth guard + role guard + phone gate
├── styles/
│   ├── base.css                 # CSS variables
│   ├── layout.css               # .auth-page, .auth-card, .dashboard-layout
│   ├── components.css           # .btn, .input, .card, .modal, .table, .badge
│   ├── utilities.css            # .text-*, spacing, .w-full
│   ├── dashboard.css            # Sidebar, layout
│   ├── properties.css           # .properties-table, .empty-state
│   ├── customers.css            # .customers-table
│   ├── team.css                 # .team-table, .role-badge
│   └── inspection.css
└── utils/
    └── passwordStrength.js      # Client-side password validator
```

### Backend Structure (key files)
```
backend/app/
├── api/routes/
│   ├── auth.py                  # register, login, verify-otp, forgot-password, reset-password
│   ├── bulk_uploads.py          # Properties/Units/Tenants upload endpoints
│   ├── payment_batch.py         # Payment batch preview/commit (CSV only)
│   ├── payment_reconciliation.py # Review queue
│   ├── properties.py            # Property CRUD
│   ├── units.py                 # Unit CRUD
│   ├── tenants.py               # Tenant CRUD + search
│   ├── leases.py                # Lease CRUD
│   ├── tickets.py               # Ticket CRUD
│   ├── expenses.py              # Expense CRUD
│   ├── payments.py              # Payment CRUD (paginated)
│   ├── charges.py               # Charge CRUD (paginated)
│   ├── dashboard.py             # Role-based summary endpoints
│   ├── reports.py               # Report endpoints
│   ├── audit.py                 # Audit log (paginated)
│   └── notifications.py         # Notification CRUD
├── services/
│   ├── bulk_upload_service.py   # openpyxl + csv parsing (shared)
│   ├── payment_batch_service.py # Payment CSV parsing (needs XLSX)
│   ├── payment_reconciliation_service.py
│   ├── ticket_service.py
│   └── expense_service.py
├── core/
│   ├── roles.py                 # LANDLORD, PROPERTY_MANAGER, FINANCE, TENANT, SYSTEM
│   ├── password_policy.py       # validate_password()
│   └── file_validation.py       # Single-file upload validation
├── models/
│   ├── users.py                 # User model
│   ├── tenant.py                # Tenant model (encrypted fields)
│   ├── property.py
│   ├── unit.py
│   ├── lease.py
│   ├── ticket.py
│   ├── payment.py
│   └── ...
└── tests/
    ├── services/
    │   ├── test_bulk_upload_service.py
    │   └── test_payment_batch_cross_source.py
    └── api/
        └── ...
```

---

## Appendix B: CSS Class Reference (Established Patterns)

| Category | Classes | Usage |
|----------|---------|-------|
| **Buttons** | `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.btn-ghost`, `.btn-sm` | All buttons |
| **Inputs** | `.input` | Text inputs (no Select/Textarea component) |
| **Cards** | `.card`, `.card-w`, `.dash-panel`, `.detail-card`, `.stat-card-r` | Content containers |
| **Tables** | `.properties-table`, `.staff-table`, `.customers-table`, `.team-table` | Data tables |
| **Banners** | `.info-banner`, `.info-banner-warning`, `.success-banner` | Notifications |
| **Badges** | `.status-pill`, `.role-badge`, `.condition-badge`, `.audit-action-badge` | Status indicators |
| **States** | `.empty-state`, `.text-muted`, `.text-error`, `.text-success`, `.text-sm`, `.text-bold` | Text utilities |
| **Layout** | `.dash-grid`, `.dashboard-bottom-grid`, `.hidden-mobile`, `.hidden-desktop`, `.form-stack` | Layout |
| **Modal** | `.modal-backdrop`, `.modal-card` | Modal overlay |
| **Auth** | `.auth-page`, `.auth-card` | Auth page layout |

### Missing CSS (must add)
| Class | Needed By | Definition |
|-------|-----------|------------|
| `.error-text` | 25+ components | `color: #ef4444; font-size: 0.875rem;` |
| `.btn-link` | VerifyPhone | `background: none; border: none; color: var(--primary); cursor: pointer; padding: 0; font: inherit;` |

---

**END OF REPORT**

This report is ready for review. No files were modified during reconnaissance.