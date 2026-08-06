

#backend\app\main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os

from app.db.session import SessionLocal

from app.api.routes.auth import router as auth_router
from app.api.routes.organizations import router as organizations_router
from app.api.routes.properties import router as properties_router
from app.api.routes.units import router as units_router
from app.api.routes.tenants import router as tenants_router
from app.api.routes.leases import router as leases_router
from app.api.routes.charges import router as charges_router
from app.api.routes.payments import router as payments_router
from app.api.routes import payment_batch
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.finance import router as finance_router
from app.api.routes.audit import router as audit_router
from app.api.routes.inspections import router as inspections_router
from app.api.routes.checklist_template import router as checklist_template_router
from app.api.routes.messages import router as messages_router
from app.api.routes.webhooks import router as webhooks_router
from app.api.routes.expenses import router as expenses_router
from app.api.routes.expense_categories import router as expense_categories_router
from app.api.routes.vendors import router as vendors_router
from app.api.routes.expense_reports import router as expense_reports_router

# Sprint 6 — Tickets + Notifications
from app.api.routes.tickets import router as tickets_router
from app.api.routes.ticket_conversation import router as ticket_conversation_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.ticket_metrics import router as ticket_metrics_router

# Startup seeds
from app.db.seed_roles import seed_roles
from app.services.checklist_seed import seed_checklist_for_all_orgs
from app.services.expense_category_seed import seed_expense_categories_for_all_orgs

# Sprint 7 (MVP-1) — Rate limiting on auth endpoints
from app.core.rate_limit import limiter, rate_limit_exceeded_handler

# Sprint 7 cleanup Batch 2 — Bulk uploads
from app.api.routes import bulk_uploads

# Sprint 7 cleanup Batch 3 — Payment reconciliation queue
from app.api.routes import payment_reconciliation


app = FastAPI(title="Rental Management API")

# ─── Rate limiter wiring (Sprint 7 MVP-1) ───
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://alphaone.africa",
        "https://www.alphaone.africa",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth_router)
app.include_router(organizations_router)
app.include_router(properties_router)
app.include_router(units_router)
app.include_router(tenants_router)
app.include_router(leases_router)
app.include_router(charges_router)

# ─── Payment routers ─────────────────────────────────────────────────────
#
# ORDER MATTERS. `payments_router` declares `GET /payments/{payment_id}`, a
# greedy two-segment route that will happily match /payments/reconciliation,
# /payments/batch, or any other sub-router's bare list endpoint — the
# `{payment_id}` slot swallows it and the handler returns "Payment not found".
#
# FastAPI resolves routes in the order they're registered, so payment
# sub-routers with more specific prefixes MUST be included BEFORE the
# generic payments_router. Add any future payment sub-router (bank
# reconciliation, refunds, etc.) above the `payments_router` line too.

app.include_router(payment_batch.router)             # /payments/batch/*
app.include_router(payment_reconciliation.router)    # /payments/reconciliation/*
app.include_router(payments_router)                  # /payments and /payments/{payment_id}

app.include_router(dashboard_router)
app.include_router(finance_router)
app.include_router(audit_router)
app.include_router(inspections_router)
app.include_router(checklist_template_router)
app.include_router(messages_router)
app.include_router(webhooks_router)
app.include_router(expenses_router)
app.include_router(expense_categories_router)
app.include_router(vendors_router)
app.include_router(expense_reports_router)

# Sprint 6
app.include_router(tickets_router)
app.include_router(ticket_conversation_router)
app.include_router(notifications_router)
app.include_router(ticket_metrics_router)

# Sprint 7 cleanup Batch 2 — Bulk uploads
app.include_router(bulk_uploads.router)


# ─── Health endpoints ───

@app.get("/")
def root():
    return {"message": "API running"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


# ─── Startup seeds ───

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        try:
            seed_roles(db)
        except Exception as e:
            print(f"[startup] role seed failed (non-fatal): {e}")

        try:
            checklist_created = seed_checklist_for_all_orgs(db)
            if checklist_created:
                print(f"[startup] seeded {checklist_created} default checklist items across orgs")
        except Exception as e:
            print(f"[startup] checklist seed failed (non-fatal): {e}")

        try:
            cats = seed_expense_categories_for_all_orgs(db)
            if cats:
                print(f"[startup] seeded {cats} expense categories")
        except Exception as e:
            print(f"[startup] category seed failed (non-fatal): {e}")
    finally:
        db.close()
