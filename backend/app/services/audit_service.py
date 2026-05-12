import uuid
import json
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    organization_id: str,
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    description: str,
    old_values: dict = None,
    new_values: dict = None,
):
    entry = AuditLog(
        id=str(uuid.uuid4()),
        organization_id=organization_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        old_values=json.dumps(old_values) if old_values else None,
        new_values=json.dumps(new_values) if new_values else None,
    )
    db.add(entry)
