# Developer Onboarding Guide

Welcome to the FlowPay backend! This document explains how the pieces fit together so you can start contributing immediately.

## 1. What Are We Building?

FlowPay an AI-native payment ops agent. The goal is to let users type things like:
> "Collect ₹1,500 from Mohit for March subscription."

And the agent handles the rest. This repo contains the **Core Services Layer** (the tools the agent uses) and the upcoming **Agent Orchestration Layer** (LangGraph).

## 2. Core Architecture

The backend is built with **FastAPI** (`app/main.py`), but it deliberately avoids traditional databases (PostgreSQL/MySQL) to fit the "small business tech stack" mental model.

Instead, the architecture relies on three primary external services:
1. **Google Sheets** (`app/services/sheets.py`): Acts as both our CRM and Ledger.
2. **Razorpay** (`app/services/razorpay.py`): Handles payment link generation and webhooks.
3. **SMTP Email** (`app/services/email.py`): Sends custom HTML templates.

## 3. How the Data Flows

### A. The "Happy Path" (Creating a Payment)
1. **Action:** A request hits `POST /razorpay/payment-links` with customer details (can include `min_partial_amount` to allow installments).
2. **CRM:** We insert a pending payment into the `Payments` Google Sheet.
3. **Gateway:** We call Razorpay to generate a short URL for the payment.
4. **Update:** We save the Razorpay ID and URL back to the Google Sheet.
5. **Notification:** We immediately send the customer an HTML "Payment Link" email.

### B. The Webhook Path (Receiving a Payment)
1. **Action:** Razorpay hits `POST /razorpay/webhooks` with `payment_link.paid` or `payment_link.partially_paid`.
2. **CRM:** We find the row in Google Sheets by `link_id`. We calculate the `current_amount` and update the total `amount_paid`, marking status as `paid` or `partially_paid`.
3. **Notification (Internal):** We send the business owner a "Payment summary" email containing both the current and total values.
4. **Notification (External):** We send the customer a "Receipt" or "Partial Receipt" email depending on the status.

### C. The Reminder Path (Background Jobs)
1. **Action:** Every hour, `APScheduler` triggers `services/scheduler.py`.
2. **CRM:** It reads all rows from the `Payments` sheet.
3. **Check:** Filters for `status == pending`.
4. **Evaluation:** If `days_since_creation == 3`, sends Polite Reminder. If `== 7`, sends Firm Reminder. If `== 14`, sends Final Notice.
5. **Update:** Writes back to `last_reminder_at` in the sheet to avoid duplicate sends.

## 4. Folder Structure Explained

- `app/config.py`: The single source of truth for environment variables (powered by `pydantic-settings`).
- `app/main.py`: Where FastAPI is instantiated and services are bootrapped on `lifespan`.
- `app/models/`: Pydantic schemas validating all incoming requests and outgoing responses.
- `app/routers/`: The REST endpoints. Keep these thin! They should just call `services/`.
- `app/services/`: The "meat" of the app. Where business logic lives.
- `app/templates/`: The HTML for the emails.

## 5. Development Tips

1. **Auto-reload is your friend:** We use `uv run uvicorn app.main:app --reload`.
2. **Lazy Initialization:** Notice how `services` are initialized in `main.py` and then lazily imported inside routers (e.g., `from app.main import sheets_service`). This avoids circular import loops while ensuring singleton instances.
3. **Error Handling:** Don't let standard Python exceptions bubble up to the client. Catch them in the router and raise `fastapi.HTTPException`.
4. **The "Best Effort" Rule (Emails):** If an email fails to send, the webhook or API shouldn't crash. E-mails are wrapped in `try/except` and log a warning if they fail. Do not block core operations on email delivery.
5. **The Retries Rule (Google Sheets):** The Google APIs occasionally return 500 Internal Errors randomly. All gspread read/write calls in `sheets.py` are wrapped in an `_with_retry` exponential backoff loop to automatically recover.

## 6. Testing

Refer to **`docs/CURL.md`** for a full suite of ready-to-run curl commands that cover every endpoint (including normal payments, partial payments, contacts, and resets).
