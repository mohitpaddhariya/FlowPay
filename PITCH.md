# FlowPay — *"It's handled."*

## One-Line Pitch

FlowPay is an AI payments-ops agent that turns a single English sentence into a complete payment collection workflow — CRM lookup, Razorpay link, branded email, automated reminders, and real-time status tracking.

---

## The Problem

Small businesses in India don't lose money because customers refuse to pay.
They lose time because **collecting payments is messy.**

A typical workflow today:

1. Search Google Sheets for the client
2. Copy their contact details
3. Create a Razorpay payment link
4. Send the link via email or WhatsApp
5. Track whether the payment arrives
6. Send reminder emails manually
7. Update the sheet when money lands

For something as small as **₹1,500**, founders spend **30 minutes chasing one payment.**

Payment collection becomes an operational burden.

---

## The Solution

What if collecting payments was **just one sentence?**

> *"Collect ₹5,000 from Mohit for March subscription."*

FlowPay turns that sentence into the **entire payment workflow** — automatically.

---

## What FlowPay Does

When the user gives an instruction, FlowPay:

1. **Understands the request** — Gemini 2.5 Flash parses intent, amount, name, and description
2. **Looks up the client** in Google Sheets via CRM tools
3. **Asks for missing details** if needed (e.g. email) and saves them back
4. **Creates a Razorpay payment link** (with optional partial-payment and due-date support)
5. **Emails the client** a branded HTML invoice with the payment link
6. **Tracks payment status** via Razorpay Webhooks in real time
7. **Sends smart reminders** — Day 3 polite → Day 7 firm → Day 14 final notice
8. **Handles partial payments** — detects them, updates the sheet, notifies the client of balance
9. **Sends the owner a summary** email when payment is received
10. **Remembers context** across messages — the conversational agent retains state per thread

The founder just **delegates the task** — FlowPay **executes the entire workflow.**

---

## Live Demo Flow

### Step 1 — User Instruction

User types in the chat UI:

> *"Collect ₹5,000 from Mohit for March subscription."*

The streaming interface shows tool calls in real time as the agent works.

### Step 2 — CRM Lookup

FlowPay checks Google Sheets for "Mohit."

If the email is missing, it asks:
> *"I found Mohit but their email is missing. Could you provide it?"*

Once provided, it saves the email to the CRM for future reference.

### Step 3 — Payment Link Created

FlowPay calls the Razorpay API and creates a payment link automatically.
The link, along with its ID and URL, is recorded in the Payments sheet.

### Step 4 — Email Sent

FlowPay sends the client a branded HTML email containing the payment link, amount, description, and due date.

### Step 5 — Payment Tracking

FlowPay monitors status via Razorpay Webhooks:

- **Full payment** → receipt emailed to client + owner summary
- **Partial payment** → balance notification emailed + sheet updated

If payment is pending, the **background scheduler** sends reminders:

| Day | Level | Tone |
|---|---|---|
| Day 3 | Level 1 | Polite nudge |
| Day 7 | Level 2 | Firm reminder |
| Day 14 | Level 3 | Final notice |

### Step 6 — Completed

Once paid:
- ✅ Google Sheet updated to **"paid"**
- ✅ Client receives a payment receipt
- ✅ Business owner receives a summary email

From **one instruction → money collected → records updated.**

---

## Why This Matters

Small businesses operate with fragmented tools:

- Google Sheets for tracking
- Razorpay for payment links
- Gmail for follow-ups
- WhatsApp for reminders

FlowPay **connects these tools** and orchestrates them into a **single automated workflow.**

Instead of dashboards and manual processes, businesses **just describe what they want done.**

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4 |
| **Backend** | Python 3.12, FastAPI, Uvicorn |
| **AI Agent** | LangGraph + LangChain + Gemini 2.5 Flash |
| **Agent Memory** | SQLite via LangGraph Checkpointing |
| **CRM** | Google Sheets (via Service Account + gspread) |
| **Payments** | Razorpay Payment Links API (test mode) |
| **Emails** | SMTP (Gmail) with branded HTML templates |
| **Reminders** | APScheduler (background hourly job) |
| **Streaming** | Server-Sent Events (SSE) for real-time UI |

### Agent Toolkit (10 tools)

The LangGraph agent has access to these tools and decides which to invoke:

| Tool | Purpose |
|---|---|
| `lookup_contact` | Search CRM by name |
| `update_contact_email` | Add or update a contact's email |
| `add_contact` | Insert a new contact |
| `get_all_contacts` | List all contacts |
| `create_payment_link` | Create Razorpay link + save to sheet + email invoice |
| `get_all_payments` | Retrieve all payment records |
| `find_payments_by_email` | Look up payments for a specific customer |
| `cancel_payment_link` | Cancel an active Razorpay link |
| `sync_payment_link` | Poll Razorpay for latest status and update sheet |
| `send_reminder_email` | Trigger a reminder email at a specified urgency level |

---

## Why It Fits This Hackathon

This hackathon asks for systems that **take action and complete real workflows.**

FlowPay is not a chatbot. It is an **agent that executes real work:**

```
instruction → tools → workflow → result
```

The output isn't text.
The output is **a payment successfully collected.**

---

## Vision

Today FlowPay handles payment collection.

In the future, it could become an **AI back-office for small businesses:**

- Overdue payment recovery
- Subscription billing automation
- Revenue analytics and cash-flow forecasting
- Automated bookkeeping and reconciliation
- WhatsApp payment follow-ups

FlowPay could eventually manage **the entire revenue operations layer** for small businesses.

---

## Closing Line

FlowPay turns payment collection into a single sentence.

Instead of chasing payments manually, you just say:

> *"Collect ₹5,000 from Mohit."*

And FlowPay replies:

**"It's handled."**