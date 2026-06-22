# backend/app/models/role.py
from sqlalchemy import Column, String, DateTime
from datetime import datetime
from app.db.base import Base
import uuid


class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    