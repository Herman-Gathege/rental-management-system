#backend\app\services\messaging\__init__.py
# Messaging package — central communication engine for the platform.
#
# This package provides a provider-agnostic messaging interface. WhatsApp
# is the current provider; SMS, email, or other channels can be added by
# implementing BaseMessagingProvider and swapping it in messaging_service.py.

from app.services.messaging.messaging_service import (
    send_notification,
    send_template_message,
    send_freeform_message,
)
