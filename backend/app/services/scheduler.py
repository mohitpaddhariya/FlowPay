"""
Payment reminder scheduler — periodically checks pending payments
and sends reminders based on how many days have passed since creation.

Schedule:
  - Day 3: Polite reminder (level 1)
  - Day 7: Firm/final reminder (level 2)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

# How many days → which reminder level
REMINDER_SCHEDULE = [
    (3, 1),    # Day 3  → polite
    (7, 2),    # Day 7  → firm
    (14, 3),   # Day 14 → final notice
]


class ReminderScheduler:
    """Background scheduler that checks pending payments and sends reminders."""

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler()
        # Run the check every hour
        self._scheduler.add_job(
            self._check_and_send_reminders,
            "interval",
            hours=1,
            id="payment_reminders",
            name="Check pending payments & send reminders",
        )
        logger.info("Reminder scheduler initialised ✓")

    def start(self) -> None:
        """Start the background scheduler."""
        self._scheduler.start()
        logger.info("Reminder scheduler started (runs every hour)")

    def stop(self) -> None:
        """Shutdown the scheduler gracefully."""
        self._scheduler.shutdown(wait=False)
        logger.info("Reminder scheduler stopped")

    def run_now(self) -> dict:
        """
        Manually trigger the reminder check (useful for demo).
        Returns a summary of what was sent.
        """
        return self._check_and_send_reminders()

    def _check_and_send_reminders(self) -> dict:
        """
        Core logic: iterate all pending payments, compute days since creation,
        and send the appropriate reminder if not already sent at that level.
        """
        # Lazy imports to avoid circular dependencies
        from app.main import sheets_service, email_service

        if sheets_service is None or email_service is None:
            logger.warning("Services not ready — skipping reminder check")
            return {"skipped": True}

        now = datetime.now(timezone.utc)
        all_payments = sheets_service.get_all_payments()
        sent_count = 0
        checked_count = 0

        for idx, payment in enumerate(all_payments, start=2):
            # Only process pending or partial payments with a Razorpay link
            if payment.status not in ("pending", "partial"):
                continue
            if not payment.razorpay_link_url:
                continue

            checked_count += 1

            # Parse created_at
            try:
                created = datetime.strptime(
                    payment.created_at, "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue

            days_elapsed = (now - created).days

            # Determine which reminder to send
            reminder_level = None
            for day_threshold, level in sorted(REMINDER_SCHEDULE, reverse=True):
                if days_elapsed >= day_threshold:
                    reminder_level = level
                    break

            if reminder_level is None:
                continue  # Not due for any reminder yet

            # Check if we already sent this level
            # We encode the level in last_reminder_at as "YYYY-MM-DD|level"
            last_reminder = payment.last_reminder_at or ""
            if f"|{reminder_level}" in last_reminder:
                continue  # Already sent this level

            # Calculate remaining balance for the reminder
            amount_due = payment.amount
            if payment.status == "partial":
                amount_due = payment.amount - payment.amount_paid
                if amount_due <= 0:
                    continue  # Shouldn't happen, but just in case

            # Send the reminder
            try:
                email_service.send_reminder_email(
                    customer_name=payment.name,
                    customer_email=payment.email,
                    amount=amount_due,
                    description=payment.description,
                    payment_url=payment.razorpay_link_url,
                    due_date=payment.due_date,
                    reminder_level=reminder_level,
                )
                # Update last_reminder_at in the sheet
                from app.models.payment import PaymentUpdate

                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                sheets_service.update_payment(
                    idx,
                    PaymentUpdate(last_reminder_at=f"{now_str}|{reminder_level}"),
                )
                sent_count += 1
                logger.info(
                    "Sent level-%d reminder to %s for '%s' (Amount due: ₹%.2f)",
                    reminder_level,
                    payment.email,
                    payment.description,
                    amount_due,
                )
            except Exception:
                logger.exception("Failed to send reminder to %s", payment.email)

        logger.info(
            "Reminder check: %d pending payments checked, %d reminders sent",
            checked_count,
            sent_count,
        )
        return {"checked": checked_count, "sent": sent_count}
