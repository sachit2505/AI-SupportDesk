"""
AI Support Triage Service
Analyzes tickets for Category, Priority, Sentiment, Summary,
and synthesizes a suggested response grounded in relevant Knowledge Base articles.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.services.llm_client import call_llm, clean_json_text
from app.services.rag_service import search_knowledge_base

logger = logging.getLogger("supportdesk.triage")

VALID_CATEGORIES = ["Billing", "Technical Issue", "Account", "Subscription", "Security", "General"]
VALID_PRIORITIES = ["Low", "Medium", "High", "Urgent"]
VALID_SENTIMENTS = ["Positive", "Neutral", "Negative"]


class TriageResult(BaseModel):
    category: str
    priority: str
    sentiment: str
    summary: str
    suggested_response: str
    relevant_articles: List[str] = Field(default_factory=list)
    is_fallback: bool = False


def fallback_triage(title: str, description: str, relevant_articles: List[str]) -> TriageResult:
    """
    Intelligent heuristic fallback when LLM API keys are missing or API calls fail.
    Grounded in support knowledge base policies.
    """
    content = f"{title} {description}".lower()

    # Rule matching
    if any(w in content for w in ["twice", "duplicate", "charged twice", "double charge"]):
        category = "Billing"
        priority = "High"
        sentiment = "Negative"
        summary = "Customer reports being charged twice for their subscription."
        suggested_response = (
            "Hello, thank you for contacting SupportDesk. We apologize for the duplicate charge. "
            "According to our Duplicate Payment Policy, accidental duplicate charges are 100% refunded "
            "within 24 hours. Please provide the last 4 digits of your card and transaction dates so we can "
            "immediately process the refund to your original payment method."
        )
    elif any(w in content for w in ["refund", "billing", "invoice", "overcharge", "receipt"]):
        category = "Billing"
        priority = "High" if "urgent" in content or "unauthorized" in content else "Medium"
        sentiment = "Negative" if "wrong" in content or "angry" in content or "unauthorized" in content else "Neutral"
        summary = "Customer has a billing or refund inquiry regarding their account."
        suggested_response = (
            "Hello, thank you for contacting billing support. Under our Refund Policy, annual plans are eligible "
            "for a full refund within 14 days of purchase or renewal. Monthly plans remain active until the end of the "
            "current billing cycle. Please provide your invoice or transaction ID for further assistance."
        )
    elif any(w in content for w in ["locked", "lockout", "brute", "5 attempts", "cannot log in", "locked out"]):
        category = "Security"
        priority = "Urgent"
        sentiment = "Negative"
        summary = "User account locked due to security policy or multiple failed logins."
        suggested_response = (
            "Hello, we apologize for the inconvenience. Under our Account Lockout Policy, accounts are locked for "
            "30 minutes after 5 consecutive failed login attempts to protect against unauthorized access. "
            "You can unlock your account immediately by clicking 'Forgot Password' on the login screen to verify your email. "
            "Alternatively, an administrator can unlock your profile from the Admin Console."
        )
    elif any(w in content for w in ["2fa", "two-factor", "authenticator", "otp", "backup code", "lost phone"]):
        category = "Security"
        priority = "High"
        sentiment = "Negative"
        summary = "Customer unable to complete Two-Factor Authentication or lost authenticator."
        suggested_response = (
            "Hello, thank you for reaching out. Under our Two-Factor Authentication Guide, you can log in using one of "
            "the 8-digit emergency backup recovery codes provided during 2FA setup. If you do not have backup codes, "
            "a SupportDesk Super Admin can initiate identity verification to reset 2FA for you."
        )
    elif any(w in content for w in ["password", "reset", "login", "credentials"]):
        category = "Account"
        priority = "Medium"
        sentiment = "Neutral"
        summary = "User requesting password reset instructions or experiencing credential issues."
        suggested_response = (
            "Hello, you can reset your password anytime by clicking 'Forgot Password' on the login screen. "
            "A 6-digit verification code will be sent to your primary email address (valid for 15 minutes). "
            "Please ensure your new password contains at least 8 characters, including uppercase, lowercase, numbers, and special symbols."
        )
    elif any(w in content for w in ["cancel", "subscription", "unsubscribe", "downgrade"]):
        category = "Subscription"
        priority = "Medium"
        sentiment = "Neutral"
        summary = "Customer requesting subscription cancellation or downgrade details."
        suggested_response = (
            "Hello, you can cancel your subscription at any time by navigating to Settings > Billing & Plan > Cancel Subscription. "
            "Your access will remain active on your current tier until the end of the billing period, and your data is "
            "safely retained for 90 days."
        )
    elif any(w in content for w in ["crash", "error", "bug", "broken", "500", "429", "timeout", "slow"]):
        category = "Technical Issue"
        priority = "High" if any(w in content for w in ["down", "production", "crash"]) else "Medium"
        sentiment = "Negative"
        summary = "Customer reporting technical error or unexpected system behavior."
        suggested_response = (
            "Hello, thank you for bringing this technical issue to our attention. Our engineering team is investigating. "
            "If you are receiving an API 429 error, please verify your rate limit tier or apply exponential backoff. "
            "We will follow up with an update shortly."
        )
    else:
        category = "General"
        priority = "Medium"
        sentiment = "Neutral"
        summary = f"Support inquiry: {title[:80]}"
        suggested_response = (
            "Hello, thank you for reaching out to SupportDesk. We have logged your ticket and an agent is currently "
            "reviewing the details. We will respond within our standard SLA window."
        )

    return TriageResult(
        category=category,
        priority=priority,
        sentiment=sentiment,
        summary=summary,
        suggested_response=suggested_response,
        relevant_articles=relevant_articles,
        is_fallback=True,
    )


def triage_ticket(title: str, description: str) -> TriageResult:
    """
    Full AI Support Triage Pipeline:
    1. Search Knowledge Base for relevant policy articles.
    2. Prompt LLM for structured JSON (Category, Priority, Sentiment, Summary, Suggested Response).
    3. Validate and ground response in KB policies.
    4. Fall back seamlessly if LLM fails or is unavailable.
    """
    # 1. Retrieve relevant knowledge base articles for context grounding
    search_query = f"{title} {description}"
    search_results = search_knowledge_base(search_query, n_results=2)
    relevant_articles = []
    policy_context_list = []

    for res in search_results:
        art_title = res.get("title", "")
        if art_title and art_title not in relevant_articles:
            relevant_articles.append(art_title)
            policy_context_list.append(f"Policy: {art_title}\n{res.get('text', '')}")

    policy_context = "\n\n".join(policy_context_list)

    # 2. Build structured LLM prompt
    system_instruction = (
        "You are an expert AI SupportDesk Triage Agent. Analyze incoming customer support tickets "
        "and provide accurate classification and an empathetic, policy-grounded suggested response.\n\n"
        "Categories must be exactly one of: ['Billing', 'Technical Issue', 'Account', 'Subscription', 'Security', 'General'].\n"
        "Priorities must be exactly one of: ['Low', 'Medium', 'High', 'Urgent'].\n"
        "Sentiments must be exactly one of: ['Positive', 'Neutral', 'Negative'].\n"
        "Provide your answer STRICTLY as a valid JSON object matching this schema:\n"
        "{\n"
        '  "category": "string",\n'
        '  "priority": "string",\n'
        '  "sentiment": "string",\n'
        '  "summary": "concise 1-2 sentence summary of the issue",\n'
        '  "suggested_response": "polite, helpful customer response grounded in the provided policy"\n'
        "}"
    )

    user_prompt = (
        f"CUSTOMER TICKET:\n"
        f"Title: {title}\n"
        f"Description: {description}\n\n"
        f"RELEVANT SUPPORT POLICIES:\n{policy_context}\n\n"
        "Analyze this ticket and generate the structured JSON triage."
    )

    raw_llm_response = call_llm(user_prompt, system_instruction=system_instruction)

    if raw_llm_response:
        try:
            json_text = clean_json_text(raw_llm_response)
            data = json.loads(json_text)

            # Validate & normalize fields
            cat = data.get("category", "General")
            prio = data.get("priority", "Medium")
            sent = data.get("sentiment", "Neutral")

            cat_norm = next((c for c in VALID_CATEGORIES if c.lower() == str(cat).lower()), "General")
            prio_norm = next((p for p in VALID_PRIORITIES if p.lower() == str(p).lower()), "Medium")
            sent_norm = next((s for s in VALID_SENTIMENTS if s.lower() == str(sent).lower()), "Neutral")

            summary = data.get("summary", f"Issue regarding {title}").strip()
            suggested_resp = data.get("suggested_response", "").strip()

            if not suggested_resp:
                suggested_resp = f"Thank you for contacting support regarding {title}. We are reviewing your ticket."

            return TriageResult(
                category=cat_norm,
                priority=prio_norm,
                sentiment=sent_norm,
                summary=summary,
                suggested_response=suggested_resp,
                relevant_articles=relevant_articles,
                is_fallback=False,
            )
        except Exception as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}. Falling back to heuristic triage.")

    # 3. Fallback when LLM is unavailable or unparseable
    return fallback_triage(title, description, relevant_articles)
