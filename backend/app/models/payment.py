from pydantic import BaseModel, EmailStr
from typing import Literal


class Payment(BaseModel):
    """A payment record from the Payments sheet."""

    name: str
    email: EmailStr
    amount: float
    description: str
    razorpay_link_id: str | None = None
    razorpay_link_url: str | None = None
    status: Literal["pending", "partial", "paid", "failed"] = "pending"
    amount_paid: float = 0.0
    due_date: str | None = None
    created_at: str = ""
    last_reminder_at: str | None = None
    notes: str | None = None


class PaymentCreate(BaseModel):
    """Request body for creating a new payment record."""

    name: str
    email: EmailStr
    amount: float
    min_partial_amount: float | None = None
    description: str
    due_date: str | None = None
    notes: str | None = None


class PaymentUpdate(BaseModel):
    """Request body for updating a payment record. All fields optional."""

    razorpay_link_id: str | None = None
    razorpay_link_url: str | None = None
    status: Literal["pending", "partial", "paid", "failed"] | None = None
    amount_paid: float | None = None
    due_date: str | None = None
    last_reminder_at: str | None = None
    notes: str | None = None
