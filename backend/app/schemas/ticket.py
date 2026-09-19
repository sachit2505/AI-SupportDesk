from datetime import datetime
from typing import Optional, List
import json
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class TicketCreate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    issue_summary: Optional[str] = Field(None, min_length=3, max_length=255)
    description: str = Field(..., min_length=5, description="Detailed customer issue description")

    @model_validator(mode="after")
    def populate_summary(self):
        # Support either 'title' or 'issue_summary'
        if not self.issue_summary and not self.title:
            raise ValueError("Either 'issue_summary' or 'title' must be provided.")
        if not self.issue_summary:
            self.issue_summary = self.title
        if not self.title:
            self.title = self.issue_summary
        return self


class TicketUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(Open|In Progress|Resolved)$")
    category: Optional[str] = None
    priority: Optional[str] = None
    sentiment: Optional[str] = None
    ai_summary: Optional[str] = None
    suggested_response: Optional[str] = None


class TicketResponse(BaseModel):
    id: int
    issue_summary: str
    title: str
    description: str
    category: str
    priority: str
    sentiment: str
    ai_summary: Optional[str] = None
    summary: Optional[str] = None
    suggested_response: Optional[str] = None
    relevant_articles: List[str] = Field(default_factory=list)
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def format_ticket(cls, data: any):
        # Handle SQLAlchemy model or dict conversion
        if hasattr(data, "issue_summary"):
            articles = []
            if hasattr(data, "relevant_articles") and data.relevant_articles:
                try:
                    articles = json.loads(data.relevant_articles)
                except Exception:
                    articles = [data.relevant_articles]

            return {
                "id": data.id,
                "issue_summary": data.issue_summary,
                "title": data.issue_summary,
                "description": data.description,
                "category": data.category,
                "priority": data.priority,
                "sentiment": data.sentiment,
                "ai_summary": data.ai_summary,
                "summary": data.ai_summary,
                "suggested_response": data.suggested_response,
                "relevant_articles": articles,
                "status": data.status,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data


class DashboardStats(BaseModel):
    total: int
    open: int
    high_urgent: int
    resolved: int


class AssistantAskRequest(BaseModel):
    question: str = Field(..., min_length=2, description="User question to knowledge assistant")


class AssistantAskResponse(BaseModel):
    answer: str
    sources: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: str
