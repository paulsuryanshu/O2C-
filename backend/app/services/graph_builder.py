"""
Graph Builder Service
======================
Projects normalized relational data into graph_nodes and graph_edges tables.
Follows the O2C flow:
  Customer → SalesOrder → Delivery → BillingDocument → JournalEntry → Payment
Plus secondary links: Orders/Billing → Product, Delivery → Plant
"""
import json
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import text


def _node_id(node_type: str, key: str) -> str:
    prefixes = {
        "Customer": "CUS",
        "SalesOrder": "SO",
        "Delivery": "DLV",
        "BillingDocument": "BIL",
        "JournalEntry": "JE",
        "Payment": "PAY",
        "Product": "PRD",
        "Plant": "PLANT",
        "SalesOrderItem": "SOI",
        "DeliveryItem": "DLVI",
        "BillingItem": "BILI",
        "Address": "ADDR",
    }
    prefix = prefixes.get(node_type, node_type[:3].upper())
    return f"{prefix}:{key}"


def _edge_id(source: str, target: str, edge_type: str) -> str:
    return f"E:{source}--{edge_type}-->{target}"


def _upsert_node(db: Session, node_id: str, node_type: str, label: str, entity_key: str, metadata: dict):
    db.execute(text("""
        INSERT OR REPLACE INTO graph_nodes (node_id, node_type, label, entity_key, metadata_json)
        VALUES (:nid, :ntype, :label, :ekey, :meta)
    """), {
        "nid": node_id,
        "ntype": node_type,
        "label": label,
        "ekey": entity_key,
        "meta": json.dumps(metadata),
    })


def _upsert_edge(db: Session, source: str, target: str, edge_type: str, metadata: dict = None):
    eid = _edge_id(source, target, edge_type)
    db.execute(text("""
        INSERT OR REPLACE INTO graph_edges (edge_id, source_id, target_id, edge_type, metadata_json)
        VALUES (:eid, :src, :tgt, :etype, :meta)
    """), {
        "eid": eid,
        "src": source,
        "tgt": target,
        "etype": edge_type,
        "meta": json.dumps(metadata or {}),
    })


def build_customer_nodes(db: Session):
    rows = db.execute(text("SELECT customer_id, name, country, city FROM customers")).fetchall()
    for r in rows:
        nid = _node_id("Customer", r[0])
        _upsert_node(db, nid, "Customer", r[1] or r[0],
                     r[0], {"id": r[0], "name": r[1], "country": r[2], "city": r[3]})


def build_sales_order_nodes(db: Session):
    rows = db.execute(text(
        "SELECT order_id, customer_id, order_date, net_value, currency, status FROM sales_orders"
    )).fetchall()
    for r in rows:
        nid = _node_id("SalesOrder", r[0])
        _upsert_node(db, nid, "SalesOrder", f"SO {r[0]}",
                     r[0], {"id": r[0], "customer_id": r[1], "date": r[2],
                            "net_value": r[3], "currency": r[4], "status": r[5]})
        # Edge: Customer → SalesOrder
        if r[1]:
            cus_nid = _node_id("Customer", r[1])
            _upsert_edge(db, cus_nid, nid, "PLACED_ORDER")


def build_delivery_nodes(db: Session):
    rows = db.execute(text(
        "SELECT delivery_id, order_id, plant_id, delivery_date, status FROM deliveries"
    )).fetchall()
    for r in rows:
        nid = _node_id("Delivery", r[0])
        _upsert_node(db, nid, "Delivery", f"DLV {r[0]}",
                     r[0], {"id": r[0], "order_id": r[1], "plant_id": r[2],
                            "delivery_date": r[3], "status": r[4]})
        # Edge: SalesOrder → Delivery
        if r[1]:
            so_nid = _node_id("SalesOrder", r[1])
            _upsert_edge(db, so_nid, nid, "HAS_DELIVERY")
        # Edge: Delivery → Plant
        if r[2]:
            plant_nid = _node_id("Plant", r[2])
            _upsert_edge(db, nid, plant_nid, "SHIPS_FROM")


