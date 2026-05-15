#backend\app\models\checklist_item_template.py
import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class ChecklistItemTemplate(Base):
    __tablename__ = "checklist_item_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # The item name shown on the inspection form
    item_name = Column(String, nullable=False)

    # Display order in the inspection form
    sort_order = Column(Integer, default=0)

    # True for system-seeded items (the 13 defaults), False for org-added
    # Even default items can still be edited or deleted by the landlord
    is_default = Column(Boolean, default=False)

    # Soft toggle — landlord can disable an item without deleting it
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    organization = relationship("Organization")
