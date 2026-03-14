# FlowPay Backend

The backend for **FlowPay**, an AI-native payment operations agent for small businesses.

> Type: _"Collect ₹5,000 from Mohit for March subscription."_
> FlowPay handles the rest — CRM lookup, payment link, email, and reminders.

## Architecture

| Layer | Technology |
|---|---|
| **Framework** | FastAPI (Python 3.12) |
| **Database** | Google Sheets (CRM + Ledger via `gspread`) |
| **Payments** | Razorpay (Test Mode API + Webhooks) |
| **Email** | Python SMTP with custom HTML templates |
| **Background Jobs** | APScheduler (hourly payment reminders) |
| **AI Agent** | LangGraph + Google Gemini 2.0 Flash |
| **Persistence** | AsyncSqliteSaver (conversation memory) |

## Project Structure

```
backend/
├── app/
│   ├── config.py         # Environment config (auto-parses Sheet URLs)
│   ├── main.py           # FastAPI entry point & lifespan
│   ├── models/           # Pydantic schemas (contact, payment, chat, email)
│   ├── routers/          # REST endpoints (razorpay, contacts, email, chat)
│   ├── services/         # Business logic (sheets, razorpay, email, agent)
│   └── templates/        # HTML email templates
├── docs/
│   ├── AI_CONTEXT.md     # System context for LLM builders
│   ├── CURL.md           # Ready-to-run curl commands for every endpoint
│   └── DEVELOPER.md      # Onboarding guide & data flow
├── .env.example          # Template environment variables
└── pyproject.toml        # uv dependencies
```

## Features

### AI Agent (Phase 2 ✅)
- **10 LangGraph tools** covering all CRM, payment, and email operations
- **Conversational memory** via SQLite checkpointer (survives server restarts)
- **Streaming SSE** responses for real-time "agent is working" UX
- **Smart entity extraction**: relative dates, partial payments, contact disambiguation
- **CRM auto-sync**: every new contact is saved to Google Sheets automatically

### Core Services (Phase 1 ✅)
- **Google Sheets CRM** with exponential backoff on API errors
- **Razorpay payment links** (full + partial/installment support)
- **Auto-emailing**: payment link → receipt → partial balance → owner summary
- **Background reminders**: Day 3 (polite) → Day 7 (firm) → Day 14 (final)

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp .env.example .env
# Paste your Google Sheets URL, Razorpay keys, SMTP creds, and Gemini API key

# 3. Start the dev server
uv run uvicorn app.main:app --reload --port 8000

# 4. Expose for webhooks (separate terminal)
ngrok http 8000
# Update Razorpay Dashboard → Webhooks → your-ngrok-url/razorpay/webhooks
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | 🤖 AI Agent (SSE streaming) |
| `POST` | `/razorpay/payment-links` | Create payment link |
| `POST` | `/razorpay/payment-links/{id}/sync` | Poll Razorpay for status updates |
| `POST` | `/razorpay/payment-links/{id}/cancel` | Cancel a payment link |
| `POST` | `/razorpay/webhooks` | Receive Razorpay webhook events |
| `GET` | `/contacts/` | List all contacts |
| `POST` | `/contacts/` | Add a contact |
| `PUT` | `/contacts/by-name/{name}` | Update contact by name |
| `POST` | `/email/reminder` | Send manual reminder |
| `POST` | `/reminders/trigger` | Force background scheduler |
| `POST` | `/reset` | Clear all payments (demo) |

## Documentation

- **[`docs/CURL.md`](docs/CURL.md)** — Copy-paste curl commands for every endpoint
- **[`docs/DEVELOPER.md`](docs/DEVELOPER.md)** — Onboarding guide with data flow diagrams
- **[`docs/AI_CONTEXT.md`](docs/AI_CONTEXT.md)** — System context for AI/LLM integration
