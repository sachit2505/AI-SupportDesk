from fastapi import APIRouter
from app.seed import seed_database

router = APIRouter(prefix="/api/seed", tags=["Demo Seed"])


@router.post("")
def trigger_seed(force: bool = False):
    """Seed the database with 5 realistic demo tickets and AI triage."""
    count = seed_database(clear_existing=force)
    return {"status": "success", "seeded_tickets": count}
