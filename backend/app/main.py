# backend/app/main.py
from app.api.routes import auth
from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base
from app.services.email_service import send_email
from app.services.s3_service import upload_file
from app.db.session import SessionLocal
from app.db.seed_roles import seed_roles
from fastapi.middleware.cors import CORSMiddleware




app = FastAPI(title="Rental Management API")

# Allow React dev server
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/auth", tags=["Auth"])

@app.get("/")
def root():
    return {"message": "API running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}


# @app.get("/test-email")
# def test_email():
#     send_email(
#         "your_email@gmail.com",
#         "Test Email",
#         "<h1>Email integration works 🎉</h1>"
#     )
#     return {"message": "email sent"}


# @app.get("/test-upload")
# def test_upload():
#     url = upload_file("test.txt", b"Hello from rental system")
#     return {"file_url": url}

from app.api.routes.auth import router as auth_router

app.include_router(auth_router)

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    seed_roles(db)
    db.close()