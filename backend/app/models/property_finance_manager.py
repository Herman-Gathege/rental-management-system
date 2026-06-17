# backend/app/models/property_finance_manager.py
#
# Finance-manager <-> property assignment (Sprint 4.5 owner portal #2).
# Parallel to PropertyManager: a FINANCE-role user is assigned to specific
# properties so they can be scoped to handle only those properties' finances.
from sqlalchemy import Column, ForeignKey, UniqueConstraint, String
from app.db.base import Base


class PropertyFinanceManager(Base):
    __tablename__ = "property_finance_managers"

    id = Column(String, primary_key=True)

    property_id = Column(String, ForeignKey("properties.id", ondelete="CASCADE"))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))

    __table_args__ = (
        UniqueConstraint("property_id", "user_id", name="uq_property_finance_manager"),
    )
