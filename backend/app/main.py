import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import CORS_ORIGINS, DEBUG
from app.database import init_db, get_db
from app.routers.tickets import router as tickets_router
from app.routers.assistant import router as assistant_router
from app.routers.seed import router as seed_router
from app.schemas.ticket import HealthResponse
from app.services.rag_service import index_knowledge_base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("supportdesk")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize database schema
    logger.info("Initializing SQLite database...")
    init_db()

    # 2. Automatically index knowledge base articles into ChromaDB
    try:
        logger.info("Indexing Knowledge Base documents into ChromaDB...")
        kb_result = index_knowledge_base(force=False)
        logger.info(f"Knowledge Base ready: {kb_result.get('total_chunks', 0)} chunks indexed.")
    except Exception as e:
        logger.warning(f"Initial knowledge base indexing encountered an issue: {e}")

    yield
    # Shutdown steps if needed


app = FastAPI(
    title="AI SupportDesk API",
    description="Intelligent Support Triage & Knowledge Assistant API (90-Minute MVP)",
    version="0.2.0",
    lifespan=lifespan,
    debug=DEBUG,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler to avoid exposing stack traces
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )

# Include Routers
app.include_router(tickets_router)
app.include_router(assistant_router)
app.include_router(seed_router)


@app.get("/", tags=["Root"])
def read_root():
    return {
        "name": "AI SupportDesk API",
        "version": "0.2.0",
        "docs_url": "/docs",
        "health_url": "/api/health",
        "status": "online",
        "features": [
            "Ticket System with AI Triage",
            "RAG Knowledge Assistant",
            "SQLite Persistence",
            "Demo Data Seeding",
        ],
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Check API and database connectivity."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    return HealthResponse(
        status="healthy",
        database=db_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
