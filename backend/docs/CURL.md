# FlowPay API — cURL Commands

Here are ready-to-use `curl` commands to test every endpoint in the FlowPay backend locally.

**Base URL**: `http://localhost:8000`

---

## 1. Razorpay Payment Links

### 1a. Create a Normal Payment Link (Full Amount Only)
Link where the customer *must* pay the exact amount.

```bash
curl -X 'POST' \
  'http://localhost:8000/razorpay/payment-links' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Mohit Paddhariya",
  "email": "mohit.paddhariya@gmail.com",
  "amount": 5000,
  "description": "Standard Consultation",
  "due_date": "2026-03-30",
  "notes": "Please pay in full."
}'
```

### 1b. Create a Partial Payment Link
Link where the customer can pay in installments (down to a minimum amount).

```bash
curl -X 'POST' \
  'http://localhost:8000/razorpay/payment-links' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Mohit Paddhariya",
  "email": "mohit.paddhariya@gmail.com",
  "amount": 10000,
  "min_partial_amount": 2500,
  "description": "Custom Website Development (Milestone 1)",
  "due_date": "2026-04-15",
  "notes": "Testing partial payments! Minimum ₹2,500."
}'
```

---

## 2. Testing Webhooks (Local Simulation)

You can simulate what Razorpay sends when a payment is made by hitting the webhook endpoint. 
*(Note: since we have HMAC signature verification, manual webhook simulations via curl will fail with a 400 Invalid Signature unless you bypass the `verify_webhook_signature` check in local testing, or use actual Razorpay Test Mode).*

To test end-to-end, it is recommended to click the generated link from step 1, select "Netbanking" -> "Success" in Razorpay Test Mode.

---

## 3. Contact Management

### 3a. Add a Contact
If you want to just add a contact to the sheet without generating a payment link yet.

```bash
curl -X 'POST' \
  'http://localhost:8000/contacts/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "John Doe",
  "email": "john.doe@example.com"
}'
```

### 3b. Update Contact (By Email)
```bash
curl -X 'PUT' \
  'http://localhost:8000/contacts/john.doe@example.com' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Johnathan Doe"
}'
```

### 3c. Update Contact (By Name)
Useful as a tool for the LangGraph agent when it only knows the name.
```bash
curl -X 'PUT' \
  'http://localhost:8000/contacts/by-name/Johnathan%20Doe' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "email": "john.newemail@example.com"
}'
```

---

## 4. Email Reminders

### 4a. Manually Trigger the Reminder Job
The scheduler normally runs every hour, but you can force it to check the sheet and send emails *right now*.

```bash
curl -X 'POST' \
  'http://localhost:8000/trigger-reminders' \
  -H 'accept: application/json' \
  -d ''
```

---

## 5. Master Commands (Demo utilities)

### 5a. Reset/Clear Payments Database
Wipes all records from the Google Sheet (except the headers) so you can start a fresh demo.

```bash
curl -X 'POST' \
  'http://localhost:8000/reset' \
  -H 'accept: application/json' \
  -d ''
```

---

## 6. AI Agent Chat (Post-Phase 2)

### 6a. Direct Payment Link Request (Streaming)
This hits the LangGraph `StateGraph`, sending back live Server-Sent Events (SSE) as the LLM calls the tools and formulates a response.

```bash
curl -X 'POST' \
  'http://localhost:8000/chat' \
  -H 'accept: text/event-stream' \
  -H 'Content-Type: application/json' \
  -d '{
  "message": "Hey FlowPay! Collect ₹500 from Mohit Paddhariya (mohit.paddhariya@gmail.com) for Web Design. Due tomorrow.",
  "thread_id": "test-session-1"
}'
```

### 6b. Missing Information Request (Memory Check)
If you ask for a payment without an email, it will ask for one. When you reply in the same thread, it remembers who you are talking about.

**Step 1: Ask for payment (Agent will pause and ask for Email)**
```bash
curl -X 'POST' \
  'http://localhost:8000/chat' \
  -H 'accept: text/event-stream' \
  -H 'Content-Type: application/json' \
  -d '{
  "message": "Hey FlowPay! Collect ₹500 from Pooja for Web Design. Due tomorrow.",
  "thread_id": "test-session-2"
}'
```

**Step 2: Reply to the Agent (Keep the exact same `thread_id`!)**
```bash
curl -X 'POST' \
  'http://localhost:8000/chat' \
  -H 'accept: text/event-stream' \
  -H 'Content-Type: application/json' \
  -d '{
  "message": "Her email is pooja@example.com",
  "thread_id": "test-session-2"
}'
```
