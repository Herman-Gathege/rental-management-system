#backend\app\api\routes\ticket_metrics.py
"""
Ticket metrics route — Sprint 6, Chunk 7.

  GET /tickets/metrics/summary   role-scoped dashboard metrics

Mounted on its own router (prefix /tickets/metrics) to avoid touching the
main tickets router. Registered in main.py.

NOTE: the path is /tickets/metrics/summary (not /tickets/metrics) so it can
never collide with the /tickets/{ticket_id} detail route in the other router.
"""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.tenant import Tenant
from app.services import ticket_metrics_service

router = APIRouter(prefix="/tickets/metrics", tags=["Ticket Metrics"])


def get_user_org(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = (
        db.query(OrganizationMember)
        .filter(OrganizationMember.user_id == current_user.id)
        .first()
    )
    if not membership:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="No organization membership")
    return current_user, membership, db


def _tenant_id(user: User, membership: OrganizationMember, db: Session) -> Optional[str]:
    from app.core.roles import TENANT
    if membership.role.name != TENANT:
        return None
    tenant = db.query(Tenant).filter(Tenant.user_id == user.id).first()
    return tenant.id if tenant else None


@router.get("/summary")
def metrics_summary(deps=Depends(get_user_org)):
    user, membership, db = deps
    tid = _tenant_id(user, membership, db)
    return ticket_metrics_service.get_metrics(
        db, membership.organization_id, user.id, membership, tenant_id=tid
    )
