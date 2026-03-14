"""
Razorpay service — handles Payment Link creation, fetching, and webhook verification.
"""

from __future__ import annotations

import hashlib
import hmac
import logging

import razorpay

from app.config import get_settings

logger = logging.getLogger(__name__)


class RazorpayService:
    """Thin wrapper around the Razorpay Python SDK for Payment Links."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = razorpay.Client(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
        )
        self._webhook_secret = settings.razorpay_webhook_secret
        logger.info("Razorpay service initialised ✓")

    # ------------------------------------------------------------------ #
    #  Payment Links
    # ------------------------------------------------------------------ #

    def create_payment_link(
        self,
        *,
        name: str,
        email: str,
        amount: float,
        description: str,
        min_partial_amount: float | None = None,
    ) -> dict:
        """
        Create a Razorpay Payment Link.

        Args:
            name: Customer name
            email: Customer email
            amount: Amount in rupees (converted to paise internally)
            description: Brief description shown on checkout
            min_partial_amount: If set, allows partial payments starting at this amount.

        Returns:
            Raw Razorpay API response dict with keys like
            id, short_url, amount, status, etc.
        """
        amount_paise = int(round(amount * 100))

        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "description": description,
            "customer": {
                "name": name,
                "email": email,
            },
            "notify": {
                "sms": False,
                "email": False,  # We handle emails ourselves
            },
            "reminder_enable": False,
            "callback_method": "get",
        }

        if min_partial_amount is not None:
            payload["accept_partial"] = True
            payload["first_min_partial_amount"] = int(round(min_partial_amount * 100))

        result = self._client.payment_link.create(payload)
        logger.info(
            "Created payment link %s for %s — ₹%s",
            result.get("id"),
            name,
            amount,
        )
        return result

    def fetch_payment_link(self, link_id: str) -> dict:
        """Fetch current state of a payment link by its ID."""
        return self._client.payment_link.fetch(link_id)

    def cancel_payment_link(self, link_id: str) -> dict:
        """Cancel an active payment link."""
        result = self._client.payment_link.cancel(link_id)
        logger.info("Cancelled payment link %s", link_id)
        return result

    # ------------------------------------------------------------------ #
    #  Webhook verification
    # ------------------------------------------------------------------ #

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """
        Verify the X-Razorpay-Signature header using HMAC SHA256.

        Returns True if the signature is valid.
        """
        if not self._webhook_secret:
            logger.warning("Webhook secret not configured — skipping verification")
            return True

        expected = hmac.new(
            self._webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)
