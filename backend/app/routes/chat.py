"""Chat endpoint - natural language query to grounded SQL answer."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.guardrails import is_in_domain, validate_query_spec
from app.services.llm_planner import plan_query
from app.services.query_executor import execute_query

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Convert natural language to query spec, validate, execute, return grounded answer."""
    message = request.message.strip()

    if not message:
        return {
            "answer": "Please enter a question.",
            "evidence": {},
            "highlight": {"nodes": [], "edges": []},
            "query_spec": None,
        }

    # Domain check
    if not is_in_domain(message):
        return {
            "answer": "This system is designed to answer questions related to the provided Order-to-Cash dataset only.",
            "evidence": {},
            "highlight": {"nodes": [], "edges": []},
            "query_spec": {"action": "reject", "reason": "out_of_domain"},
        }

    # LLM planning
    spec = await plan_query(message)

    # Validate spec
    is_valid, error = validate_query_spec(spec)
    if not is_valid:
        return {
            "answer": f"Query planning failed: {error}",
            "evidence": {},
            "highlight": {"nodes": [], "edges": []},
            "query_spec": spec,
        }

    # Execute
    result = execute_query(db, spec)

    return {
        "answer": result.get("answer", "No result."),
        "evidence": result.get("evidence", {}),
        "highlight": result.get("highlight", {"nodes": [], "edges": []}),
        "query_spec": spec,
    }
