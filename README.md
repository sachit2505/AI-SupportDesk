# AI SupportDesk — Intelligent Support Triage & Knowledge Assistant

A lightweight, demonstrable 90-Minute MVP for customer support ticketing, automated AI triage, policy grounding, and a RAG-powered knowledge assistant.

---

## Overview

**AI SupportDesk** streamlines customer service by automating the initial analysis of support requests and enabling natural language question-answering over internal policies.

When a customer submits a ticket:
1. **AI Support Triage** classifies the issue into a standard category (`Billing`, `Technical Issue`, `Account`, `Subscription`, `Security`, `General`).
2. **Priority & Sentiment** are determined (`Urgent`, `High`, `Medium`, `Low` / `Positive`, `Neutral`, `Negative`).
3. **Policy Grounding**: The system searches internal Markdown knowledge articles to find relevant rules.
4. **Suggested Response**: A customer-facing response is generated, citing company policies.
5. **Support Queue**: Support agents review incoming tickets, inspect AI recommendations, and update ticket workflow status (`Open` → `In Progress` → `Resolved`).

Additionally, a standalone **RAG Knowledge Assistant** allows users to ask open-ended questions about company policies and receive answers strictly grounded in retrieved documents.

---

## Features

- **Automated AI Triage**: Structured JSON analysis with sentiment, priority, category, and concise issue summary.
- **Knowledge-Assisted Grounding**: Suggested responses link directly to verified support policies (e.g. Duplicate Payment Policy, 14-day refund window).
- **RAG Knowledge Assistant**: Vector search via ChromaDB using local sentence embeddings with source citation badges.
- **Support Dashboard**: Real-time stats (Total, Open, High/Urgent, Resolved), category/priority/status filters, and ticket workflow controls.
- **Graceful Fallback & Offline Resilience**: Full functionality works with or without external LLM API keys. Never crashes on API quota or network errors.
- **Demo Data Seeding**: Single-command or single-click seeding of 5 realistic support tickets.

---

## Architecture

```text
       ┌─────────────────────────────────────────────────────────┐
       │                   User / Support Agent                  │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                  React + Vite Frontend                  │
       │   • Support Dashboard        • Ticket Submission Form   │
       │   • Status Filter / Metrics  • RAG Knowledge Assistant  │
       └────────────────────────────┬────────────────────────────┘
                                    │ HTTP / REST (Vite Proxy)
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │                     FastAPI Backend                     │
       │  ├── Ticket Service (/api/tickets)                      │
       │  ├── AI Triage Service (app/services/ai_triage.py)      │
       │  ├── RAG Service (app/services/rag_service.py)          │
       │  └── Demo Seed Router (/api/seed)                       │
       └───────────────┬───────────────────────────┬─────────────┘
                       │                           │
                       ▼                           ▼
            ┌──────────────────────┐    ┌──────────────────────┐
            │   SQLite Database    │    │  ChromaDB Vector DB  │
            │ (data/supportdesk.db)│    │  (data/chroma_db/)   │
            └──────────────────────┘    └──────────┬───────────┘
                                                   │
                                                   ▼
                                        ┌──────────────────────┐
                                        │ 8 Knowledge Articles │
                                        │  (knowledge_base/)   │
                                        └──────────────────────┘
```

---

## Knowledge Base Articles

Located in `knowledge_base/` and `backend/knowledge_base/`:
1. `password_reset_policy.md`
2. `refund_policy.md`
3. `duplicate_payment_policy.md`
4. `subscription_cancellation.md`
5. `account_lockout.md`
6. `two_factor_authentication.md`
7. `payment_failure.md`
8. `contact_support_policy.md`

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Verifies server and SQLite database connection |
| `GET` | `/api/tickets/stats` | Summary counts (total, open, high/urgent, resolved) |
| `GET` | `/api/tickets` | List tickets (supports `?status=`, `?priority=`, `?category=`) |
| `POST` | `/api/tickets` | Create ticket, run AI triage & policy grounding |
| `GET` | `/api/tickets/{id}` | Retrieve ticket details |
| `PATCH` | `/api/tickets/{id}` | Update ticket fields (e.g. `status`) |
| `DELETE` | `/api/tickets/{id}` | Delete ticket |
| `POST` | `/api/assistant/ask` | Ask RAG Knowledge Assistant (`{"question": "..."}`) |
| `POST` | `/api/assistant/index` | Re-index Markdown documents into ChromaDB |
| `GET` | `/api/assistant/documents` | List available knowledge base articles |
| `POST` | `/api/seed` | Populate 5 realistic demo tickets |

---

## Project Structure

