# FlowPay Backend

The backend for FlowPay, an AI-native payment operations agent for small businesses.

This backend serves as the tool execution layer for the LangGraph agent, orchestrating Google Sheets, Razorpay, and Email (SMTP) to complete end-to-end payment collection workflows from plain English instructions.

## Architecture

- **Framework**: FastAPI
- **Database**: Google Sheets (used as CRM and Ledger via `gspread`)
- **Payments**: Razorpay (Test mode API + Webhooks)
- **Email**: Built-in Python SMTP with custom HTML templates
- **Background Jobs**: APScheduler (for payment reminders)
- **Agent Orchestration**: LangGraph + Google Gemini (WIP)

## Structure & Documentation

```
backend/
├── app/                  # Main FastAPI Application
│   ├── config.py         # Environment variables & constants
│   ├── main.py           # FastAPI entry point & lifespan
│   ├── models/           # Pydantic schema definitions
│   ├── routers/          # FastAPI routes
│   ├── services/         # Core business logic (Sheets, Razorpay, Email)
│   └── templates/        # HTML email templates
├── docs/                 # 📚 Extensive Documentation
│   ├── AI_CONTEXT.md     # Context and capabilities for future LLM Builders
│   ├── CURL.md           # Copy-paste curl commands to test every single API route
│   └── DEVELOPER.md      # Onboarding guide mapping out the data flow
└── pyproject.toml        # uv dependencies
```

## Features

- **Google Sheets CRM**: Read/write contacts (name, email) and payment records. Built with automatic exponential backoff to handle Google API 500 errors gracefully.
- **Razorpay Integration**: Creates payment links dynamically (supporting full payments or installments via `min_partial_amount`). Webhooks handle idempotency automatically to prevent double-logging.
- **Smart Emailing**:
  - Auto-sends payment link immediately on creation.
  - Auto-sends receipt (or partial payment balance) on webhook hit.
  - Sends the business owner an internal summary when money arrives.
- **Background Reminders**: Scheduled job (hourly) that checks sheet for pending payments:
  - Day 3: Polite friendly reminder
  - Day 7: Firm overdue notice
  - Day 14: Final notice

## Running Locally

1. Install dependencies using `uv`:
   ```bash
   uv sync
   ```
2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Fill out Google Sheets JSON, Razorpay Keys, and SMTP details
   ```
3. Start the dev server:
   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```
4. Expose for webhooks (in a separate terminal):
   ```bash
   ngrok http 8000
   ```
   *Update Razorpay Dashboard to point to `your-ngrok-url.app/razorpay/webhooks`*

## API Endpoints

The core tools that the LangGraph Agent uses:
- `GET /contacts/search?name={name}` – Look up customer
- `PUT /contacts/by-name/{name}` – Update missing info (e.g. email)
- `POST /razorpay/payment-links` – Generates link, saves to sheets, sends initial email
- `POST /email/reminder` – Send one-off manual reminder
- `POST /reminders/trigger` – Force the background scheduler to run (demo purposes)
- `POST /reset` – Clear all payment records from Google Sheets (demo purposes)
