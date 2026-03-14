"""Pydantic models for Razorpay Payment Links."""

from pydantic import BaseModel, EmailStr


class CreatePaymentLinkRequest(BaseModel):
    """Request body for creating a Razorpay payment link."""

    name: str
    email: EmailStr
    amount: float  # in rupees (we convert to paise internally)
    min_partial_amount: float | None = None  # in rupees
    description: str
    due_date: str | None = None  # YYYY-MM-DD
    notes: str | None = None


class PaymentLinkResponse(BaseModel):
    """Response after creating or fetching a payment link."""

    link_id: str
    short_url: str
    amount: float  # in rupees
    currency: str = "INR"
    status: str  # created, partially_paid, paid, cancelled, expired
    customer_name: str | None = None
    customer_email: str | None = None
    description: str | None = None
    amount_paid: float = 0.0  # in rupees


class PaymentLinkSyncResponse(BaseModel):
    """Response after syncing a payment link status."""

    link_id: str
    status: str
    amount: float
    amount_paid: float
    sheet_updated: bool = False
