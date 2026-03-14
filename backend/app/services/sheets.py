"""
Google Sheets service — handles all reads and writes to the
Contacts and Payments worksheets via gspread + Service Account auth.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials

from app.config import get_settings
from app.models.contact import Contact, ContactCreate, ContactUpdate
from app.models.payment import Payment, PaymentCreate, PaymentUpdate

logger = logging.getLogger(__name__)

# Scopes needed for read/write access to Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

CONTACTS_HEADERS = ["Name", "Email"]
PAYMENTS_HEADERS = [
    "Name",
    "Email",
    "Amount",
    "Description",
    "Razorpay Link ID",
    "Razorpay Link URL",
    "Status",
    "Amount Paid",
    "Due Date",
    "Created At",
    "Last Reminder At",
    "Notes",
]


class GoogleSheetsService:
    """Thin wrapper around gspread for FlowPay's two worksheets."""

    def __init__(self) -> None:
        settings = get_settings()
        creds = Credentials.from_service_account_file(
            settings.google_sheets_credentials_file,
            scopes=SCOPES,
        )
        self._client = gspread.authorize(creds)
        self._spreadsheet = self._client.open_by_key(settings.google_sheet_id)

        # Ensure worksheets exist with correct headers
        self._contacts_ws = self._ensure_worksheet("Contacts", CONTACTS_HEADERS)
        self._payments_ws = self._ensure_worksheet("Payments", PAYMENTS_HEADERS)
        logger.info("Google Sheets service initialised ✓")

    # ------------------------------------------------------------------ #
    #  Helpers
    # ------------------------------------------------------------------ #

    def _with_retry(self, func, *args, **kwargs):
        """Execute a gspread call with exponential backoff on 500 errors."""
        import time
        from gspread.exceptions import APIError

        retries = 3
        for i in range(retries):
            try:
                return func(*args, **kwargs)
            except APIError as e:
                if i == retries - 1:
                    raise
                logger.warning("Google Sheets API error: %s. Retrying in %ss...", e, 2**i)
                time.sleep(2 ** i)

    def _ensure_worksheet(
        self, title: str, headers: list[str]
    ) -> gspread.Worksheet:
        """Get or create a worksheet and make sure the header row is correct."""
        try:
            ws = self._with_retry(self._spreadsheet.worksheet, title)
        except gspread.exceptions.WorksheetNotFound:
            ws = self._spreadsheet.add_worksheet(
                title=title, rows=1000, cols=len(headers)
            )
            logger.info("Created worksheet '%s'", title)

        # Set headers if the first row is empty
        existing_headers = ws.row_values(1)
        if not existing_headers:
            ws.update([headers], "A1")
            logger.info("Set headers for worksheet '%s'", title)
            
        # Always format the header row: Bold, Dark Gray bg, White text, Frozen top row
        try:
            header_range = f"A1:{chr(ord('A') + len(headers) - 1)}1"
            ws.format(
                header_range,
                {
                    "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                    "textFormat": {
                        "bold": True,
                        "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                    },
                },
            )
            # Freeze the first row
            ws.freeze(rows=1)
        except Exception as e:
            logger.warning("Could not format headers for '%s': %s", title, e)

        return ws

    @staticmethod
    def _row_to_contact(row: list[str]) -> Contact:
        """Convert a raw sheet row to a Contact model."""
        return Contact(
            name=row[0] if len(row) > 0 else "",
            email=row[1] if len(row) > 1 else "",
        )

    @staticmethod
    def _row_to_payment(row: list[str]) -> Payment:
        """Convert a raw sheet row to a Payment model."""

        def val(idx: int) -> str:
            return row[idx] if len(row) > idx else ""

        return Payment(
            name=val(0),
            email=val(1),
            amount=float(val(2) or 0),
            description=val(3),
            razorpay_link_id=val(4) or None,
            razorpay_link_url=val(5) or None,
            status=val(6) or "pending",
            amount_paid=float(val(7) or 0),
            due_date=val(8) or None,
            created_at=val(9),
            last_reminder_at=val(10) or None,
            notes=val(11) or None,
        )

    # ------------------------------------------------------------------ #
    #  Contacts CRUD
    # ------------------------------------------------------------------ #

    def get_all_contacts(self) -> list[Contact]:
        """Return every contact in the Contacts sheet."""
        rows = self._with_retry(self._contacts_ws.get_all_values)
        # Skip header row
        return [self._row_to_contact(r) for r in rows[1:] if any(r)]

    def find_contact(self, name: str) -> Contact | None:
        """Case-insensitive search by name. Returns first match or None."""
        for contact in self.get_all_contacts():
            if contact.name.lower() == name.lower():
                return contact
        return None

    def find_contact_by_email(self, email: str) -> Contact | None:
        """Search by email. Returns first match or None."""
        for contact in self.get_all_contacts():
            if contact.email.lower() == email.lower():
                return contact
        return None

    def add_contact(self, data: ContactCreate) -> Contact:
        """Append a new contact row."""
        row = [data.name, data.email]
        self._with_retry(self._contacts_ws.append_row, row, value_input_option="USER_ENTERED")
        logger.info("Added contact: %s", data.name)
        return Contact(name=data.name, email=data.email)

    def update_contact(self, email: str, data: ContactUpdate) -> Contact | None:
        """Update a contact found by email. Returns updated contact or None."""
        rows = self._with_retry(self._contacts_ws.get_all_values)
        for idx, row in enumerate(rows[1:], start=2):  # 1-indexed, skip header
            if len(row) > 1 and row[1].lower() == email.lower():
                new_name = data.name if data.name is not None else row[0]
                new_email = data.email if data.email is not None else row[1]
                self._with_retry(
                    self._contacts_ws.update,
                    f"A{idx}:B{idx}",
                    [[new_name, new_email]],
                    value_input_option="USER_ENTERED",
                )
                logger.info("Updated contact: %s", email)
                return Contact(name=new_name, email=new_email)
        return None

    def update_contact_by_name(self, name: str, data: ContactUpdate) -> Contact | None:
        """Update a contact found by name (case-insensitive).

        Useful when the agent knows the name but not the email
        (e.g. user says "Mohit's email is xyz@gmail.com").
        """
        rows = self._with_retry(self._contacts_ws.get_all_values)
        for idx, row in enumerate(rows[1:], start=2):
            if len(row) > 0 and row[0].lower() == name.lower():
                new_name = data.name if data.name is not None else row[0]
                new_email = data.email if data.email is not None else (row[1] if len(row) > 1 else "")
                self._with_retry(
                    self._contacts_ws.update,
                    f"A{idx}:B{idx}",
                    [[new_name, new_email]],
                    value_input_option="USER_ENTERED",
                )
                logger.info("Updated contact by name: %s", name)
                return Contact(name=new_name, email=new_email)
        return None

    # ------------------------------------------------------------------ #
    #  Payments CRUD
    # ------------------------------------------------------------------ #

    def get_all_payments(self) -> list[Payment]:
        """Return every record in the Payments sheet."""
        rows = self._with_retry(self._payments_ws.get_all_values)
        return [self._row_to_payment(r) for r in rows[1:] if any(r)]

    def find_payments_by_email(self, email: str) -> list[Payment]:
        """Return all payment records for a given email."""
        return [
            p
            for p in self.get_all_payments()
            if p.email.lower() == email.lower()
        ]

    def add_payment(self, data: PaymentCreate) -> Payment:
        """Create a new payment record with sensible defaults."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        row = [
            data.name,
            data.email,
            str(data.amount),
            data.description,
            "",  # razorpay_link_id — filled later
            "",  # razorpay_link_url — filled later
            "pending",
            "0",  # amount_paid
            data.due_date or "",
            now,
            "",  # last_reminder_at
            data.notes or "",
        ]
        self._with_retry(self._payments_ws.append_row, row, value_input_option="USER_ENTERED")
        logger.info("Added payment for %s — ₹%s", data.name, data.amount)
        return self._row_to_payment(row)

    def update_payment(self, row_index: int, data: PaymentUpdate) -> Payment | None:
        """
        Update a payment record by its 1-based row index (header = row 1).
        Only non-None fields in *data* are overwritten.
        """
        rows = self._with_retry(self._payments_ws.get_all_values)
        if row_index < 2 or row_index > len(rows):
            return None

        current = rows[row_index - 1]  # 0-indexed list

        # Pad current row to full width
        while len(current) < len(PAYMENTS_HEADERS):
            current.append("")

        if data.razorpay_link_id is not None:
            current[4] = data.razorpay_link_id
        if data.razorpay_link_url is not None:
            current[5] = data.razorpay_link_url
        if data.status is not None:
            current[6] = data.status
        if data.amount_paid is not None:
            current[7] = str(data.amount_paid)
        if data.due_date is not None:
            current[8] = data.due_date
        if data.last_reminder_at is not None:
            current[10] = data.last_reminder_at
        if data.notes is not None:
            current[11] = data.notes

        end_col = chr(ord("A") + len(PAYMENTS_HEADERS) - 1)  # 'L'
        self._with_retry(
            self._payments_ws.update,
            f"A{row_index}:{end_col}{row_index}",
            [current],
            value_input_option="USER_ENTERED",
        )
        logger.info("Updated payment row %d", row_index)
        return self._row_to_payment(current)

    def reset_payments(self) -> None:
        """Clear all rows from the Payments sheet except the header."""
        # Get total number of rows currently populated
        rows = self._with_retry(self._payments_ws.get_all_values)
        if len(rows) > 1:
            end_col = chr(ord("A") + len(PAYMENTS_HEADERS) - 1)
            # Clear from row 2 downwards
            self._payments_ws.batch_clear([f"A2:{end_col}{len(rows)}"])
            logger.info("Payments sheet reset (cleared %d rows)", len(rows) - 1)

