"""Email API router — manual reminder endpoint."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.models.email import SendReminderRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["Email"])


def _get_email_service():
    from app.main import email_service  # noqa: WPS433

    if email_service is None:
        raise HTTPException(status_code=503, detail="Email service not ready")
    return email_service


def _get_sheets():
    from app.main import sheets_service  # noqa: WPS433

    if sheets_service is None:
        raise HTTPException(status_code=503, detail="Sheets service not ready")
    return sheets_service


@router.post("/reminder", status_code=200)
def send_reminder(data: SendReminderRequest):
    """
    Send a payment reminder email.

    Only `customer_email` is required — name, amount, payment URL,
    due date etc. are looked up from the Payments sheet automatically.

    - level 1 = Polite (Day 3 tone)
    - level 2 = Firm / Final Notice (Day 7 tone)

    Also updates `last_reminder_at` in the sheet.
    """
    sheets = _get_sheets()
    email_svc = _get_email_service()

    # Find all pending payments for this email
    payments = sheets.find_payments_by_email(data.customer_email)
    pending = [p for p in payments if p.status in ("pending", "partial") and p.razorpay_link_url]

    if not pending:
        raise HTTPException(
            status_code=404,
            detail=f"No pending payments with a payment link found for '{data.customer_email}'",
        )

    sent_count = 0
    all_sheet_payments = sheets.get_all_payments()

    for payment in pending:
        try:
            # Calculate remaining balance for the reminder
            amount_due = payment.amount
            if payment.status == "partial":
                amount_due = payment.amount - payment.amount_paid
                if amount_due <= 0:
                    continue  # Shouldn't happen, but just in case

            email_svc.send_reminder_email(
                customer_name=payment.name,
                customer_email=payment.email,
                amount=amount_due,
                description=payment.description,
                payment_url=payment.razorpay_link_url,
                due_date=payment.due_date,
                reminder_level=data.reminder_level,
            )

            # Update last_reminder_at in the sheet
            from app.models.payment import PaymentUpdate

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            for idx, sp in enumerate(all_sheet_payments, start=2):
                if sp.razorpay_link_id == payment.razorpay_link_id:
                    sheets.update_payment(
                        idx,
                        PaymentUpdate(last_reminder_at=f"{now_str}|{data.reminder_level}"),
                    )
                    break

            sent_count += 1
        except Exception:
            logger.exception("Failed to send reminder to %s", payment.email)

    return {
        "status": "sent",
        "to": data.customer_email,
        "reminders_sent": sent_count,
        "level": data.reminder_level,
    }

