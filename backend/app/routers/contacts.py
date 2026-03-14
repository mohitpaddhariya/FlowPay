"""Contacts API router."""

from fastapi import APIRouter, HTTPException, Query

from app.models.contact import Contact, ContactCreate, ContactUpdate
from app.services.sheets import GoogleSheetsService

router = APIRouter(prefix="/contacts", tags=["Contacts"])


def _get_service() -> GoogleSheetsService:
    """Lazy import to avoid circular init issues."""
    from app.main import sheets_service  # noqa: WPS433

    if sheets_service is None:
        raise HTTPException(status_code=503, detail="Sheets service not ready")
    return sheets_service


@router.get("", response_model=list[Contact])
def list_contacts():
    """Return all contacts from the Contacts sheet."""
    return _get_service().get_all_contacts()


@router.get("/search", response_model=Contact | None)
def search_contact(name: str = Query(..., description="Contact name to search")):
    """Search for a contact by name (case-insensitive)."""
    contact = _get_service().find_contact(name)
    if contact is None:
        raise HTTPException(status_code=404, detail=f"Contact '{name}' not found")
    return contact


@router.post("", response_model=Contact, status_code=201)
def create_contact(data: ContactCreate):
    """Add a new contact to the Contacts sheet."""
    existing = _get_service().find_contact_by_email(data.email)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Contact with email '{data.email}' already exists",
        )
    return _get_service().add_contact(data)


@router.put("/{email}", response_model=Contact)
def update_contact(email: str, data: ContactUpdate):
    """Update an existing contact (looked up by email)."""
    updated = _get_service().update_contact(email, data)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Contact '{email}' not found")
    return updated


@router.put("/by-name/{name}", response_model=Contact)
def update_contact_by_name(name: str, data: ContactUpdate):
    """
    Update a contact looked up by name (case-insensitive).
    Useful when the agent only knows the name (e.g. to add a missing email).
    """
    updated = _get_service().update_contact_by_name(name, data)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Contact '{name}' not found")
    return updated