def build_billing_nodes(db: Session):
    rows = db.execute(text("""
        SELECT billing_id, order_id, delivery_id, customer_id,
               billing_date, net_value, currency, status, cancelled
        FROM billing_documents
    """)).fetchall()
    for r in rows:
        nid = _node_id("BillingDocument", r[0])
        _upsert_node(db, nid, "BillingDocument", f"BIL {r[0]}",
                     r[0], {"id": r[0], "order_id": r[1], "delivery_id": r[2],
                            "customer_id": r[3], "date": r[4], "net_value": r[5],
                            "currency": r[6], "status": r[7], "cancelled": bool(r[8])})
        # Edge: SalesOrder → BillingDocument
        if r[1]:
            so_nid = _node_id("SalesOrder", r[1])
            _upsert_edge(db, so_nid, nid, "HAS_BILLING")
        # Edge: Delivery → BillingDocument
        if r[2]:
            dlv_nid = _node_id("Delivery", r[2])
            _upsert_edge(db, dlv_nid, nid, "BILLED_VIA")
        # Edge: Customer → BillingDocument (direct for billing without clear SO)
        if r[3] and not r[1]:
            cus_nid = _node_id("Customer", r[3])
            _upsert_edge(db, cus_nid, nid, "BILLED_TO")


def build_journal_entry_nodes(db: Session):
    rows = db.execute(text(
        "SELECT entry_id, billing_id, customer_id, posting_date, amount, currency FROM journal_entries"
    )).fetchall()
    for r in rows:
        nid = _node_id("JournalEntry", r[0])
        _upsert_node(db, nid, "JournalEntry", f"JE {r[0]}",
                     r[0], {"id": r[0], "billing_id": r[1], "customer_id": r[2],
                            "posting_date": r[3], "amount": r[4], "currency": r[5]})
        # Edge: BillingDocument → JournalEntry
        if r[1]:
            bil_nid = _node_id("BillingDocument", r[1])
            _upsert_edge(db, bil_nid, nid, "CREATES_JOURNAL_ENTRY")


def build_payment_nodes(db: Session):
    rows = db.execute(text(
        "SELECT payment_id, customer_id, billing_id, journal_entry_id, payment_date, amount, currency FROM payments"
    )).fetchall()
    for r in rows:
        nid = _node_id("Payment", r[0])
        _upsert_node(db, nid, "Payment", f"PAY {r[0]}",
                     r[0], {"id": r[0], "customer_id": r[1], "billing_id": r[2],
                            "journal_entry_id": r[3], "payment_date": r[4],
                            "amount": r[5], "currency": r[6]})
        # Edge: JournalEntry → Payment
        if r[3]:
            je_nid = _node_id("JournalEntry", r[3])
            _upsert_edge(db, je_nid, nid, "CLEARED_BY")
        elif r[2]:
            # Fallback: BillingDocument → Payment if no JE
            bil_nid = _node_id("BillingDocument", r[2])
            _upsert_edge(db, bil_nid, nid, "PAID_BY")


def build_product_nodes(db: Session):
    rows = db.execute(text("SELECT product_id, description FROM products")).fetchall()
    for r in rows:
        nid = _node_id("Product", r[0])
        _upsert_node(db, nid, "Product", r[1] or r[0],
                     r[0], {"id": r[0], "description": r[1]})

    # Product links from billing items
    bi_rows = db.execute(text(
        "SELECT DISTINCT billing_id, product_id FROM billing_items WHERE product_id != ''"
    )).fetchall()
    for r in bi_rows:
        bil_nid = _node_id("BillingDocument", r[0])
        prd_nid = _node_id("Product", r[1])
        _upsert_edge(db, bil_nid, prd_nid, "INCLUDES_PRODUCT")

    # Product links from delivery items
    di_rows = db.execute(text(
        "SELECT DISTINCT delivery_id, product_id FROM delivery_items WHERE product_id != ''"
    )).fetchall()
    for r in di_rows:
        dlv_nid = _node_id("Delivery", r[0])
        prd_nid = _node_id("Product", r[1])
        _upsert_edge(db, dlv_nid, prd_nid, "DELIVERS_PRODUCT")


def build_plant_nodes(db: Session):
    rows = db.execute(text("SELECT plant_id, name, country, city FROM plants")).fetchall()
    for r in rows:
        nid = _node_id("Plant", r[0])
        _upsert_node(db, nid, "Plant", r[1] or r[0],
                     r[0], {"id": r[0], "name": r[1], "country": r[2], "city": r[3]})


def run_graph_build(db: Session) -> dict:
    """Clear existing graph and rebuild from relational tables."""
    db.execute(text("DELETE FROM graph_nodes"))
    db.execute(text("DELETE FROM graph_edges"))
    db.commit()

    build_customer_nodes(db)
    build_plant_nodes(db)
    build_product_nodes(db)
    build_sales_order_nodes(db)
    build_delivery_nodes(db)
    build_billing_nodes(db)
    build_journal_entry_nodes(db)
    build_payment_nodes(db)
    db.commit()

    node_count = db.execute(text("SELECT COUNT(*) FROM graph_nodes")).scalar()
    edge_count = db.execute(text("SELECT COUNT(*) FROM graph_edges")).scalar()
    return {"nodes": node_count, "edges": edge_count}
