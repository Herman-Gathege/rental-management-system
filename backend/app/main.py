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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.db.session import SessionLocal
from app.db.seed_roles import seed_roles
from app.services.checklist_seed import seed_checklist_for_all_orgs

# Routers
from app.api.routes.auth import router as auth_router
from app.api.routes.organizations import router as org_router
from app.api.routes.properties import router as properties_router
from app.api.routes.units import router as units_router
from app.api.routes.tenants import router as tenants_router
from app.api.routes.leases import router as leases_router
from app.api.routes.charges import router as charges_router
from app.api.routes.payments import router as payments_router
from app.api.routes.finance import router as finance_router
from app.api.routes.audit import router as audit_router
from app.api.routes.checklist_template import router as checklist_template_router
from app.api.routes.inspections import router as inspections_router
from app.api.routes.messages import router as messages_router
from app.api.routes.webhooks import router as webhooks_router

app = FastAPI(title="Rental Management API")

# CORS for React + Docker frontend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static file serving for uploads (local dev storage) ───
# Files saved by s3_service.upload_file() are accessible at /uploads/<key>
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Register routers
app.include_router(auth_router)
app.include_router(org_router)
app.include_router(properties_router)
app.include_router(units_router)
app.include_router(tenants_router)
app.include_router(leases_router)
app.include_router(charges_router)
app.include_router(payments_router)
app.include_router(finance_router)
app.include_router(audit_router)
app.include_router(checklist_template_router)
app.include_router(inspections_router)
app.include_router(messages_router)
app.include_router(webhooks_router)

@app.get("/")
def root():
    return {"message": "API running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        # Seed roles
        seed_roles(db)

        # TEMPORARY: seed checklist defaults for any existing orgs
        created = seed_checklist_for_all_orgs(db)
        if created > 0:
            print(f"[Startup] Seeded {created} default checklist items across orgs")
    finally:
        db.close()