```text
ai-support-desk/
├── .env.example                     # Root environment configuration template
├── .gitignore                       # Clean gitignore (venv, node_modules, .db, .env)
├── README.md                        # Documentation and run instructions
├── knowledge_base/                  # 8 support policy Markdown documents
│   ├── password_reset_policy.md
│   ├── refund_policy.md
│   ├── duplicate_payment_policy.md
│   ├── subscription_cancellation.md
│   ├── account_lockout.md
│   ├── two_factor_authentication.md
│   ├── payment_failure.md
│   └── contact_support_policy.md
├── backend/
│   ├── .env                         # Local backend configuration
│   ├── .env.example                 # Backend environment template
│   ├── requirements.txt             # Pinned backend dependencies
│   ├── data/
│   │   ├── supportdesk.db           # SQLite database
│   │   └── chroma_db/               # ChromaDB persistent vector index
│   ├── app/
│   │   ├── main.py                  # FastAPI app & lifespan indexing
│   │   ├── config.py                # Environment configuration loader
│   │   ├── database.py              # SQLite session & table creation
│   │   ├── seed.py                  # CLI demo data generator
│   │   ├── models/ticket.py         # SQLAlchemy Ticket table model
│   │   ├── schemas/ticket.py        # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── tickets.py           # Ticket CRUD & stats
│   │   │   ├── assistant.py         # RAG Q&A endpoints
│   │   │   └── seed.py              # Seeding API endpoint
│   │   └── services/
│   │       ├── llm_client.py        # Gemini & OpenAI client + JSON cleaner
│   │       ├── rag_service.py       # ChromaDB indexer & retriever
│   │       └── ai_triage.py         # AI categorization & grounded response
│   └── tests/
│       └── test_backend.py          # Automated test suite (8 tests)
└── frontend/
    ├── package.json                 # React 18, Vite dependencies
    ├── vite.config.js               # Proxy /api to http://127.0.0.1:8000
    ├── index.html                   # Mount point
    └── src/
        ├── App.jsx                  # Main multi-tab application
        ├── App.css                  # UI styling & design system
        ├── services/api.js          # Centralized API fetch methods
        └── components/
            ├── DashboardView.jsx    # Metric cards, filters, and ticket list
            ├── TicketForm.jsx       # Customer submission form with triage output
            ├── TicketDetailModal.jsx# Ticket review, response copy & status changer
            └── KnowledgeAssistant.jsx# RAG question answering with citations
```

---

## Environment Variables

Copy `.env.example` to `.env` or set environment variables:

```ini
# Backend Server Configuration
HOST=127.0.0.1
PORT=8000
DEBUG=True

# SQLite Database
DATABASE_URL=sqlite:///./data/supportdesk.db

# CORS Allowed Origins
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# LLM Providers (Optional - application runs out-of-the-box with built-in fallback)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

---

## Installation & Running

### 1. Backend Setup

```powershell
cd C:\Users\SACHIT\.gemini\antigravity\scratch\ai-support-desk\backend

# Run directly via virtual environment Python
.\venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```
- **API Root**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 2. Frontend Setup

```powershell
cd C:\Users\SACHIT\.gemini\antigravity\scratch\ai-support-desk\frontend

# Start Vite development server
npm run dev
```
- Open [http://localhost:5173](http://localhost:5173)

---

## Useful Development Commands

### Seed Demo Tickets
Populate 5 realistic sample tickets (duplicate charge, lockout, password reset, etc.):
```powershell
# In backend directory:
.\venv\Scripts\python -m app.seed --force
```
*(Or click **"⚡ Seed Demo Tickets"** on the dashboard toolbar).*

### Re-Index Knowledge Base
Force re-indexing of Markdown files into ChromaDB:
```powershell
.\venv\Scripts\python -c "from app.services.rag_service import index_knowledge_base; print(index_knowledge_base(force=True))"
```

### Run Backend Tests
Execute the automated test suite:
```powershell
.\venv\Scripts\python -m unittest tests/test_backend.py
```

---

## 2-Minute Demo Script

Follow this walkthrough to showcase the end-to-end functionality:

1. **Check System Health & Stats**:
   - Open [http://localhost:5173](http://localhost:5173).
   - Observe the green status indicator: `Backend: Online (DB: connected)`.
   - The top metrics show `Total Tickets: 5`, `Open Tickets: 5`, and `High / Urgent: 3`.

2. **Inspect an AI-Triaged Ticket**:
   - In the support queue, click on **Ticket #1**: *"Charged twice for monthly Pro subscription"*.
   - View the **AI Triage Summary**: Identified as **Billing**, **High Priority**, **Negative Sentiment**.
   - Note the **Grounded Knowledge Policy**: `📖 Duplicate Payment Policy`.
   - See the **Suggested Response**: Accurately references the policy guarantee of a 100% full refund within 24 hours.
   - Click **"📋 Copy Response"** to copy the text to your clipboard.
   - Click **"Mark In Progress"** or **"✓ Mark Resolved"** and notice the status update dynamically reflected on the dashboard metrics.

3. **Submit a New Support Ticket**:
   - Switch to the **"✍ Submit New Ticket"** tab.
   - Enter:
     - **Issue Summary**: `Account locked after multiple wrong passwords`
     - **Description**: `I entered my old password 5 times by accident and now the system says my account is locked.`
   - Click **"Submit Ticket & Run AI Triage"**.
   - Notice the instant AI classification: Category `Security`, Priority `Urgent`, Sentiment `Negative`, with instructions from the `Account Lockout Policy` to reset via email or admin console.
   - Click **"View on Dashboard →"** to see your new ticket at the top of the queue.

4. **Test the RAG Knowledge Assistant**:
   - Switch to the **"🤖 Knowledge Assistant (RAG)"** tab.
   - Click one of the suggestion chips: *"What is your refund policy for annual plans?"*.
   - Click **"Ask Assistant"**.
   - Observe the grounded answer citing the 14-day 100% refund window, accompanied by source badge: `📄 Refund Policy`.
   - Try another question: *"How do I recover access if I lost my 2FA phone?"* and observe the grounded answer citing emergency backup recovery codes.
