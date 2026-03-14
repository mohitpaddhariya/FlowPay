"""Payments API router."""

from fastapi import APIRouter, HTTPException, Query

from app.models.payment import Payment, PaymentCreate, PaymentUpdate
from app.services.sheets import GoogleSheetsService

router = APIRouter(prefix="/payments", tags=["Payments"])


def _get_service() -> GoogleSheetsService:
    """Lazy import to avoid circular init issues."""
    from app.main import sheets_service  # noqa: WPS433

    if sheets_service is None:
        raise HTTPException(status_code=503, detail="Sheets service not ready")
    return sheets_service


@router.get("", response_model=list[Payment])
def list_payments():
    """Return all payment records from the Payments sheet."""
    return _get_service().get_all_payments()


@router.get("/search", response_model=list[Payment])
def search_payments(
    email: str = Query(..., description="Client email to search payments for"),
):
    """Search payment records by client email."""
    return _get_service().find_payments_by_email(email)


@router.post("", response_model=Payment, status_code=201)
def create_payment(data: PaymentCreate):
    """Create a new payment record in the Payments sheet."""
    return _get_service().add_payment(data)


@router.put("/{row_index}", response_model=Payment)
def update_payment(row_index: int, data: PaymentUpdate):
    """
    Update a payment record by its row index (1-based, header is row 1).
    Only provided fields are overwritten.
    """
    updated = _get_service().update_payment(row_index, data)
    if updated is None:
        raise HTTPException(
            status_code=404,
            detail=f"Payment row {row_index} not found",
        )
    return updated
