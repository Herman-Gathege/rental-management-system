from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base
from app.services.email_service import send_email
from app.services.s3_service import upload_file



app = FastAPI(title="Rental Management API")



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