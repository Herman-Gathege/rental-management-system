#backend\app\api\routes\notifications.py
"""
Notification routes — Sprint 6.

  GET  /notifications                  list unread (or all) for current user
  PUT  /notifications/{id}/read        mark one as read
  PUT  /notifications/read-all         mark all as read
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.organization_member import OrganizationMember
from app.models.notification import Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


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


def _enrich(n: Notification) -> dict:
    return {
        "id": n.id,
        "title": n.title,
        "body": n.body,
        "notification_type": n.notification_type,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


@router.get("/")
def list_notifications(
    unread_only: bool = Query(False, description="Return only unread notifications"),
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    q = db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.organization_id == membership.organization_id,
    )
    if unread_only:
        q = q.filter(Notification.is_read == False)  # noqa: E712
    notifications = q.order_by(Notification.created_at.desc()).limit(50).all()
    return [_enrich(n) for n in notifications]


@router.put("/read-all")
def mark_all_read(deps=Depends(get_user_org)):
    """Mark all notifications as read for the current user."""
    user, membership, db = deps
    db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.organization_id == membership.organization_id,
        Notification.is_read == False,  # noqa: E712
    ).update({"is_read": True})
    db.commit()
    return {"detail": "All notifications marked as read"}


@router.put("/{notification_id}/read")
def mark_read(
    notification_id: str,
    deps=Depends(get_user_org),
):
    user, membership, db = deps
    n = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user.id,
        )
        .first()
    )
    if not n:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found")
    n.is_read = True
    db.commit()
    return _enrich(n)
