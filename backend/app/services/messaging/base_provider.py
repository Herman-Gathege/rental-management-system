#backend\app\services\messaging\base_provider.py
"""
Abstract base class for messaging providers.

To add a new channel (SMS, email, etc.), create a new module that
implements this interface and register it in messaging_service.py.

Each provider is responsible for:
  - converting our internal payload into the provider's API format
  - making the HTTP call
  - returning a normalized result the messaging service can persist
"""
from abc import ABC, abstractmethod
from typing import Optional


class BaseMessagingProvider(ABC):
    """Interface every messaging provider must implement."""

    @abstractmethod
    def send_template(
        self,
        to_phone: str,
        template_name: str,
        template_params: list,
        language_code: str = "en_US",
    ) -> dict:
        """
        Send a pre-approved template message.

        Args:
            to_phone: E.164 phone number (e.g. "+254712345678")
            template_name: Name of the template as registered with the provider
            template_params: Ordered list of values to fill the template's variables
            language_code: Language code for the template (e.g. "en_US", "sw")

        Returns:
            {
                "provider_message_id": "...",
                "status": "sent",
                "raw_response": {...}
            }

        Raises:
            MessagingProviderError on failure.
        """
        ...

    @abstractmethod
    def send_freeform_text(self, to_phone: str, body: str) -> dict:
        """
        Send a free-form text message.

        For WhatsApp, this only works within the 24-hour customer service window
        (i.e. after the user has messaged you recently). Outside that window,
        only template messages are allowed.

        Args:
            to_phone: E.164 phone number
            body: The message text

        Returns:
            Same shape as send_template().
        """
        ...

    @abstractmethod
    def validate_webhook_signature(self, raw_body: bytes, signature_header: str) -> bool:
        """
        Verify that an incoming webhook actually came from the provider.

        Used in Phase 2 (inbound messages).
        """
        ...


class MessagingProviderError(Exception):
    """Raised by providers when sending fails."""

    def __init__(self, message: str, raw_response: Optional[dict] = None):
        super().__init__(message)
        self.raw_response = raw_response or {}
