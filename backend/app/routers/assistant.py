from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status

from app.schemas.ticket import AssistantAskRequest, AssistantAskResponse
from app.services.rag_service import ask_assistant, index_knowledge_base, get_kb_directory

router = APIRouter(prefix="/api/assistant", tags=["Knowledge Assistant"])


@router.post("/ask", response_model=AssistantAskResponse)
def query_knowledge_assistant(req: AssistantAskRequest):
    """
    RAG-powered Knowledge Assistant:
    Retrieves policy context from ChromaDB and returns a grounded answer with sources.
    """
    question = req.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty."
        )

    try:
        result = ask_assistant(question)
        return AssistantAskResponse(
            answer=result.get("answer", "No answer found."),
            sources=result.get("sources", []),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge assistant error: {str(e)}"
        )


@router.post("/index")
def trigger_index(force: bool = True):
    """Re-index all documents in the knowledge base."""
    try:
        result = index_knowledge_base(force=force)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {str(e)}"
        )


@router.get("/documents")
def get_documents_list():
    """List all available support articles in the knowledge base."""
    kb_dir = get_kb_directory()
    docs = []
    if kb_dir.exists():
        for f in sorted(kb_dir.glob("*.md")):
            # Extract first heading
            title = f.stem.replace("_", " ").title()
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            docs.append({
                "filename": f.name,
                "title": title
            })
    return {"count": len(docs), "documents": docs}
