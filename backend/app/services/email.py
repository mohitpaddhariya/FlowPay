"""
Email service — sends HTML emails via SMTP with embedded FlowPay logo.
Uses Python built-in smtplib + email.mime (no extra dependencies).
"""

from __future__ import annotations

import logging
import smtplib
from datetime import datetime, timezone
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
LOGO_PATH = Path(__file__).resolve().parent.parent.parent / "public" / "flowplay.png"

REMINDER_MESSAGES = {
    1: (
        "Just floating this to the top of your inbox. Your payment of "
        "₹<strong>{{amount}}</strong> for <strong>{{description}}</strong> "
        "is currently pending."
        "<br/><br/>"
        "If you've already made this payment and it's crossing paths with "
        "this email, please let us know!"
    ),
    2: (
        "This is a reminder that your payment of "
        "₹<strong>{{amount}}</strong> for <strong>{{description}}</strong> "
        "is now overdue."
        "<br/><br/>"
        "Please clear this balance at your earliest convenience to ensure "
        "uninterrupted service."
        "<br/><br/>"
        "Let us know if you are facing any issues processing the payment."
    ),
    3: (
        "This is a <strong>final notice</strong> regarding your pending payment "
        "of ₹<strong>{{amount}}</strong> for <strong>{{description}}</strong>."
        "<br/><br/>"
        "Please settle the outstanding balance immediately to avoid "
        "any service disruption or further action."
        "<br/><br/>"
        "If you've already made this payment, please disregard this message "
        "and accept our apologies for the inconvenience."
    ),
}


