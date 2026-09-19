"""
Demo Seed Script for AI SupportDesk
Populates 5 realistic tickets covering different categories with AI triage.
Usage:
    python -m app.seed
"""

import sys
import json
from app.database import SessionLocal, init_db
from app.models.ticket import Ticket
from app.services.ai_triage import triage_ticket

DEMO_TICKETS = [
    {
        "issue_summary": "Charged twice for monthly Pro subscription",
        "description": "I noticed two identical charges of $49.00 on my credit card statement dated yesterday. Please refund the duplicate payment as soon as possible.",
    },
    {
        "issue_summary": "Password reset verification email not arriving",
        "description": "I requested a password reset link 20 minutes ago, but nothing has shown up in my inbox or spam folder. My account email is alex.turner@example.com.",
    },
    {
        "issue_summary": "Account locked after multiple failed login attempts",
        "description": "Our marketing manager attempted to log in with the wrong password and now our primary account is completely locked. We have a live product launch today and need access restored immediately!",
    },
    {
        "issue_summary": "Payment failed for annual renewal with card error",
        "description": "Our company credit card was declined during yesterday's renewal attempt. We received a notification stating our subscription might be suspended. How do we update our card and retry the payment?",
    },
    {
        "issue_summary": "Lost phone with Two-Factor Authentication (2FA) app",
        "description": "My phone was damaged yesterday and I can no longer access Google Authenticator. I don't have my recovery codes written down. How can I regain access to my workspace?",
    },
]


def seed_database(clear_existing: bool = False):
    """Seed the database with realistic demo tickets and run triage."""
    init_db()
    db = SessionLocal()
    try:
        if clear_existing:
            db.query(Ticket).delete()
            db.commit()
            print("Cleared existing tickets.")

        existing_count = db.query(Ticket).count()
        if existing_count > 0 and not clear_existing:
            print(f"Database already contains {existing_count} tickets. Skipping seed. (Use --force to clear and re-seed)")
            return existing_count

        created_count = 0
        for item in DEMO_TICKETS:
            triage = triage_ticket(item["issue_summary"], item["description"])
            ticket = Ticket(
                issue_summary=item["issue_summary"],
                description=item["description"],
                category=triage.category,
                priority=triage.priority,
                sentiment=triage.sentiment,
                ai_summary=triage.summary,
                suggested_response=triage.suggested_response,
                relevant_articles=json.dumps(triage.relevant_articles),
                status="Open",
            )
            db.add(ticket)
            created_count += 1

        db.commit()
        print(f"Successfully seeded {created_count} demo tickets with AI triage into SQLite database!")
        return created_count
    finally:
        db.close()


if __name__ == "__main__":
    force = "--force" in sys.argv or "-f" in sys.argv
    seed_database(clear_existing=force)
