# Developer Onboarding Guide

Welcome to the FlowPay backend! This document explains how the pieces fit together.

## 1. What Is FlowPay?

FlowPay is an AI-native payment ops agent. Users type things like:
> "Collect ₹1,500 from Mohit for March subscription. Allow installments."

And the LangGraph agent handles the rest — CRM check, contact creation, payment link generation, email dispatch, and follow-up reminders.

## 2. Architecture Overview

The backend is built with **FastAPI** and deliberately uses **Google Sheets** as the database (CRM + Ledger) to fit the "small business" mental model. No PostgreSQL needed.

### Three External Services
1. **Google Sheets** (`app/services/sheets.py`): CRM for contacts and ledger for payments.
2. **Razorpay** (`app/services/razorpay.py`): Payment link generation and webhook processing.
3. **SMTP Email** (`app/services/email.py`): Branded HTML templates for all communication.

### AI Orchestration Layer
4. **LangGraph Agent** (`app/services/agent.py`): 10-tool StateGraph with Gemini 2.0 Flash, SQLite-backed memory, SSE streaming.

## 3. Data Flows

### A. Creating a Payment (via AI Agent)
1. User sends message to `POST /chat`
2. Agent calls `lookup_contact_tool` to check CRM
3. If contact is new → `update_contact_email_tool` adds them
4. If info is missing → Agent pauses and asks user
5. Once ready → `create_payment_link_tool` creates Razorpay link, saves to Sheets, sends email
6. Agent streams back confirmation with the payment URL

### B. Receiving a Payment (Webhook)
1. Razorpay hits `POST /razorpay/webhooks` with `payment_link.paid` or `payment_link.partially_paid`
2. Sheet row is updated with `amount_paid` and `status`
3. Customer receives receipt email; owner receives internal summary

### C. Reminders (Background)
1. APScheduler runs hourly
2. Scans for `pending` payments
3. Day 3 → Polite | Day 7 → Firm | Day 14 → Final notice
4. Updates `last_reminder_at` to prevent duplicates

## 4. Folder Structure

| Path | Purpose |
|---|---|
| `app/config.py` | Pydantic settings, auto-parses Google Sheet URLs |
| `app/main.py` | FastAPI app + service bootstrapping |
| `app/models/` | Pydantic schemas for all requests/responses |
| `app/routers/` | Thin REST endpoints calling services |
| `app/services/` | Core business logic + AI agent |
| `app/templates/` | HTML email templates |

## 5. Development Tips

1. **Auto-reload**: `uv run uvicorn app.main:app --reload`
2. **Lazy imports**: Services are initialized in `main.py` and imported lazily inside tools/routers to avoid circular imports.
3. **Error handling**: Catch exceptions in routers → raise `HTTPException`. Never let raw Python errors leak to the client.
4. **Best-effort emails**: Email failures are logged but don't crash the API.
5. **Google Sheets retries**: All gspread calls use `_with_retry` with exponential backoff.
6. **Rate limit resilience**: The AI agent has built-in retry (2s → 4s → 8s) for Gemini API 429 errors.
7. **Sheet URL UX**: Users can paste a full Google Sheets URL in `.env` — `config.py` auto-extracts the ID.

## 6. Testing

See **[`docs/CURL.md`](CURL.md)** for ready-to-run curl commands covering every endpoint and edge case.
