# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    organization_name: str
    # Sprint 6.2 (#6): phone captured at signup so we can send a WhatsApp OTP.
    phone: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ─── OTP (Sprint 6.2 #6) ───

class OtpVerifyRequest(BaseModel):
    code: str


class OtpResendRequest(BaseModel):
    # Optional: allow correcting the destination number on resend. When omitted,
    # the number captured at registration is reused.
    phone: Optional[str] = None
