# backend\app\services\messaging\__init__.py
# Messaging package - central communication engine for the platform.
#
# This package provides a provider-agnostic messaging interface. WhatsApp
# is the current provider; SMS, email, or other channels can be added by
# implementing BaseMessagingProvider and swapping it in messaging_service.py.

from app.services.messaging.messaging_service import (
    send_notification,
    send_template_message,
    send_freeform_message,
)

# Event-driven notification helpers (Phase 3).
# These are designed to be invoked via FastAPI's BackgroundTasks from route
# handlers, so HTTP responses don't block on WhatsApp API calls.
from app.services.messaging.notifications import (
    notify_lease_created,
    notify_payment_received,
    notify_rent_due_for_charges,
    notify_org_invite,
)
