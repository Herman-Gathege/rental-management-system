from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import json

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.audit_log import AuditLog
from fastapi import HTTPException

router = APIRouter(prefix="/audit", tags=["Audit Log"])


def get_user_org(user: User, db: Session):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == user.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="No organization found")
    return membership


@router.get("/")
def list_audit_logs(
    entity_type: str = Query(None, description="Filter: property, unit, tenant, lease, charge, payment"),
    entity_id: str = Query(None),
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    membership = get_user_org(current_user, db)

    query = db.query(AuditLog).filter(
        AuditLog.organization_id == membership.organization_id
    )

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)

    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    return [
        {
            "id": l.id,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "description": l.description,
            "old_values": json.loads(l.old_values) if l.old_values else None,
            "new_values": json.loads(l.new_values) if l.new_values else None,
            "user_email": l.user.email if l.user else None,
            "created_at": l.created_at,
        }
        for l in logs
    ]
