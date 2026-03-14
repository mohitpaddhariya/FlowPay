"""Razorpay API router — payment links, sync, and webhooks."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.razorpay import (
    CreatePaymentLinkRequest,
    PaymentLinkResponse,
    PaymentLinkSyncResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/razorpay", tags=["Razorpay"])


# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #


def _get_razorpay():
    from app.main import razorpay_service  # noqa: WPS433

    if razorpay_service is None:
        raise HTTPException(status_code=503, detail="Razorpay service not ready")
    return razorpay_service


def _get_sheets():
    from app.main import sheets_service  # noqa: WPS433

    if sheets_service is None:
        raise HTTPException(status_code=503, detail="Sheets service not ready")
    return sheets_service


def _get_email():
    from app.main import email_service  # noqa: WPS433

    return email_service  # Can be None — emails are best-effort


def _paise_to_rupees(paise: int) -> float:
    return round(paise / 100, 2)


def _parse_link(raw: dict) -> PaymentLinkResponse:
    """Convert raw Razorpay API response to our Pydantic model."""
    customer = raw.get("customer", {}) or {}
    return PaymentLinkResponse(
        link_id=raw["id"],
        short_url=raw.get("short_url", ""),
        amount=_paise_to_rupees(raw.get("amount", 0)),
        currency=raw.get("currency", "INR"),
        status=raw.get("status", "unknown"),
        customer_name=customer.get("name"),
        customer_email=customer.get("email"),
        description=raw.get("description"),
        amount_paid=_paise_to_rupees(raw.get("amount_paid", 0)),
    )


# ------------------------------------------------------------------ #
#  Payment Link CRUD
# ------------------------------------------------------------------ #


@router.post("/payment-links", response_model=PaymentLinkResponse, status_code=201)
def create_payment_link(data: CreatePaymentLinkRequest):
    """
    Create a Razorpay payment link and record it in Google Sheets.

    Flow:
    1. Creates a new payment record in the Payments sheet (if not exists).
    2. Calls Razorpay to create the payment link.
    3. Updates the sheet row with razorpay_link_id and razorpay_link_url.
    """
    rz = _get_razorpay()
    sheets = _get_sheets()

    # Step 1: Create payment row in Sheets
    from app.models.payment import PaymentCreate, PaymentUpdate

    payment = sheets.add_payment(
        PaymentCreate(
            name=data.name,
            email=data.email,
            amount=data.amount,
            description=data.description,
            due_date=data.due_date,
            notes=data.notes,
        )
    )

    # Step 2: Create Razorpay payment link
    raw = rz.create_payment_link(
        name=data.name,
        email=data.email,
        amount=data.amount,
        description=data.description,
        min_partial_amount=data.min_partial_amount,
    )

    # Step 3: Update the sheet row with Razorpay details
    # The row we just appended is the last row
    all_payments = sheets.get_all_payments()
    row_index = len(all_payments) + 1  # +1 for header

    sheets.update_payment(
        row_index,
        PaymentUpdate(
            razorpay_link_id=raw["id"],
            razorpay_link_url=raw.get("short_url", ""),
        ),
    )

    # Step 4: Auto-send payment link email
    email_svc = _get_email()
    if email_svc:
        try:
            email_svc.send_payment_link_email(
                customer_name=data.name,
                customer_email=data.email,
                amount=data.amount,
                description=data.description,
                payment_url=raw.get("short_url", ""),
                due_date=data.due_date,
            )
        except Exception:
            logger.warning("Failed to send payment link email (non-blocking)")

    return _parse_link(raw)


@router.get("/payment-links/{link_id}", response_model=PaymentLinkResponse)
def get_payment_link(link_id: str):
    """Fetch current status of a payment link from Razorpay."""
    rz = _get_razorpay()
    try:
        raw = rz.fetch_payment_link(link_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _parse_link(raw)


@router.post("/payment-links/{link_id}/cancel", response_model=PaymentLinkResponse)
def cancel_payment_link(link_id: str):
    """Cancel an active payment link."""
    rz = _get_razorpay()
    try:
        raw = rz.cancel_payment_link(link_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _parse_link(raw)


# ------------------------------------------------------------------ #
#  Sync (polling approach for hackathon demo)
# ------------------------------------------------------------------ #


@router.post("/payment-links/{link_id}/sync", response_model=PaymentLinkSyncResponse)
def sync_payment_link(link_id: str):
    """
    Poll Razorpay for the latest payment link status and update Google Sheets.

    Use this instead of webhooks when you don't have a public URL.
    """
    rz = _get_razorpay()
    sheets = _get_sheets()

    try:
        raw = rz.fetch_payment_link(link_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    rz_status = raw.get("status", "unknown")
    rz_amount_paid = _paise_to_rupees(raw.get("amount_paid", 0))
    rz_amount = _paise_to_rupees(raw.get("amount", 0))

    # Map Razorpay status → our status
    status_map = {
        "created": "pending",
        "partially_paid": "partial",
        "paid": "paid",
        "cancelled": "failed",
        "expired": "failed",
    }
    our_status = status_map.get(rz_status, "pending")

    # Find and update the matching row in the Payments sheet
    from app.models.payment import PaymentUpdate

    sheet_updated = False
    all_payments = sheets.get_all_payments()
    for idx, p in enumerate(all_payments, start=2):  # row 2 onwards
        if p.razorpay_link_id == link_id:
            sheets.update_payment(
                idx,
                PaymentUpdate(status=our_status, amount_paid=rz_amount_paid),
            )
            sheet_updated = True
            logger.info("Synced payment link %s → %s", link_id, our_status)
            break

    return PaymentLinkSyncResponse(
        link_id=link_id,
        status=our_status,
        amount=rz_amount,
        amount_paid=rz_amount_paid,
        sheet_updated=sheet_updated,
    )


# ------------------------------------------------------------------ #
#  Webhook endpoint
# ------------------------------------------------------------------ #


@router.post("/webhooks", status_code=200)
async def razorpay_webhook(request: Request):
    """
    Receive Razorpay webhook events.

    Supported events:
      - payment_link.paid → full payment received
      - payment_link.partially_paid → partial payment received

    Configure in: Razorpay Dashboard → Webhooks
    URL: https://<your-domain>/razorpay/webhooks
    Events: payment_link.paid, payment_link.partially_paid
    """
    rz = _get_razorpay()
    sheets = _get_sheets()

    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not rz.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = json.loads(body)
    event = payload.get("event", "")

    if event in ("payment_link.paid", "payment_link.partially_paid"):
        payment_link = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
        link_id = payment_link.get("id", "")
        amount_paid = _paise_to_rupees(payment_link.get("amount_paid", 0))
        total_amount = _paise_to_rupees(payment_link.get("amount", 0))

        # Determine status
        is_fully_paid = amount_paid >= total_amount
        our_status = "paid" if is_fully_paid else "partial"

        # Update Google Sheet
        from app.models.payment import PaymentUpdate

        all_payments = sheets.get_all_payments()
        for idx, p in enumerate(all_payments, start=2):
            if p.razorpay_link_id == link_id:
                # Idempotency check: don't double-process if nothing changed
                if p.status == our_status and p.amount_paid == amount_paid:
                    logger.info("Webhook duplicate ignored: %s — %s", event, link_id)
                    break

                # Calculate how much was paid in *this* specific transaction
                # By taking the new total amount paid from Razorpay and subtracting our
                # locally stored total amount paid from before this webhook.
                current_amount = amount_paid - p.amount_paid 

                sheets.update_payment(
                    idx,
                    PaymentUpdate(status=our_status, amount_paid=amount_paid),
                )
                logger.info("Webhook processed: %s — %s → %s", event, link_id, our_status)

                email_svc = _get_email()
                if email_svc:
                    try:
                        if is_fully_paid:
                            # Send receipt to customer
                            email_svc.send_receipt_email(
                                customer_name=p.name,
                                customer_email=p.email,
                                amount_paid=current_amount,
                                description=p.description,
                            )
                            # Send owner summary
                            email_svc.send_owner_summary(
                                customer_name=p.name,
                                current_amount=current_amount,
                                total_amount_paid=amount_paid,
                                description=p.description,
                                status="paid",
                            )
                        else:
                            # Send partial payment notification
                            email_svc.send_partial_payment_email(
                                customer_name=p.name,
                                customer_email=p.email,
                                current_amount=current_amount,
                                total_amount_paid=amount_paid,
                                total_invoice_amount=p.amount,
                                description=p.description,
                                payment_url=p.razorpay_link_url or "",
                            )
                            # Send owner summary for partial
                            email_svc.send_owner_summary(
                                customer_name=p.name,
                                current_amount=current_amount,
                                total_amount_paid=amount_paid,
                                description=p.description,
                                status="partial",
                            )
                    except Exception:
                        logger.warning("Failed to send notification email (non-blocking)")

                break

    return {"status": "ok"}

