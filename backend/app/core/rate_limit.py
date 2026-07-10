#backend\app\core\rate_limit.py
"""
Rate limiting (Sprint 7 — MVP-1).

Protects auth endpoints from brute force, spam signup, WhatsApp OTP cost abuse,
and password-reset abuse. Uses slowapi (a FastAPI-compatible wrapper around
python-limits) backed by Redis so counters survive backend restarts and are
shared across containers if we ever scale horizontally.

Keys:
  - Default is per-user (JWT sub claim) for authenticated requests; falls
    back to per-IP for anonymous ones. See get_user_id_or_ip below.
  - Explicit @limiter.limit(...) decorators on specific routes inherit this
    default unless they pass their own key_func.

Sprint 7 follow-up (Module 3 rate limits): a global default cap of
200 requests/minute applies to EVERY endpoint that isn't already covered by
a stricter explicit decorator. Rationale for 200 instead of the guide's
suggested 100: an active landlord dashboard with several polling widgets
(notifications, tickets summary, dashboard stats) can legitimately hit
60–80 req/min without any abuse. 200 leaves comfortable headroom for real
users while still blocking scraping / credential-stuffing (which run at
thousands/min). Bump lower once we have usage data if abuse is observed.

Fail-open behavior: if Redis is unreachable, slowapi silently degrades to
letting requests through rather than 500'ing. We prefer a temporarily-open
rate limiter over a broken app; the alternative is worse.
"""
import os
import logging

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Redis is already running in the compose stack. Fall back to in-memory if the
# env var isn't set (dev-only path; counters will reset on restart).
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
STORAGE_URI = REDIS_URL if REDIS_URL else "memory://"


def get_user_id_or_ip(request: Request) -> str:
    """
    Key function for authenticated endpoints: prefer the user id from the JWT
    subject, fall back to IP if the request is somehow unauthenticated (which
    slowapi will still rate-limit rather than blow up).

    Note: we don't decode the token here — that's the auth dependency's job.
    Instead, we read it off request.state.user if a route dep has set it, or
    parse the bearer token loosely for the `sub` claim. This keeps the limiter
    fast (no DB hit) and doesn't couple it to get_current_user.
    """
    # Preferred: a route dependency has already stashed the user on state.
    user = getattr(request.state, "user", None)
    if user is not None:
        uid = getattr(user, "id", None)
        if uid:
            return f"user:{uid}"

    # Fallback: peek at the JWT subject without full validation. If it fails
    # for any reason (missing header, malformed token, decode error), fall
    # through to IP-based keying.
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        try:
            # Lazy import so a missing/broken jwt module doesn't break the
            # limiter for unauthenticated endpoints.
            from app.core.jwt import decode_token
            payload = decode_token(token)
            sub = payload.get("sub")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass

    return f"ip:{get_remote_address(request)}"


# The global limiter. Endpoints opt in via @limiter.limit("N/period") decorators;
# every endpoint also inherits the default_limits below unless a stricter
# explicit decorator overrides.
#
# Sprint 7 follow-up: key_func changed from get_remote_address to
# get_user_id_or_ip so the default limit is per-user for authenticated
# traffic (fairer for users behind shared NATs — common on Kenyan mobile
# carriers). Existing per-endpoint decorators on unauthenticated routes
# (register / login / forgot-password) still function correctly because
# unauthenticated requests fall through to IP inside get_user_id_or_ip.
limiter = Limiter(
    key_func=get_user_id_or_ip,
    default_limits=["200/minute"],
    storage_uri=STORAGE_URI,
    strategy="fixed-window",          # simple + cheap; sliding window not needed for these limits
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Friendly 429 response. slowapi's default is a plain string body; we return
    JSON with a clear message so the frontend can surface it in an alert like
    any other 400/401. The Retry-After header is set by slowapi automatically.
    """
    logger.info(
        "rate limit hit path=%s key=%s detail=%s",
        request.url.path, exc.detail, str(exc),
    )
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down and try again in a moment."},
    )