"""Pydantic models for email requests."""

from pydantic import BaseModel, EmailStr


class SendReminderRequest(BaseModel):
    """
    Request to send a payment reminder.
    Only email is required — name, amount, payment_url etc.
    are looked up from the Payments sheet automatically.
    """

    customer_email: EmailStr
    reminder_level: int = 1  # 1 = polite (Day 3), 2 = firm (Day 7)
