"""
FlowPay Backend — FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import contacts, payments, razorpay as razorpay_router, email as email_router, chat as chat_router
from app.services.sheets import GoogleSheetsService
from app.services.razorpay import RazorpayService
from app.services.email import EmailService
from app.services.scheduler import ReminderScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# Module-level references so routers can access services
sheets_service: GoogleSheetsService | None = None
razorpay_service: RazorpayService | None = None
email_service: EmailService | None = None
reminder_scheduler: ReminderScheduler | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise shared resources on startup, tear down on shutdown."""
    global sheets_service, razorpay_service, email_service, reminder_scheduler
    logger.info("Connecting to Google Sheets …")
    sheets_service = GoogleSheetsService()
    logger.info("Initialising Razorpay …")
    razorpay_service = RazorpayService()
    logger.info("Initialising Email …")
    email_service = EmailService()
    logger.info("Starting Reminder Scheduler …")
    reminder_scheduler = ReminderScheduler()
    reminder_scheduler.start()
    logger.info("Ready 🚀")
    yield
    if reminder_scheduler:
        reminder_scheduler.stop()
    sheets_service = None
    razorpay_service = None
    email_service = None
    reminder_scheduler = None
    logger.info("Shutdown complete")


app = FastAPI(
    title="FlowPay API",
    description="AI-native payments ops agent — Google Sheets backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(contacts.router)
app.include_router(payments.router)
app.include_router(razorpay_router.router)
app.include_router(email_router.router)
app.include_router(chat_router.router)

@app.get("/", tags=["Health"])
def root():
    """Health check."""
    return {"status": "ok", "service": "FlowPay API"}


@app.post("/reminders/trigger", tags=["Reminders"])
def trigger_reminders():
    """
    Manually trigger the reminder check (for demo).
    Scans all pending payments and sends Day 3 / Day 7 reminders.
    In production, this runs automatically every hour.
    """
    if reminder_scheduler is None:
        return {"error": "Scheduler not ready"}
    result = reminder_scheduler.run_now()
    return {"status": "ok", **result}


@app.post("/reset", tags=["Admin"])
def reset_system():
    """
    Master reset route (for demo purposes).
    Clears all payment records from the Google Sheet to start fresh.
    """
    if sheets_service is None:
        raise HTTPException(status_code=503, detail="Sheets service not ready")
    
    sheets_service.reset_payments()
    return {"status": "ok", "message": "Payments sheet reset successfully"}

