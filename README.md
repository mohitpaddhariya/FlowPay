# FlowPay — *"It's handled."*

**FlowPay** is an AI-native payments ops agent for small businesses in India.
Type what you need done in plain English — FlowPay handles the CRM lookups, Razorpay payment links, emails, reminders, and follow-ups end-to-end.

> **Example:** `"Collect ₹5,000 from Mohit for March subscription."`
>
> FlowPay looks up Mohit in your Google Sheet, creates a Razorpay link, emails it, tracks the payment, sends reminders, and notifies you when money arrives.

---

## ✨ Features

| Category | What it does |
|---|---|
| **Natural-language task intake** | Just describe what you want — the LLM figures out which tools to call |
| **Contact management** | Lookup, add, and update contacts in Google Sheets automatically |
| **Payment links** | Create Razorpay payment links with optional partial-payment support and due dates |
| **Automated emails** | Branded HTML emails for invoices, receipts, and reminders — all sent via SMTP |
| **Smart reminders** | Background scheduler sends Day 3 (polite) → Day 7 (firm) → Day 14 (final notice) reminders |
| **Webhook processing** | Real-time payment status updates from Razorpay, including partial-payment handling |
| **Owner summaries** | Internal email to the business owner when a payment is received |
| **Conversational memory** | Multi-turn chat with SQLite-backed checkpointing — the agent remembers context across messages |
| **Streaming UI** | Real-time Server-Sent Events stream tool calls and responses to the frontend |

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│         Next.js Frontend        │
│   (React 19 · Tailwind CSS 4)  │
│   Chat UI · Quick Tasks · SSE  │
└──────────────┬──────────────────┘
               │  POST /chat (SSE stream)
               ▼
┌─────────────────────────────────┐
│        FastAPI Backend          │
│          (Python 3.12)          │
│                                 │
│  ┌───────────────────────────┐  │
│  │   LangGraph Agent        │  │
│  │   (Gemini 2.5 Flash)     │  │
│  │                          │  │
│  │  10 tools:               │  │
│  │  · lookup_contact        │  │
│  │  · update_contact_email  │  │
│  │  · add_contact           │  │
│  │  · get_all_contacts      │  │
│  │  · create_payment_link   │  │
│  │  · get_all_payments      │  │
│  │  · find_payments_by_email│  │
│  │  · cancel_payment_link   │  │
│  │  · sync_payment_link     │  │
│  │  · send_reminder_email   │  │
│  └───────────────────────────┘  │
│                                 │
│  Services:                      │
│  · GoogleSheetsService (gspread)│
│  · RazorpayService (SDK)        │
│  · EmailService (SMTP + HTML)   │
│  · ReminderScheduler (APSched.) │
└──────────┬──────────┬───────────┘
           │          │
     ┌─────┘          └──────┐
     ▼                       ▼
┌──────────┐          ┌───────────┐
│  Google   │          │ Razorpay  │
│  Sheets   │          │  (Test)   │
│  (CRM)   │          │           │
└──────────┘          └───────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python ≥ 3.12** (managed via [uv](https://docs.astral.sh/uv/))
- **Node.js ≥ 18** + **pnpm**
- A Google Cloud **Service Account** with the Sheets API enabled
- A **Razorpay** account (test mode)
- A **Gmail** account with an App Password (or another SMTP provider)
- A **Gemini API key** from Google AI Studio

### 1. Clone & set up the backend

```bash
cd backend
cp .env.example .env
# Fill in your credentials in .env
```

Place your Google Service Account JSON file as `backend/credentials.json`, then share your target Google Sheet with the service account email (Editor access).

```bash
uv sync            # installs dependencies
uv run uvicorn app.main:app --reload --port 8000
```

### 2. Set up the frontend

```bash
cd frontend
pnpm install
```

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

```bash
pnpm run dev       # starts on http://localhost:3000
```

### 3. (Optional) Razorpay Webhooks

To receive real-time payment updates, expose the backend publicly (e.g. via ngrok) and configure the webhook URL in the Razorpay Dashboard:

```
URL:    https://<your-domain>/razorpay/webhooks
Events: payment_link.paid, payment_link.partially_paid
```

---

## 📁 Project Structure

```
FlowPay/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point & lifespan
│   │   ├── config.py            # Pydantic settings from .env
│   │   ├── models/              # Pydantic request/response models
│   │   ├── routers/             # API endpoints (chat, contacts, payments, razorpay, email)
│   │   ├── services/
│   │   │   ├── agent.py         # LangGraph agent, tools, and graph definition
│   │   │   ├── sheets.py        # Google Sheets CRUD
│   │   │   ├── razorpay.py      # Razorpay SDK wrapper
│   │   │   ├── email.py         # SMTP email with HTML templates
│   │   │   └── scheduler.py     # APScheduler payment reminder service
│   │   └── templates/           # HTML email templates (invoice, receipt, reminder)
│   ├── .env.example
│   └── pyproject.toml
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Main chat UI
│   │   ├── api.ts               # SSE streaming client
│   │   ├── globals.css          # Design system CSS variables
│   │   └── layout.tsx           # Root layout
│   └── package.json
├── README.md
└── PITCH.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4 |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **AI / Agent** | LangGraph, LangChain, Gemini 2.5 Flash |
| **Persistence** | Google Sheets (CRM), SQLite (agent memory) |
| **Payments** | Razorpay Payment Links API (test mode) |
| **Email** | SMTP (Gmail) with Jinja-style HTML templates |
| **Scheduling** | APScheduler (background reminder jobs) |

---

## 📝 License

Built for hackathon use. See [PITCH.md](PITCH.md) for the full pitch deck.