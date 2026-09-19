import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.ticket import Ticket
from app.schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    DashboardStats,
)
from app.services.ai_triage import triage_ticket

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


@router.get("/stats", response_model=DashboardStats)
def get_ticket_stats(db: Session = Depends(get_db)):
    """Retrieve summary metrics for the support dashboard."""
    total = db.query(func.count(Ticket.id)).scalar() or 0
    open_count = db.query(func.count(Ticket.id)).filter(Ticket.status == "Open").scalar() or 0
    resolved_count = db.query(func.count(Ticket.id)).filter(Ticket.status == "Resolved").scalar() or 0
    high_urgent_count = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.priority.in_(["High", "Urgent"]))
        .filter(Ticket.status != "Resolved")
        .scalar()
        or 0
    )

    return DashboardStats(
        total=total,
        open=open_count,
        high_urgent=high_urgent_count,
        resolved=resolved_count,
    )


@router.get("", response_model=List[TicketResponse])
def get_all_tickets(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    category_filter: Optional[str] = Query(None, alias="category"),
    db: Session = Depends(get_db),
):
    """Retrieve all tickets ordered by creation time descending with optional filters."""
    query = db.query(Ticket)

    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if priority_filter:
        query = query.filter(Ticket.priority == priority_filter)
    if category_filter:
        query = query.filter(Ticket.category == category_filter)

    tickets = query.order_by(Ticket.created_at.desc()).all()
    return tickets


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(ticket_in: TicketCreate, db: Session = Depends(get_db)):
    """
    Create a new support ticket:
    1. Triggers AI Support Triage (Category, Priority, Sentiment, Summary).
    2. RAG Knowledge retrieval for suggested grounded response.
    3. Persists ticket in SQLite database.
    """
    issue_text = ticket_in.issue_summary or ticket_in.title or ""
    desc_text = ticket_in.description.strip()

    if not issue_text.strip():
        raise HTTPException(status_code=400, detail="Ticket issue summary cannot be empty.")

    # Execute AI Triage & Knowledge-Assisted Response
    triage = triage_ticket(title=issue_text, description=desc_text)

    new_ticket = Ticket(
        issue_summary=issue_text.strip(),
        description=desc_text,
        category=triage.category,
        priority=triage.priority,
        sentiment=triage.sentiment,
        ai_summary=triage.summary,
        suggested_response=triage.suggested_response,
        relevant_articles=json.dumps(triage.relevant_articles),
        status="Open",
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Retrieve a single ticket by its ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(ticket_id: int, update_in: TicketUpdate, db: Session = Depends(get_db)):
    """Update ticket fields such as status ('Open', 'In Progress', 'Resolved')."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found")

    update_data = update_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Delete a ticket by ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket #{ticket_id} not found")
    db.delete(ticket)
    db.commit()
    return None
