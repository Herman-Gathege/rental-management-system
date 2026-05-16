#backend\app\models\inspection_item.py
import uuid
from sqlalchemy import Column, String, Integer, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class InspectionItem(Base):
    __tablename__ = "inspection_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    inspection_id = Column(String, ForeignKey("lease_inspections.id", ondelete="CASCADE"), nullable=False)

    # Copied from the checklist template at creation time so historical
    # inspections remain accurate even if the template changes later
    item_name = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)

    # ─── Condition assessment ───
    # good / fair / poor / damaged / (null if not yet inspected)
    condition = Column(String, nullable=True)
    comments = Column(Text, nullable=True)

    # ─── Photos ───
    # JSON-encoded list of URLs (we use Text to keep it simple cross-DB)
    # Max 5 photos per item enforced at the API layer
    photo_urls = Column(Text, nullable=True, default="[]")

    # ─── Deduction (move-out only) ───
    # Amount in KES to deduct from the deposit for damage on this item
    deduction_amount = Column(Numeric(12, 2), nullable=True, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    inspection = relationship("LeaseInspection", back_populates="items")
