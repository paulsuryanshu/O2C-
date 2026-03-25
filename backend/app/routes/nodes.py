"""Node detail endpoints."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db

router = APIRouter()


@router.get("/{node_id:path}")
def get_node(node_id: str, db: Session = Depends(get_db)):
    """Return full metadata for a node and its immediate neighbors."""
    node = db.execute(text(
        "SELECT node_id, node_type, label, entity_key, metadata_json FROM graph_nodes WHERE node_id = :nid"
    ), {"nid": node_id}).mappings().first()

    if not node:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

    def parse_meta(m):
        try:
            return json.loads(m) if m else {}
        except Exception:
            return {}

    # Get neighbors
    out_edges = db.execute(text("""
        SELECT e.edge_id, e.target_id, e.edge_type, n.label, n.node_type
        FROM graph_edges e
        JOIN graph_nodes n ON e.target_id = n.node_id
        WHERE e.source_id = :nid
    """), {"nid": node_id}).fetchall()

    in_edges = db.execute(text("""
        SELECT e.edge_id, e.source_id, e.edge_type, n.label, n.node_type
        FROM graph_edges e
        JOIN graph_nodes n ON e.source_id = n.node_id
        WHERE e.target_id = :nid
    """), {"nid": node_id}).fetchall()

    return {
        "node_id": node["node_id"],
        "node_type": node["node_type"],
        "label": node["label"],
        "entity_key": node["entity_key"],
        "metadata": parse_meta(node["metadata_json"]),
        "outgoing": [
            {"edge_id": r[0], "target_id": r[1], "edge_type": r[2], "label": r[3], "type": r[4]}
            for r in out_edges
        ],
        "incoming": [
            {"edge_id": r[0], "source_id": r[1], "edge_type": r[2], "label": r[3], "type": r[4]}
            for r in in_edges
        ],
    }
