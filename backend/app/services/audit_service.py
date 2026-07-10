#backend\app\services\audit_service.py
"""
Audit log service.

log_action() writes one row per audited event. Rows are added to the caller's
DB session but NOT committed here — the caller commits alongside the domain
change so audit is atomic with the action being logged.

get_client_ip() extracts a request's client IP, honoring X-Forwarded-For if
present. Used by auth-event audit calls so the log records where the request
came from, not the reverse-proxy's IP.

Sprint 7 follow-up added:
  - Optional ip_address parameter (older callers don't set it → null column)
  - Nullable organization_id support (auth events like failed-login-with-
    unknown-email have no org context)
"""
import uuid
import json
from typing import Optional
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    organization_id: Optional[str],
    user_id: Optional[str],
    action: str,
    entity_type: str,
    entity_id: str,
    description: str,
    old_values: dict = None,
    new_values: dict = None,
    ip_address: Optional[str] = None,
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
        ip_address=ip_address,
    )
    db.add(entry)


def get_client_ip(request) -> Optional[str]:
    """Best-effort client IP for audit logging.

    Prefers the first entry in X-Forwarded-For (the ORIGINAL client when a
    reverse proxy / load balancer sits in front); falls back to
    request.client.host for direct connections. Returns None if neither is
    available (should be rare).

    Trust model note: X-Forwarded-For is client-settable. In dev/local this
    is fine. In prod, only accept it when the request is coming from a
    trusted proxy — that's a deployment concern (uvicorn / nginx config),
    not this function.
    """
    xff = request.headers.get("x-forwarded-for", "").strip()
    if xff:
        return xff.split(",")[0].strip() or None
    if request.client:
        return request.client.host
    return None
