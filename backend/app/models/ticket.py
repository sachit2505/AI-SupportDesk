import json
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    issue_summary = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # AI Triage Fields
    category = Column(String(100), default="General", nullable=False)
    priority = Column(String(50), default="Medium", nullable=False)
    sentiment = Column(String(50), default="Neutral", nullable=False)
    ai_summary = Column(Text, nullable=True)
    suggested_response = Column(Text, nullable=True)
    relevant_articles = Column(Text, nullable=True)  # JSON-encoded list of article titles

    # Ticket Workflow Status (Open, In Progress, Resolved)
    status = Column(String(50), default="Open", nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Aliases for backward compatibility with Phase 1
    @property
    def title(self) -> str:
        return self.issue_summary

    @title.setter
    def title(self, value: str):
        self.issue_summary = value

    @property
    def summary(self) -> str:
        return self.ai_summary

    @summary.setter
    def summary(self, value: str):
        self.ai_summary = value

    def get_articles_list(self) -> list:
        if not self.relevant_articles:
            return []
        try:
            return json.loads(self.relevant_articles)
        except Exception:
            return [self.relevant_articles]

    def set_articles_list(self, articles: list):
        self.relevant_articles = json.dumps(articles) if articles else "[]"

    def __repr__(self):
        return f"<Ticket #{self.id} issue={self.issue_summary[:30]!r} prio={self.priority} status={self.status}>"
