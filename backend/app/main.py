# # backend/app/main.py
# from app.api.routes import auth
# from fastapi import FastAPI
# from app.db.session import engine
# from app.db.base import Base
# from app.services.email_service import send_email
# from app.services.s3_service import upload_file
# from app.db.session import SessionLocal
# from app.db.seed_roles import seed_roles
# from fastapi.middleware.cors import CORSMiddleware




# app = FastAPI(title="Rental Management API")

# # Allow React dev server
# origins = [
#     "http://localhost:5173",
#     "http://127.0.0.1:5173",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# app.include_router(auth.router, prefix="/auth", tags=["Auth"])

# @app.get("/")
# def root():
#     return {"message": "API running"}

# @app.get("/health")
# def health_check():
#     return {"status": "ok"}


# # @app.get("/test-email")
# # def test_email():
# #     send_email(
# #         "your_email@gmail.com",
# #         "Test Email",
# #         "<h1>Email integration works 🎉</h1>"
# #     )
# #     return {"message": "email sent"}


# # @app.get("/test-upload")
# # def test_upload():
# #     url = upload_file("test.txt", b"Hello from rental system")
# #     return {"file_url": url}

# from app.api.routes.auth import router as auth_router

# app.include_router(auth_router)

# @app.on_event("startup")
# def startup_event():
#     db = SessionLocal()
#     seed_roles(db)
#     db.close()

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

#bulk uploads
from app.api.routes import bulk_uploads


app = FastAPI(title="Rental Management API")

# ─── Rate limiter wiring (Sprint 7 MVP-1) ───
# The limiter itself lives in app.core.rate_limit; we register it on app.state
# so slowapi's decorators can find it, add a friendly JSON handler for 429s,
# and install the middleware that actually intercepts requests.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
app.include_router(payments_router)
app.include_router(payment_batch.router)
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

#bulk uploads
app.include_router(bulk_uploads.router)


# ─── Health endpoints ───
# Restored: previously present in main.py, silently dropped during a Sprint
# 5/6 merge. Useful for uptime probes, load balancer health checks, and a
# quick smoke test that the API is up.

@app.get("/")
def root():
    return {"message": "API running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ─── Startup seeds ───
# Restored (Sprint 7 audit): seed_roles and seed_checklist_for_all_orgs were
# present on the sprint-4.5-spinoff-checklist-batch branch but silently
# dropped in a later merge, leaving orgs created after that point with no
# default roles or checklist template items. Each seed is wrapped in its
# own try/except so one seed failing doesn't kill the others — the app
# should always start even if a seed can't run.

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