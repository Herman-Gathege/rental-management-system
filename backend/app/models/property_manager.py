# backend/app/models/property_manager.py
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.db.base import Base


class PropertyManager(Base):
    __tablename__ = "property_managers"

    id = Column(Integer, primary_key=True)

    property_id = Column(Integer, ForeignKey("properties.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

    __table_args__ = (
        UniqueConstraint("property_id", "user_id", name="uq_property_manager"),
    )