#backend\app\models\tenant_document.py
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class TenantDocument(Base):
    __tablename__ = "tenant_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    # Type of document being stored
    # Allowed values: national_id_front, national_id_back, passport_biodata, other
    document_type = Column(String, nullable=False)

    # S3 details
    file_url = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)

    uploaded_by_user_id = Column(String, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    uploaded_by = relationship("User")
