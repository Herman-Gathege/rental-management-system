# backend/app/models/property.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(String, primary_key=True, index=True)

    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    country = Column(String, nullable=False)

    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"))

    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization")