"""
CLI script to run ingestion + graph build.
Usage: python -m scripts.ingest
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.database import init_db, SessionLocal
from app.services.ingestion import run_full_ingestion
from app.services.graph_builder import run_graph_build


def main():
    print("[INIT] Initializing database schema...")
    init_db()
    db = SessionLocal()
    try:
        print("[INGEST] Loading JSON data...")
        counts = run_full_ingestion(db)
        for table, count in counts.items():
            print(f"  {table}: {count} records")

        print("[GRAPH] Building graph projection...")
        graph = run_graph_build(db)
        print(f"  Nodes: {graph['nodes']}")
        print(f"  Edges: {graph['edges']}")
        print("[DONE] Ingestion complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
