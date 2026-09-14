# backend/app/models/automation_run.py
"""
Audit trail for scheduled automation runs.

Every execution of a scheduled job writes one row per organisation, including
runs that found nothing to do and runs that failed. This is what makes the
automations diagnosable: an operator can answer "did the reminder job run on
the 10th, and why did it skip tenant X?" without grepping container logs.

The (organization_id, job, run_date) uniqueness is the first layer of
idempotency — a job that is retried on the same day for the same org cannot
record a second successful run, and the caller checks this row before doing
any work.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


JOB_INVOICE_GENERATION = "invoice_generation"
JOB_PAYMENT_REMINDER = "payment_reminder"

STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"


class AutomationRun(Base):
    __tablename__ = "automation_runs"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "job",
            "run_date",
            name="uq_automation_run_org_job_date",
        ),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(
        String,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job = Column(String, nullable=False)
    run_date = Column(Date, nullable=False)

    status = Column(String, nullable=False, default=STATUS_SUCCESS)
    processed = Column(Integer, nullable=False, default=0)
    created_count = Column(Integer, nullable=False, default=0)
    skipped_count = Column(Integer, nullable=False, default=0)
    notified_count = Column(Integer, nullable=False, default=0)
    message = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    organization = relationship("Organization")