class EmailService:
    """Sends branded HTML emails via SMTP."""

    def __init__(self) -> None:
        settings = get_settings()
        self._host = settings.smtp_host
        self._port = settings.smtp_port
        self._username = settings.smtp_username
        self._password = settings.smtp_password
        self._from_email = settings.from_email
        self._business_name = settings.business_name

        # Pre-load templates
        self._payment_link_tpl = (TEMPLATES_DIR / "payment_link.html").read_text()
        self._receipt_tpl = (TEMPLATES_DIR / "payment_receipt.html").read_text()
        self._reminder_tpl = (TEMPLATES_DIR / "payment_reminder.html").read_text()

        # Pre-load logo
        self._logo_data: bytes | None = None
        if LOGO_PATH.exists():
            self._logo_data = LOGO_PATH.read_bytes()

        logger.info("Email service initialised ✓")

    # ------------------------------------------------------------------ #
    #  Internal helpers
    # ------------------------------------------------------------------ #

    def _build_message(
        self,
        *,
        to_email: str,
        subject: str,
        html_body: str,
    ) -> MIMEMultipart:
        """Build a MIME message with inline logo."""
        msg = MIMEMultipart("related")
        msg["From"] = f"{self._business_name} <{self._from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        # HTML part
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Inline logo image
        if self._logo_data:
            img = MIMEImage(self._logo_data, _subtype="png")
            img.add_header("Content-ID", "<flowpay_logo>")
            img.add_header("Content-Disposition", "inline", filename="flowpay.png")
            msg.attach(img)

        return msg

    def _send(self, msg: MIMEMultipart) -> None:
        """Send message via SMTP."""
        try:
            with smtplib.SMTP(self._host, self._port) as server:
                server.starttls()
                server.login(self._username, self._password)
                server.send_message(msg)
            logger.info("Email sent to %s — %s", msg["To"], msg["Subject"])
        except Exception:
            logger.exception("Failed to send email to %s", msg["To"])
            raise

    def _render(self, template: str, **kwargs: str) -> str:
        """Simple template variable replacement."""
        html = template
        # Always inject business_name
        kwargs.setdefault("business_name", self._business_name)
        for key, value in kwargs.items():
            html = html.replace("{{" + key + "}}", str(value))
        return html

    # ------------------------------------------------------------------ #
    #  Public methods
    # ------------------------------------------------------------------ #

    def send_payment_link_email(
        self,
        *,
        customer_name: str,
        customer_email: str,
        amount: float,
        description: str,
        payment_url: str,
        due_date: str | None = None,
    ) -> None:
        """Send payment link email to customer."""
        html = self._render(
            self._payment_link_tpl,
            customer_name=customer_name,
            amount=f"{amount:,.2f}",
            description=description,
            payment_url=payment_url,
            due_date=due_date or "On receipt",
        )
        subject = f"Invoice from {self._business_name}: {description}"
        msg = self._build_message(to_email=customer_email, subject=subject, html_body=html)
        self._send(msg)

    def send_receipt_email(
        self,
        *,
        customer_name: str,
        customer_email: str,
        amount_paid: float,
        description: str,
    ) -> None:
        """Send payment receipt email to customer."""
        now = datetime.now(timezone.utc).strftime("%d %b %Y")
        html = self._render(
            self._receipt_tpl,
            customer_name=customer_name,
            amount_paid=f"{amount_paid:,.2f}",
            description=description,
            paid_at=now,
        )
        subject = f"Payment Received — {self._business_name}"
        msg = self._build_message(to_email=customer_email, subject=subject, html_body=html)
        self._send(msg)

    def send_reminder_email(
        self,
        *,
        customer_name: str,
        customer_email: str,
        amount: float,
        description: str,
        payment_url: str,
        due_date: str | None = None,
        reminder_level: int = 1,
    ) -> None:
        """Send payment reminder email (level 1=polite Day 3, 2=firm Day 7, 3=final Day 14)."""
        level = max(1, min(3, reminder_level))
        reminder_message = REMINDER_MESSAGES[level].replace(
            "{{description}}", description
        ).replace(
            "{{amount}}", f"{amount:,.2f}"
        )
        html = self._render(
            self._reminder_tpl,
            customer_name=customer_name,
            amount=f"{amount:,.2f}",
            description=description,
            payment_url=payment_url,
            due_date=due_date or "Overdue",
            reminder_message=reminder_message,
        )
        subjects = {
            1: f"Reminder: Pending payment for {description}",
            2: f"Action Required: Overdue invoice from {self._business_name}",
            3: f"Final Notice: {description} — {self._business_name}",
        }
        subject = subjects[level]
        msg = self._build_message(to_email=customer_email, subject=subject, html_body=html)
        self._send(msg)

    def send_partial_payment_email(
        self,
        *,
        customer_name: str,
        customer_email: str,
        current_amount: float,
        total_amount_paid: float,
        total_invoice_amount: float,
        description: str,
        payment_url: str,
    ) -> None:
        """Notify customer of partial payment and remaining balance."""
        balance = total_invoice_amount - total_amount_paid
        now = datetime.now(timezone.utc).strftime("%d %b %Y")
        html = self._render(
            self._receipt_tpl,
            customer_name=customer_name,
            amount_paid=f"{current_amount:,.2f}",
            description=f"{description} (partial — total paid: ₹{total_amount_paid:,.2f}, balance: ₹{balance:,.2f})",
            paid_at=now,
        )
        subject = f"Received ₹{current_amount:,.2f}, balance ₹{balance:,.2f} still pending"
        msg = self._build_message(to_email=customer_email, subject=subject, html_body=html)
        self._send(msg)

    def send_owner_summary(
        self,
        *,
        customer_name: str,
        current_amount: float,
        total_amount_paid: float,
        description: str,
        status: str,
    ) -> None:
        """Send a brief internal summary to the business owner."""
        # Note: current_amount is what was just paid, total_amount_paid is cumulative
        status_label = "✓ Paid in full" if status == "paid" else f"Partial — ₹{current_amount:,.2f} received"
        html = (
            f"<div style='font-family:-apple-system,BlinkMacSystemFont,\"Inter\",\"Segoe UI\",Roboto,Helvetica,Arial,sans-serif;max-width:480px;margin:auto;padding:32px;background-color:#ffffff;border:1px solid #e5e7eb;border-radius:16px;color:#111827;'>"
            f"<div style='margin-bottom:24px;'>"
            f"<span style='display:inline-block;background-color:#0f172a;color:#ffffff;font-size:12px;font-weight:600;padding:4px 10px;border-radius:6px;margin-bottom:12px;'>Internal Update</span>"
            f"<h3 style='margin:0;font-size:18px;font-weight:600;letter-spacing:-0.5px;'>{customer_name}</h3>"
            f"<p style='margin:4px 0 0 0;font-size:14px;color:#6b7280;'>{status_label}</p>"
            f"</div>"
            f"<div style='height:1px;background-color:#f3f4f6;width:100%;margin-bottom:24px;'></div>"
            f"<table style='width:100%;border-collapse:collapse;font-size:14px;'>"
            f"<tr><td style='padding:12px 0;color:#6b7280;border-bottom:1px solid #f9fafb;'>Amount Just Paid</td>"
            f"<td style='padding:12px 0;text-align:right;font-weight:600;color:#059669;border-bottom:1px solid #f9fafb;'>₹{current_amount:,.2f}</td></tr>"
            f"<tr><td style='padding:12px 0;color:#6b7280;border-bottom:1px solid #f9fafb;'>Total Paid To Date</td>"
            f"<td style='padding:12px 0;text-align:right;font-weight:500;border-bottom:1px solid #f9fafb;'>₹{total_amount_paid:,.2f}</td></tr>"
            f"<tr><td style='padding:12px 0;color:#6b7280;'>For</td>"
            f"<td style='padding:12px 0;text-align:right;font-weight:500;'>{description}</td></tr>"
            f"</table>"
            f"<div style='margin-top:32px;text-align:center;'>"
            f"<p style='margin:0;font-size:12px;color:#9ca3af;font-weight:500;'>Powered by ⚡️ FlowPay</p>"
            f"</div>"
            f"</div>"
        )
        subject = f"💰 {customer_name} paid ₹{current_amount:,.2f} — {description}"
        msg = self._build_message(to_email=self._from_email, subject=subject, html_body=html)
        self._send(msg)

