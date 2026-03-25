"""Graph endpoints - returns nodes and edges for visualization."""
import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db

router = APIRouter()


@router.get("")
def get_graph(
    node_type: str = Query(None, description="Filter by node type"),
    focal: str = Query(None, description="Return subgraph around this node_id"),
    limit: int = Query(500, le=2000),
    db: Session = Depends(get_db),
):
    """Return graph nodes and edges, optionally filtered."""
    if focal:
        # Return 2-hop neighborhood
        node_ids_query = db.execute(text("""
            SELECT DISTINCT node_id FROM graph_nodes WHERE node_id = :nid
            UNION
            SELECT target_id FROM graph_edges WHERE source_id = :nid
            UNION
            SELECT source_id FROM graph_edges WHERE target_id = :nid
        """), {"nid": focal}).fetchall()
        node_ids = [r[0] for r in node_ids_query]
        placeholders = ",".join([f"'{nid}'" for nid in node_ids])

        if not node_ids:
            return {"nodes": [], "edges": []}

        nodes = db.execute(text(
            f"SELECT node_id, node_type, label, entity_key, metadata_json FROM graph_nodes WHERE node_id IN ({placeholders})"
        )).mappings().fetchall()

        edges = db.execute(text(
            f"SELECT edge_id, source_id, target_id, edge_type, metadata_json FROM graph_edges WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})"
        )).mappings().fetchall()
    elif node_type:
        nodes = db.execute(text(
            "SELECT node_id, node_type, label, entity_key, metadata_json FROM graph_nodes WHERE node_type = :nt LIMIT :lim"
        ), {"nt": node_type, "lim": limit}).mappings().fetchall()
        node_ids = [n["node_id"] for n in nodes]
        placeholders = ",".join([f"'{nid}'" for nid in node_ids]) if node_ids else "''"
        edges = db.execute(text(
            f"SELECT edge_id, source_id, target_id, edge_type, metadata_json FROM graph_edges WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})"
        )).mappings().fetchall()
    else:
        nodes = db.execute(text(
            "SELECT node_id, node_type, label, entity_key, metadata_json FROM graph_nodes LIMIT :lim"
        ), {"lim": limit}).mappings().fetchall()
        edges = db.execute(text(
            "SELECT edge_id, source_id, target_id, edge_type, metadata_json FROM graph_edges LIMIT :lim"
        ), {"lim": limit * 3}).mappings().fetchall()

    def parse_meta(m):
        try:
            return json.loads(m) if m else {}
        except Exception:
            return {}

    return {
        "nodes": [
            {
                "id": n["node_id"],
                "type": n["node_type"],
                "label": n["label"],
                "entity_key": n["entity_key"],
                "data": parse_meta(n["metadata_json"]),
            }
            for n in nodes
        ],
        "edges": [
            {
                "id": e["edge_id"],
                "source": e["source_id"],
                "target": e["target_id"],
                "type": e["edge_type"],
                "data": parse_meta(e["metadata_json"]),
            }
            for e in edges
        ],
    }


@router.get("/stats")
def get_graph_stats(db: Session = Depends(get_db)):
    """Return graph statistics."""
    node_counts = db.execute(text(
        "SELECT node_type, COUNT(*) as cnt FROM graph_nodes GROUP BY node_type ORDER BY cnt DESC"
    )).fetchall()
    edge_counts = db.execute(text(
        "SELECT edge_type, COUNT(*) as cnt FROM graph_edges GROUP BY edge_type ORDER BY cnt DESC"
    )).fetchall()
    return {
        "node_types": {r[0]: r[1] for r in node_counts},
        "edge_types": {r[0]: r[1] for r in edge_counts},
        "total_nodes": sum(r[1] for r in node_counts),
        "total_edges": sum(r[1] for r in edge_counts),
    }
