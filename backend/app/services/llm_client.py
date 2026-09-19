"""
LLM Client for AI SupportDesk
Supports Google Gemini, OpenAI, and graceful local fallback.
Never crashes when keys are missing or requests fail.
"""

import json
import logging
import re
from typing import Optional, Dict, Any
import httpx

from app.config import GEMINI_API_KEY, OPENAI_API_KEY

logger = logging.getLogger("supportdesk.llm")


def clean_json_text(raw_text: str) -> str:
    """Extract JSON block from markdown fences if present."""
    text = raw_text.strip()
    if "```json" in text:
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
    elif "```" in text:
        match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
    return text


def call_gemini(prompt: str, system_instruction: Optional[str] = None, timeout: float = 15.0) -> Optional[str]:
    """Call Google Gemini REST API."""
    if not GEMINI_API_KEY:
        return None

    # Using gemini-2.5-flash or gemini-1.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    contents = []
    if system_instruction:
        contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_instruction}\n\nUSER REQUEST: {prompt}"}]})
    else:
        contents.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        }
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            else:
                logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"Gemini API request failed: {e}")
    return None


def call_openai(prompt: str, system_instruction: Optional[str] = None, timeout: float = 15.0) -> Optional[str]:
    """Call OpenAI Chat Completions REST API."""
    if not OPENAI_API_KEY:
        return None

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1024,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
            else:
                logger.warning(f"OpenAI API returned status {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"OpenAI API request failed: {e}")
    return None


def call_llm(prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
    """
    Attempt calling available LLM providers in order of preference (Gemini -> OpenAI).
    Returns None if no API keys configured or if calls fail.
    """
    # 1. Try Gemini
    if GEMINI_API_KEY:
        res = call_gemini(prompt, system_instruction)
        if res:
            return res

    # 2. Try OpenAI
    if OPENAI_API_KEY:
        res = call_openai(prompt, system_instruction)
        if res:
            return res

    return None
