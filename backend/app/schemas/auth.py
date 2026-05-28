from pydantic import BaseModel


class RegisterInviteSchema(BaseModel):
    password: str