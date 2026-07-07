#backend\app\schemas\auth.py
from pydantic import BaseModel


class RegisterInviteSchema(BaseModel):
    password: str