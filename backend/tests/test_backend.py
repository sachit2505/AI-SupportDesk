"""
Backend Automated Test Suite for AI SupportDesk
Tests ticket creation, AI triage, status updates, health checks, RAG assistant, and error validation.
"""

import unittest
from starlette.testclient import TestClient
from app.main import app
from app.database import SessionLocal, init_db
from app.models.ticket import Ticket
from app.services.ai_triage import fallback_triage


class TestSupportDeskBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def setUp(self):
        # Clean up tickets before test
        db = SessionLocal()
        db.query(Ticket).delete()
        db.commit()
        db.close()

    def test_health_endpoint(self):
        """Test GET /api/health returns 200 and healthy status."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["database"], "connected")

    def test_ticket_creation_and_ai_triage(self):
        """Test POST /api/tickets triggers AI triage and persists to SQLite."""
        payload = {
            "title": "Charged twice on credit card",
            "description": "I have two duplicate charges for $49 on my Visa statement."
        }
        response = self.client.post("/api/tickets", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["category"], "Billing")
        self.assertEqual(data["priority"], "High")
        self.assertEqual(data["sentiment"], "Negative")
        self.assertIn("Duplicate Payment Policy", data["relevant_articles"])
        self.assertTrue(len(data["suggested_response"]) > 20)

    def test_ticket_retrieval_and_filtering(self):
        """Test GET /api/tickets lists tickets and GET /api/tickets/{id} retrieves specific ticket."""
        # Create ticket
        create_resp = self.client.post("/api/tickets", json={
            "issue_summary": "Cannot reset account password",
            "description": "Password verification email is not arriving in my inbox."
        })
        ticket_id = create_resp.json()["id"]

        # List all
        list_resp = self.client.get("/api/tickets")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(len(list_resp.json()), 1)

        # Retrieve by ID
        get_resp = self.client.get(f"/api/tickets/{ticket_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["id"], ticket_id)
        self.assertEqual(get_resp.json()["category"], "Account")

    def test_ticket_status_update(self):
        """Test PATCH /api/tickets/{id} updates ticket status."""
        create_resp = self.client.post("/api/tickets", json={
            "issue_summary": "Account locked after failed login",
            "description": "Locked out after typing incorrect password 5 times."
        })
        ticket_id = create_resp.json()["id"]

        # Update status to In Progress
        patch_resp = self.client.patch(f"/api/tickets/{ticket_id}", json={"status": "In Progress"})
        self.assertEqual(patch_resp.status_code, 200)
        self.assertEqual(patch_resp.json()["status"], "In Progress")

        # Update status to Resolved
        patch_resp2 = self.client.patch(f"/api/tickets/{ticket_id}", json={"status": "Resolved"})
        self.assertEqual(patch_resp2.status_code, 200)
        self.assertEqual(patch_resp2.json()["status"], "Resolved")

    def test_dashboard_stats(self):
        """Test GET /api/tickets/stats returns accurate metrics."""
        # Create 1 Open, 1 Resolved
        t1 = self.client.post("/api/tickets", json={
            "issue_summary": "Urgent lockout issue",
            "description": "Complete account lockout preventing access to production."
        }).json()

        t2 = self.client.post("/api/tickets", json={
            "issue_summary": "General question",
            "description": "Where can I read the product documentation?"
        }).json()

        self.client.patch(f"/api/tickets/{t2['id']}", json={"status": "Resolved"})

        stats_resp = self.client.get("/api/tickets/stats")
        self.assertEqual(stats_resp.status_code, 200)
        stats = stats_resp.json()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["open"], 1)
        self.assertEqual(stats["resolved"], 1)

    def test_knowledge_assistant_endpoint(self):
        """Test POST /api/assistant/ask retrieves grounded policy answer."""
        query = {"question": "What is the refund policy for annual subscriptions?"}
        resp = self.client.post("/api/assistant/ask", json=query)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(len(data["answer"]) > 20)
        self.assertIn("Refund Policy", data["sources"])

    def test_assistant_validation_error(self):
        """Test empty question validation in assistant endpoint."""
        resp = self.client.post("/api/assistant/ask", json={"question": "   "})
        self.assertEqual(resp.status_code, 400)

    def test_ai_fallback_triage_behavior(self):
        """Test fallback heuristic triage directly."""
        res = fallback_triage(
            title="Lost Two-Factor Authentication phone",
            description="My phone broke and I cannot enter the 2FA code.",
            relevant_articles=["Two-Factor Authentication (2FA) Guide"]
        )
        self.assertEqual(res.category, "Security")
        self.assertEqual(res.priority, "High")
        self.assertEqual(res.sentiment, "Negative")
        self.assertTrue(res.is_fallback)


if __name__ == "__main__":
    unittest.main()
