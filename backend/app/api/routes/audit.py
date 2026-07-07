#backend\app\api\routes\audit.py
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


def _serialize(l: AuditLog) -> dict:
    return {
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


@router.get("/")
def list_audit_logs(
    entity_type: str = Query(None, description="Filter: property, unit, tenant, lease, charge, payment"),
    entity_id: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(None, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List audit logs.

    Pagination (Sprint 6.2 #3): when `offset` is provided, returns a paginated
    envelope { items, total, limit, offset }. When `offset` is omitted, returns
    the bare list (unchanged, limited to `limit`) so existing callers keep
    working. `limit` doubles as the page size.
    """
    membership = get_user_org(current_user, db)

    query = db.query(AuditLog).filter(
        AuditLog.organization_id == membership.organization_id
    )

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)

    query = query.order_by(AuditLog.created_at.desc())

    # Paginated envelope when offset is given.
    if offset is not None:
        total = query.count()
        logs = query.offset(offset).limit(limit).all()
        return {
            "items": [_serialize(l) for l in logs],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    # Backward-compatible bare list (limited to `limit`).
    logs = query.limit(limit).all()
    return [_serialize(l) for l in logs]