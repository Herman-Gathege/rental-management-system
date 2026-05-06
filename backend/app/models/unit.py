#backend\app\models\unit.py

import uuid
from sqlalchemy import Column, String, Integer, Float, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Unit(Base):
    __tablename__ = "units"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = Column(String, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)  # e.g. "Unit A1", "Room 4B"
    description = Column(String, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    size_sqm = Column(Float, nullable=True)
    rent_amount = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    property = relationship("Property", backref="units")
    leases = relationship("Lease", back_populates="unit")
