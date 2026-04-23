# backend/app/models/property_manager.py
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, String
from app.db.base import Base


class PropertyManager(Base):
    __tablename__ = "property_managers"

    id = Column(String, primary_key=True)

    property_id = Column(String, ForeignKey("properties.id", ondelete="CASCADE"))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))

    __table_args__ = (
        UniqueConstraint("property_id", "user_id", name="uq_property_manager"),
    )