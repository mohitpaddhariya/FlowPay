# FlowPay – “It’s handled.”

FlowPay is an **AI‑native payments ops agent** for small businesses in India.  
You type what you want done in plain English, FlowPay handles the Razorpay links, Google Sheet updates, emails, and follow‑ups.

---

## What FlowPay Does

Given an instruction like:

> “Collect ₹1,500 from Mohit Paddhariya for March subscription.”

FlowPay will:

1. **Understand your request** using an LLM (Gemini).
2. **Look up the client** in your connected Google Sheet.
3. **Ask for missing info** (like email or due date) and write it back to the Sheet.
4. **Create a Razorpay payment link** (test mode for hackathon).
5. **Email the client** the payment link.
6. **Track payment status** (pending / paid / failed).
7. **Update records** and send you a short summary when money arrives.

The demo shows a full, end‑to‑end flow: from a single sentence to money collected and records updated.

---

## Follow‑Ups & Notifications

FlowPay isn’t just “create link and forget.” It also handles realistic follow‑ups:

- **Payment reminders:** after a set duration, if payment hasn’t arrived, FlowPay sends:
  - Day 3 – a polite reminder,
  - Day 7 – a firmer nudge,
  - Day 14 – a final notice.  
  Each email references the actual invoice and amount.

- **Partial payment handling:** if the client pays only part of the amount, FlowPay detects it and sends:  
  “Received ₹X, balance ₹Y still pending.”  
  It updates the Sheet and keeps the remaining amount tracked.

- **Payment receipts:** as soon as payment is completed, FlowPay:
  - emails the client a receipt, and
  - sends you a brief internal summary (who paid, how much, for what).

These three flows are designed to feel real and impressive in a short hackathon demo.

---

## Why This Matters

Today, founders waste time:

- hunting rows in Google Sheets,
- creating Razorpay links by hand,
- sending one‑off emails,
- manually marking who has paid.

FlowPay turns all of that into **one instruction**.  
It behaves like a small **payments ops agency in a box**: tool‑driven, workflow‑first, and built on top of Razorpay + Google Sheets.

---

## Tech (High‑Level)

- **Frontend:** Next.js web UI to:
  - type tasks in natural language,
  - see tasks and their status,
  - answer quick follow‑up questions (e.g. missing email).

- **Backend:** Python (FastAPI + LangGraph)
  - parses tasks with Gemini,
  - calls tools for Google Sheets, Razorpay, and email,
  - tracks task status and follow‑ups.

- **Integrations:**
  - Google Sheets – source of truth for contacts and payment records.
  - Razorpay (test mode) – payment links and status.
  - Email provider – client emails, reminders, receipts, and owner summaries.