# AI Context

*System context for LLM agents and developers working on this repository.*

## 1. Project Goal
FlowPay is an AI agent (LangGraph + Gemini 2.0 Flash) that handles end-to-end payment operations via natural language. It manages CRM contacts, Razorpay payment links, email dispatch, and reminders — all from a single conversational interface.

## 2. Current State
**Phase 1 (Tool Building) ✅ and Phase 2 (AI Orchestration) ✅ are COMPLETE.**

The LangGraph agent is fully operational with 10 tools, SSE streaming, SQLite-backed conversation memory, and CRM-first verification logic.

## 3. Agent Tools (10 Total)

### CRM Tools (Google Sheets)
| Tool | Purpose |
|---|---|
| `lookup_contact_tool` | Search CRM by name; returns all matches for disambiguation |
| `update_contact_email_tool` | Upsert: updates existing contact or inserts new one |
| `add_contact_tool` | Directly add a new contact |
| `get_all_contacts_tool` | List all contacts |
| `get_all_payments_tool` | List all payment records |
| `find_payments_by_email_tool` | Find payments for a specific email |

### Payment Tools (Razorpay)
| Tool | Purpose |
|---|---|
| `create_payment_link_tool` | Creates link, saves to Sheets, sends email (full business logic) |
| `cancel_payment_link_tool` | Cancel an active payment link |
| `sync_payment_link_tool` | Poll Razorpay for latest status and update CRM |

### Communication Tools (Email)
| Tool | Purpose |
|---|---|
| `send_reminder_email_tool` | Send manual reminder (levels 1–3) for pending payments |

## 4. Agent Behavior Rules
1. **CRM-first verification**: Agent ALWAYS calls `lookup_contact_tool` before creating any payment link, even when the user provides both name and email.
2. **Auto-upsert**: If a contact doesn't exist, it's added automatically via `update_contact_email_tool`.
3. **Missing info pause**: Agent pauses and asks the user when email, description, or `min_partial_amount` is missing.
4. **Date resolution**: Relative dates ("tomorrow", "in 3 days") are calculated from the system clock.
5. **Disambiguation**: Multiple CRM matches trigger a clarification prompt.
6. **Rate limit resilience**: Exponential backoff (2s → 4s → 8s) on 429 errors.

## 5. Configuration UX
- `GOOGLE_SHEET_ID` accepts either a full Google Sheets URL or a raw sheet ID (auto-parsed via Pydantic validator).
- `GEMINI_API_KEY` is loaded from `.env` via `python-dotenv`.

## 6. Automated Systems (No Agent Involvement)
- **Receipts & Partial Payment Emails**: Triggered automatically by Razorpay webhooks.
- **Owner Summaries**: Sent automatically when payments arrive.
- **Scheduled Reminders**: APScheduler runs hourly (Day 3/7/14 escalation).

## 7. Tech Stack
`fastapi`, `langgraph`, `langchain-google-genai`, `langchain-core`, `langgraph-checkpoint-sqlite`, `aiosqlite`, `gspread`, `razorpay`, `pydantic-settings`, `apscheduler`
