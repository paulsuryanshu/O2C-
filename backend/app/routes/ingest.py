"""Ingestion endpoint - trigger data load and graph build."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.ingestion import run_full_ingestion
from app.services.graph_builder import run_graph_build

router = APIRouter()


@router.post("/run")
def run_ingestion(db: Session = Depends(get_db)):
    """Load all JSON data and rebuild the graph projection."""
    ingestion_counts = run_full_ingestion(db)
    graph_counts = run_graph_build(db)
    return {
        "status": "success",
        "ingestion": ingestion_counts,
        "graph": graph_counts,
    }


@router.post("/graph-only")
def rebuild_graph(db: Session = Depends(get_db)):
    """Rebuild graph projection only (after ingestion already done)."""
    graph_counts = run_graph_build(db)
    return {"status": "success", "graph": graph_counts}
