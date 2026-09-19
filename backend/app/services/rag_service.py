"""
RAG Service for AI SupportDesk
Indexes support documents into ChromaDB, retrieves relevant policy chunks,
and answers user queries grounded in knowledge articles.
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Any

import chromadb
from chromadb.config import Settings

from app.services.llm_client import call_llm

logger = logging.getLogger("supportdesk.rag")

# Locate knowledge base directories
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
KB_DIR_BACKEND = BACKEND_DIR / "knowledge_base"
KB_DIR_ROOT = BACKEND_DIR.parent / "knowledge_base"

CHROMA_DATA_DIR = BACKEND_DIR / "data" / "chroma_db"
CHROMA_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DATA_DIR),
    settings=Settings(anonymized_telemetry=False)
)

COLLECTION_NAME = "support_knowledge_base"


def get_kb_directory() -> Path:
    """Find the active knowledge base directory."""
    if KB_DIR_BACKEND.exists() and any(KB_DIR_BACKEND.glob("*.md")):
        return KB_DIR_BACKEND
    if KB_DIR_ROOT.exists() and any(KB_DIR_ROOT.glob("*.md")):
        return KB_DIR_ROOT
    return KB_DIR_BACKEND


def get_or_create_collection():
    """Get or create the ChromaDB collection with default embedding function."""
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "SupportDesk Policy and Knowledge Articles"}
    )


def extract_title_and_chunks(file_path: Path) -> Tuple[str, List[Dict[str, str]]]:
    """
    Parse a Markdown file into titled sections/chunks.
    Returns (article_title, list_of_chunks).
    """
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Extract H1 Title
    title = file_path.stem.replace("_", " ").title()
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # Split by H2 headers (## Section)
    raw_sections = re.split(r"\n(?=## )", text)
    chunks = []

    for idx, section in enumerate(raw_sections):
        cleaned = section.strip()
        if not cleaned:
            continue
        
        # If this chunk is just the H1 header without body, keep it attached or skip
        sec_lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
        if len(sec_lines) == 1 and sec_lines[0].startswith("# "):
            continue

        sec_title = title
        first_line = sec_lines[0] if sec_lines else ""
        if first_line.startswith("## "):
            sec_title = f"{title} - {first_line[3:].strip()}"
        elif first_line.startswith("# "):
            sec_title = title

        chunks.append({
            "id": f"{file_path.stem}_chunk_{idx}",
            "text": cleaned,
            "title": title,
            "section_title": sec_title,
            "filename": file_path.name,
        })

    # If no section headers, add the full document as one chunk
    if not chunks and text.strip():
        chunks.append({
            "id": f"{file_path.stem}_chunk_0",
            "text": text.strip(),
            "title": title,
            "section_title": title,
            "filename": file_path.name,
        })

    return title, chunks


def index_knowledge_base(force: bool = False) -> Dict[str, Any]:
    """
    Index all Markdown documents from the knowledge_base directory into ChromaDB.
    """
    kb_dir = get_kb_directory()
    collection = get_or_create_collection()

    count = collection.count()
    if count > 0 and not force:
        return {
            "status": "already_indexed",
            "total_chunks": count,
            "directory": str(kb_dir)
        }

    # If force, reset collection
    if force and count > 0:
        chroma_client.delete_collection(COLLECTION_NAME)
        collection = get_or_create_collection()

    md_files = list(kb_dir.glob("*.md"))
    if not md_files:
        logger.warning(f"No markdown documents found in {kb_dir}")
        return {"status": "no_documents", "total_chunks": 0, "directory": str(kb_dir)}

    documents = []
    ids = []
    metadatas = []
    indexed_titles = []

    for file_path in md_files:
        title, chunks = extract_title_and_chunks(file_path)
        indexed_titles.append(title)
        for chunk in chunks:
            documents.append(chunk["text"])
            ids.append(chunk["id"])
            metadatas.append({
                "title": chunk["title"],
                "section_title": chunk["section_title"],
                "filename": chunk["filename"],
            })

    if documents:
        collection.upsert(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )

    return {
        "status": "success",
        "total_chunks": len(documents),
        "documents_indexed": list(set(indexed_titles)),
        "directory": str(kb_dir),
    }


def search_knowledge_base(query: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """
    Perform semantic vector search on indexed knowledge documents.
    """
    collection = get_or_create_collection()
    if collection.count() == 0:
        index_knowledge_base()

    try:
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, max(1, collection.count()))
        )

        matched = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

            for doc, meta, dist in zip(docs, metas, distances):
                matched.append({
                    "text": doc,
                    "title": meta.get("title", "Knowledge Base Article"),
                    "section_title": meta.get("section_title", ""),
                    "filename": meta.get("filename", ""),
                    "distance": dist,
                })
        return matched
    except Exception as e:
        logger.error(f"ChromaDB search failed: {e}")
        # Fallback to simple keyword match over files
        return keyword_fallback_search(query, n_results)


def keyword_fallback_search(query: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """Simple keyword matching fallback if vector search errors out."""
    kb_dir = get_kb_directory()
    query_lower = query.lower()
    matches = []

    for file_path in kb_dir.glob("*.md"):
        content = file_path.read_text(encoding="utf-8")
        title = file_path.stem.replace("_", " ").title()
        score = sum(1 for word in query_lower.split() if len(word) > 3 and word in content.lower())
        if score > 0:
            matches.append({
                "text": content[:600],
                "title": title,
                "section_title": title,
                "filename": file_path.name,
                "distance": 1.0 / (score + 1),
            })
    matches.sort(key=lambda x: x["distance"])
    return matches[:n_results]


def ask_assistant(question: str) -> Dict[str, Any]:
    """
    RAG Pipeline:
    1. Retrieve relevant knowledge chunks.
    2. Ground answer strictly in retrieved content.
    3. Call LLM or fallback generator.
    4. Return answer and source article titles.
    """
    q = question.strip()
    if not q:
        return {
            "answer": "Please ask a specific support question.",
            "sources": []
        }

    # 1. Retrieve knowledge chunks
    search_results = search_knowledge_base(q, n_results=3)

    if not search_results:
        return {
            "answer": "I could not find any relevant information in our support knowledge base. Please contact our support team at support@supportdesk.internal or submit a support ticket.",
            "sources": []
        }

    # Deduplicate sources
    sources = []
    context_blocks = []
    for res in search_results:
        title = res["title"]
        if title not in sources:
            sources.append(title)
        context_blocks.append(f"--- Article: {title} ---\n{res['text']}")

    context_text = "\n\n".join(context_blocks)

    # 2. Prepare LLM prompt
    system_prompt = (
        "You are the AI SupportDesk Knowledge Assistant. Your job is to answer customer questions "
        "truthfully and accurately based SOLELY on the provided support knowledge base articles.\n"
        "Guidelines:\n"
        "- Do NOT invent, assume, or hallucinate policies not present in the context.\n"
        "- If the answer is not supported by the context, politely state: 'This information is not covered in our support knowledge base. Please contact support@supportdesk.internal or submit a ticket.'\n"
        "- Be concise, professional, polite, and helpful.\n"
        "- Format with clear markdown bullet points when explaining procedures."
    )

    prompt = (
        f"KNOWLEDGE BASE CONTEXT:\n{context_text}\n\n"
        f"CUSTOMER QUESTION: {q}\n\n"
        "Please provide an accurate, grounded answer based on the context above:"
    )

    llm_answer = call_llm(prompt, system_instruction=system_prompt)
    if llm_answer and len(llm_answer.strip()) > 20:
        return {
            "answer": llm_answer.strip(),
            "sources": sources
        }

    # 3. Graceful Fallback if LLM API is unavailable/fails
    top_match = search_results[0]
    raw_lines = [l.strip() for l in top_match["text"].splitlines() if l.strip()]
    content_lines = [l for l in raw_lines if not l.startswith("#")]
    
    # Format bullets or paragraphs cleanly
    if content_lines:
        content_preview = "\n".join(content_lines[:6])
    else:
        content_preview = top_match["text"]

    fallback_answer = (
        f"Based on our **{top_match['title']}**:\n\n"
        f"{content_preview}\n\n"
        f"If you require further clarification or need agent assistance, please feel free to submit a support ticket."
    )

    return {
        "answer": fallback_answer,
        "sources": sources
    }
