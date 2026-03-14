from pydantic import BaseModel, EmailStr


class Contact(BaseModel):
    """A contact in the Contacts sheet."""

    name: str
    email: EmailStr


class ContactCreate(BaseModel):
    """Request body for creating a new contact."""

    name: str
    email: EmailStr


class ContactUpdate(BaseModel):
    """Request body for updating a contact. All fields optional."""

    name: str | None = None
    email: EmailStr | None = None
