# AI Context

*This document serves as the "System State" for LLM agents working on this repository.*

## 1. Project Goal
Build an AI agent (using LangGraph) that handles end-to-end payment operations (CRM lookup, Razorpay links, Emailing, and Reminders) using natural language instructions.

## 2. Current State
**Phase 1 (Tool Building) is COMPLETE.** All backend APIs required for the agent to function are built, tested, and wired together.

## 3. Available Tools for LangGraph
The following modules exist in `app/services/` and are exposed via `app/routers/`. The LangGraph agent should wrap these APIs/Services into `ToolNode` instances.

### A. Google Sheets (`app/services/sheets.py`)
Acts as the CRM and Invoice Ledger.
- `find_contact(name: str)`
- `find_contact_by_email(email: str)`
- `update_contact_by_name(name: str, data: ContactUpdate)`
- `add_payment(data: PaymentCreate)`

### B. Razorpay (`app/services/razorpay.py`)
Handles payment generation and webhook fulfillment.
- `POST /razorpay/payment-links` (Requires Name, Email, Amount, Description)
  - *Note: This endpoint automatically handles sheet insertion and sending the initial email.*
  - **NEW:** This endpoint accepts a `min_partial_amount` to allow customers to pay in installments. Usage of this should be exposed to the user as a capability.

### C. Email (`app/services/email.py`)
Handles manual interventions.
- `POST /email/reminder` (Requires customer_email, reminder_level: 1, 2, or 3)

### D. Automated Systems (Background)
The LangGraph agent **does not need to worry about these**. They happen automatically:
- **Receipts**: Sent automatically via Razorpay Webhook.
- **Owner Summaries**: Sent automatically via Razorpay Webhook.
- **Scheduled Reminders**: `APScheduler` runs hourly to send Day 3, 7, and 14 reminders for pending invoices.

## 4. Next Step: Phase 2 (Orchestration)
We need to introduce LangGraph.

**Proposed Agent State:**
```python
class AgentState(TypedDict):
    messages: list[BaseMessage]
    customer_name: str | None
    customer_email: str | None
    amount: float | None
    description: str | None
```

**Proposed Workflow:**
1. User provides prompt: "Collect 500 from Mohit for March ops."
2. **LLM Node** extracts intent and parameters.
3. If email is missing, **Tool Node** hits Google Sheets `find_contact` to get it.
4. If still missing, LLM pauses and asks user for email. Provide email via `update_contact_by_name`.
5. Once all parameters (name, email, amount, description) are met, **Tool Node** calls `POST /razorpay/payment-links`.
6. Agent replies: "Payment link created and emailed to Mohit."

## 5. Constraints
- **Frameworks**: `fastapi`, `langgraph`, `langchain-google-genai` (Gemini 1.5/2.0 Pro).
- Avoid creating new database systems; rely exclusively on the `GoogleSheetsService` for state tracking.

## 6. Testing & Documentation
All edge cases (partial payments, duplicate webhooks, Google API 500 errors) have been resolved. See `docs/CURL.md` for manual testing commands.
