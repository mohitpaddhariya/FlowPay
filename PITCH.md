# FlowPay — “It’s handled.”

## One-Line Pitch
FlowPay is an AI payments operations agent for small businesses.
Instead of creating payment links, sending reminders, and tracking invoices manually,
you simply tell FlowPay what you want done — and it handles the workflow end-to-end.

---

# The Problem

Small businesses in India don’t lose money because customers refuse to pay.

They lose time because **collecting payments is messy.**

A typical workflow today looks like this:

1. Search Google Sheets for the client
2. Copy their contact details
3. Create a Razorpay payment link
4. Send the link via email or WhatsApp
5. Track if the payment arrives
6. Send reminder emails
7. Update the sheet manually

For something as small as **₹1,500**, founders spend **30 minutes chasing the payment.**

Payment collection becomes an operational burden.

---

# The Idea

What if collecting payments was **just one sentence?**

Example instruction:

> Collect ₹1,500 from Mohit Paddhariya for March subscription.

FlowPay turns that sentence into the **entire payment workflow.**

---

# What FlowPay Does

When the user gives an instruction, FlowPay:

1. Understands the request using an LLM
2. Looks up the client in Google Sheets
3. Asks for missing details if needed
4. Creates a Razorpay payment link
5. Emails the client the payment link
6. Tracks payment status
7. Updates records when payment arrives
8. Sends the owner a summary

So instead of **doing the work manually**, the founder just **delegates it.**

FlowPay behaves like a **payments operations assistant.**

---

# Demo Flow

### Step 1 — User Instruction

User types:

Collect ₹1,500 from Mohit for March subscription.

FlowPay understands the intent.

---

### Step 2 — Data Lookup

FlowPay checks Google Sheets for Mohit.

If something is missing, it asks:

"Email for Mohit is missing. Please provide it."

Once provided, it saves the data back to the sheet.

---

### Step 3 — Payment Link

FlowPay creates a Razorpay payment link automatically.

---

### Step 4 — Email Sent

FlowPay sends the client an email with the payment link.

---

### Step 5 — Payment Tracking

FlowPay monitors payment status.

If payment is pending, it automatically sends reminders:

Day 3 — polite reminder  
Day 7 — firmer reminder  
Day 14 — final notice

---

### Step 6 — Payment Received

Once the payment arrives:

• Google Sheet is updated  
• Client receives a receipt  
• Founder gets a payment summary  

From **one instruction to money collected.**

---

# Why This Matters

Small businesses operate with messy tools:

• Google Sheets  
• WhatsApp  
• Razorpay  
• Email  

FlowPay connects these tools and turns them into an **automated workflow system.**

Instead of dashboards and forms, businesses **just describe what they want done.**

---

# Tech Stack

Frontend
Next.js interface where users type instructions and view task status.

Backend
Python + FastAPI + LangGraph

LLM
Gemini — used to interpret tasks and decide which tools to call.

Integrations

• Google Sheets — contacts and payment records  
• Razorpay — payment links and status  
• Email provider — payment links, reminders, receipts  

FlowPay orchestrates these tools into a **single automated workflow.**

---

# Why It Fits This Hackathon

This hackathon asks for systems that **take action and complete workflows.**

FlowPay is not a chatbot.

It is an **agent that executes real work**:

instruction → tools → workflow → result.

The output isn't text.

The output is **a payment successfully collected.**

---

# Vision

Today FlowPay handles payment collection.

In the future it could become an **AI back-office for small businesses**:

• overdue payment recovery  
• subscription billing automation  
• revenue analytics  
• automated bookkeeping  
• WhatsApp payment follow-ups  

FlowPay could eventually manage **the entire revenue operations layer** for small businesses.

---

# Closing Line

FlowPay turns payment collection into a single sentence.

Instead of chasing payments manually,

you just say:

> “Collect ₹1,500 from Mohit.”

And FlowPay replies:

**“It’s handled.”**