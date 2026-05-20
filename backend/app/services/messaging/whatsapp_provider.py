#backend\app\services\messaging\whatsapp_provider.py
"""
Meta WhatsApp Cloud API provider.

Implements BaseMessagingProvider for the official Meta WhatsApp Cloud API.
All Meta-specific quirks (phone formatting, payload shape, webhook signature
verification, error codes) live in this file. The rest of the system stays
provider-agnostic.

Docs: https://developers.facebook.com/docs/whatsapp/cloud-api
"""
import os
import hmac
import hashlib
import requests
from typing import Optional
from app.services.messaging.base_provider import (
    BaseMessagingProvider,
    MessagingProviderError,
)


# Meta's Graph API version — pin a known version so they can't break us
GRAPH_API_VERSION = "v25.0"
GRAPH_API_BASE = "https://graph.facebook.com"


class WhatsAppProvider(BaseMessagingProvider):
    """Sends and validates messages via Meta's WhatsApp Cloud API."""

    def __init__(self):
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.app_secret = os.getenv("WHATSAPP_APP_SECRET")  # used for webhook signing

        if not self.phone_number_id or not self.access_token:
            raise MessagingProviderError(
                "WhatsApp provider not configured. "
                "Set WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN."
            )

        self.endpoint = f"{GRAPH_API_BASE}/{GRAPH_API_VERSION}/{self.phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    # ─── Helpers ───

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normalize a phone number to Meta-friendly format.

        Meta expects digits-only with country code, no '+' prefix.
        e.g. "+254 704 072 784" → "254704072784"
        """
        default_country = os.getenv("WHATSAPP_DEFAULT_COUNTRY_CODE", "254")

        # Strip everything that isn't a digit
        digits = "".join(c for c in phone if c.isdigit())

        # If it starts with the country code, leave as-is
        if digits.startswith(default_country):
            return digits

        # If it starts with 0 (local Kenyan format like 0712...),
        # replace leading 0 with country code
        if digits.startswith("0"):
            return default_country + digits[1:]

        # Otherwise prepend the country code as a best-effort default
        return default_country + digits

    def _post(self, payload: dict) -> dict:
        """Make the HTTP call and normalize the response."""
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=15,
            )
        except requests.RequestException as e:
            raise MessagingProviderError(
                f"HTTP request to WhatsApp failed: {str(e)}"
            )

        try:
            data = response.json()
        except ValueError:
            raise MessagingProviderError(
                f"WhatsApp returned non-JSON response (status {response.status_code})"
            )

        # Meta returns 200 OK on success, error payload on failure
        if response.status_code != 200 or "error" in data:
            error_msg = data.get("error", {}).get("message", "Unknown error")
            raise MessagingProviderError(
                f"WhatsApp API error: {error_msg}",
                raw_response=data,
            )

        # Extract the message ID Meta assigned
        messages = data.get("messages", [])
        provider_message_id = messages[0]["id"] if messages else None

        return {
            "provider_message_id": provider_message_id,
            "status": "sent",
            "raw_response": data,
        }

    # ─── Template messages ───

    def send_template(
        self,
        to_phone: str,
        template_name: str,
        template_params: list,
        language_code: str = "en_US",
    ) -> dict:
        """
        Send a pre-approved template message.

        Template parameters are positional — they fill {{1}}, {{2}}, etc. in
        the template body in order. If your template has no parameters, pass
        an empty list.
        """
        normalized_to = self.normalize_phone(to_phone)

        # Build the parameters array if any params were provided
        components = []
        if template_params:
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(p)} for p in template_params
                    ],
                }
            ]

        payload = {
            "messaging_product": "whatsapp",
            "to": normalized_to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }

        if components:
            payload["template"]["components"] = components

        return self._post(payload)

    # ─── Free-form text ───

    def send_freeform_text(self, to_phone: str, body: str) -> dict:
        """
        Send a free-form text message.

        Important: Meta requires this to be inside the 24-hour service window
        (i.e. the recipient must have messaged you in the last 24h), or the
        recipient is on Meta's test-number allow-list.
        """
        normalized_to = self.normalize_phone(to_phone)

        payload = {
            "messaging_product": "whatsapp",
            "to": normalized_to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": body,
            },
        }

        return self._post(payload)

    # ─── Webhook signature verification (Phase 2) ───

    def validate_webhook_signature(self, raw_body: bytes, signature_header: str) -> bool:
        """
        Verify a webhook payload against Meta's X-Hub-Signature-256 header.

        Meta signs every webhook with HMAC-SHA256 using the app secret.
        We compute the expected signature and compare.

        For Phase 1 this is unused but defined for completeness.
        """
        if not self.app_secret or not signature_header:
            return False

        # Meta sends "sha256=abc123..." — strip the prefix
        if not signature_header.startswith("sha256="):
            return False

        provided_signature = signature_header.split("=", 1)[1]

        expected_signature = hmac.new(
            self.app_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(provided_signature, expected_signature)
