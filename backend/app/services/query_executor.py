"""
Query Executor
===============
Executes whitelisted query specs against the SQLite database.
All answers are grounded in real data — no hallucination.
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Any


def _node_id(node_type: str, key: str) -> str:
    prefixes = {
        "Customer": "CUS", "SalesOrder": "SO", "Delivery": "DLV",
        "BillingDocument": "BIL", "JournalEntry": "JE", "Payment": "PAY",
        "Product": "PRD", "Plant": "PLANT",
    }
    return f"{prefixes.get(node_type, 'UNK')}:{key}"


def trace_billing_flow(db: Session, billing_id: str) -> dict:
    """Trace the full O2C flow for a billing document."""
    # Billing doc
    bil = db.execute(text(
        "SELECT * FROM billing_documents WHERE billing_id = :bid"
    ), {"bid": billing_id}).mappings().first()

    if not bil:
        return {
            "found": False,
            "answer": f"Billing document {billing_id} not found in the dataset.",
            "evidence": {},
            "highlight": {"nodes": [], "edges": []},
        }

    result = {"billing_document": dict(bil)}
    highlight_nodes = [_node_id("BillingDocument", billing_id)]
    highlight_edges = []

    # Sales Order
    if bil["order_id"]:
        so = db.execute(text(
            "SELECT * FROM sales_orders WHERE order_id = :oid"
        ), {"oid": bil["order_id"]}).mappings().first()
        if so:
            result["sales_order"] = dict(so)
            highlight_nodes.append(_node_id("SalesOrder", bil["order_id"]))
            highlight_edges.append(f"E:{_node_id('SalesOrder', bil['order_id'])}--HAS_BILLING-->{_node_id('BillingDocument', billing_id)}")

            # Customer
            if so["customer_id"]:
                cust = db.execute(text(
                    "SELECT * FROM customers WHERE customer_id = :cid"
                ), {"cid": so["customer_id"]}).mappings().first()
                if cust:
                    result["customer"] = dict(cust)
                    highlight_nodes.append(_node_id("Customer", so["customer_id"]))

    # Delivery
    if bil["delivery_id"]:
        dlv = db.execute(text(
            "SELECT * FROM deliveries WHERE delivery_id = :did"
        ), {"did": bil["delivery_id"]}).mappings().first()
        if dlv:
            result["delivery"] = dict(dlv)
            highlight_nodes.append(_node_id("Delivery", bil["delivery_id"]))
            highlight_edges.append(f"E:{_node_id('Delivery', bil['delivery_id'])}--BILLED_VIA-->{_node_id('BillingDocument', billing_id)}")

    # Journal Entry
    je = db.execute(text(
        "SELECT * FROM journal_entries WHERE billing_id = :bid LIMIT 1"
    ), {"bid": billing_id}).mappings().first()
    if je:
        result["journal_entry"] = dict(je)
        highlight_nodes.append(_node_id("JournalEntry", je["entry_id"]))
        highlight_edges.append(f"E:{_node_id('BillingDocument', billing_id)}--CREATES_JOURNAL_ENTRY-->{_node_id('JournalEntry', je['entry_id'])}")

    # Payment
    pay = db.execute(text(
        "SELECT * FROM payments WHERE billing_id = :bid LIMIT 1"
    ), {"bid": billing_id}).mappings().first()
    if pay:
        result["payment"] = dict(pay)
        highlight_nodes.append(_node_id("Payment", pay["payment_id"]))

    # Products in billing items
    products = db.execute(text(
        "SELECT bi.*, p.description FROM billing_items bi "
        "LEFT JOIN products p ON bi.product_id = p.product_id "
        "WHERE bi.billing_id = :bid"
    ), {"bid": billing_id}).mappings().fetchall()
    if products:
        result["products"] = [dict(p) for p in products]

    # Build narrative answer
    lines = [f"**Billing Document {billing_id}**"]
    lines.append(f"- Date: {bil['billing_date']} | Amount: {bil['net_value']} {bil['currency']} | Status: {bil['status']}")
    if bil.get("cancelled"):
        lines.append("- ⚠️ This billing document has been **cancelled**.")
    if "customer" in result:
        c = result["customer"]
        lines.append(f"- Customer: {c['name']} ({c['customer_id']}) from {c['country']}")
    if "sales_order" in result:
        so = result["sales_order"]
        lines.append(f"- Sales Order: {so['order_id']} | Date: {so['order_date']} | Net: {so['net_value']} {so['currency']}")
    if "delivery" in result:
        d = result["delivery"]
        lines.append(f"- Delivery: {d['delivery_id']} | Date: {d['delivery_date']} | Status: {d['status']}")
    else:
        lines.append("- ⚠️ No delivery found for this billing document.")
    if "journal_entry" in result:
        je = result["journal_entry"]
        lines.append(f"- Journal Entry: {je['entry_id']} | Posted: {je['posting_date']} | Amount: {je['amount']} {je['currency']}")
    else:
        lines.append("- ⚠️ No journal entry found for this billing document.")
    if "payment" in result:
        p = result["payment"]
        lines.append(f"- Payment: {p['payment_id']} | Date: {p['payment_date']} | Amount: {p['amount']} {p['currency']}")
    else:
        lines.append("- ⚠️ No payment recorded for this billing document (open receivable).")

    return {
        "found": True,
        "answer": "\n".join(lines),
        "evidence": result,
        "highlight": {"nodes": highlight_nodes, "edges": highlight_edges},
    }


def lookup_journal_entry_for_billing(db: Session, billing_id: str) -> dict:
    rows = db.execute(text(
        "SELECT * FROM journal_entries WHERE billing_id = :bid"
    ), {"bid": billing_id}).mappings().fetchall()

    if not rows:
        return {
            "found": False,
            "answer": f"No journal entries found for billing document {billing_id}.",
            "evidence": {},
            "highlight": {"nodes": [_node_id("BillingDocument", billing_id)], "edges": []},
        }

    entries = [dict(r) for r in rows]
    lines = [f"**Journal Entries for Billing Document {billing_id}**"]
    for e in entries:
        lines.append(f"- Entry: {e['entry_id']} | Posted: {e['posting_date']} | Amount: {e['amount']} {e['currency']} | Account: {e['account']}")

    return {
        "found": True,
        "answer": "\n".join(lines),
        "evidence": {"journal_entries": entries},
        "highlight": {
            "nodes": [_node_id("BillingDocument", billing_id)] + [_node_id("JournalEntry", e["entry_id"]) for e in entries],
            "edges": [],
        },
    }


def top_products_by_billing_count(db: Session, limit: int = 10) -> dict:
    rows = db.execute(text("""
        SELECT bi.product_id, p.description,
               COUNT(DISTINCT bi.billing_id) AS billing_count,
               SUM(bi.net_value) AS total_value
        FROM billing_items bi
        LEFT JOIN products p ON bi.product_id = p.product_id
        WHERE bi.product_id != ''
        GROUP BY bi.product_id
        ORDER BY billing_count DESC
        LIMIT :lim
    """), {"lim": limit}).fetchall()

    if not rows:
        return {"found": False, "answer": "No billing item data found.", "evidence": {}, "highlight": {"nodes": [], "edges": []}}

    data = [{"product_id": r[0], "description": r[1], "billing_count": r[2], "total_value": r[3]} for r in rows]
    lines = [f"**Top {limit} Products by Billing Document Count**"]
    for i, d in enumerate(data, 1):
        lines.append(f"{i}. {d['description'] or d['product_id']} ({d['product_id']}) — {d['billing_count']} billing docs, total value: {d['total_value']:.2f}")

    return {
        "found": True,
        "answer": "\n".join(lines),
        "evidence": {"products": data},
        "highlight": {"nodes": [_node_id("Product", d["product_id"]) for d in data], "edges": []},
    }


def top_customers_by_billing_value(db: Session, limit: int = 10) -> dict:
    rows = db.execute(text("""
        SELECT bd.customer_id, c.name,
               COUNT(bd.billing_id) AS billing_count,
               SUM(bd.net_value) AS total_value,
               bd.currency
        FROM billing_documents bd
        LEFT JOIN customers c ON bd.customer_id = c.customer_id
        WHERE bd.customer_id != '' AND bd.cancelled = 0
        GROUP BY bd.customer_id
        ORDER BY total_value DESC
        LIMIT :lim
    """), {"lim": limit}).fetchall()

    if not rows:
        return {"found": False, "answer": "No billing data found.", "evidence": {}, "highlight": {"nodes": [], "edges": []}}

    data = [{"customer_id": r[0], "name": r[1], "billing_count": r[2], "total_value": r[3], "currency": r[4]} for r in rows]
    lines = [f"**Top {limit} Customers by Billing Volume**"]
    for i, d in enumerate(data, 1):
        lines.append(f"{i}. {d['name'] or d['customer_id']} ({d['customer_id']}) — {d['billing_count']} bills, total: {d['total_value']:.2f} {d['currency']}")

    return {
        "found": True,
        "answer": "\n".join(lines),
        "evidence": {"customers": data},
        "highlight": {"nodes": [_node_id("Customer", d["customer_id"]) for d in data], "edges": []},
    }


def delivered_not_billed(db: Session) -> dict:
    rows = db.execute(text("""
        SELECT d.delivery_id, d.order_id, d.delivery_date, d.status
        FROM deliveries d
        LEFT JOIN billing_documents bd ON d.delivery_id = bd.delivery_id
        WHERE bd.billing_id IS NULL
        LIMIT 100
    """)).fetchall()

    if not rows:
        return {
            "found": True,
            "answer": "All deliveries have corresponding billing documents. No gaps found.",
            "evidence": {},
            "highlight": {"nodes": [], "edges": []},
        }

    data = [{"delivery_id": r[0], "order_id": r[1], "delivery_date": r[2], "status": r[3]} for r in rows]
    lines = [f"**Deliveries Without Billing Documents ({len(data)} found)**"]
    for d in data[:20]:
        lines.append(f"- Delivery {d['delivery_id']} (Order: {d['order_id']}, Date: {d['delivery_date']}, Status: {d['status']})")
    if len(data) > 20:
        lines.append(f"... and {len(data) - 20} more.")

    return {
        "found": True,
        "answer": "\n".join(lines),
        "evidence": {"deliveries": data},
        "highlight": {"nodes": [_node_id("Delivery", d["delivery_id"]) for d in data[:20]], "edges": []},
    }


def billed_without_delivery(db: Session) -> dict:
    rows = db.execute(text("""
        SELECT bd.billing_id, bd.order_id, bd.billing_date, bd.net_value, bd.currency
        FROM billing_documents bd
        WHERE (bd.delivery_id IS NULL OR bd.delivery_id = '')
          AND bd.cancelled = 0
        LIMIT 100
    """)).fetchall()

    if not rows:
        return {
            "found": True,
            "answer": "All billing documents have associated delivery references.",
            "evidence": {},
            "highlight": {"nodes": [], "edges": []},
        }

    data = [{"billing_id": r[0], "order_id": r[1], "billing_date": r[2], "net_value": r[3], "currency": r[4]} for r in rows]
    lines = [f"**Billing Documents Without Delivery ({len(data)} found)**"]
    for d in data[:20]:
        lines.append(f"- Billing {d['billing_id']} (Order: {d['order_id']}, Date: {d['billing_date']}, Value: {d['net_value']} {d['currency']})")

    return {
        "found": True,
        "answer": "\n".join(lines),
        "evidence": {"billing_documents": data},
        "highlight": {"nodes": [_node_id("BillingDocument", d["billing_id"]) for d in data[:20]], "edges": []},
    }


def open_receivables_without_payment(db: Session) -> dict:
    rows = db.execute(text("""
        SELECT je.entry_id, je.billing_id, je.customer_id, je.posting_date, je.amount, je.currency
        FROM journal_entries je
        LEFT JOIN payments p ON je.entry_id = p.journal_entry_id
        WHERE p.payment_id IS NULL
        LIMIT 100
    """)).fetchall()

    if not rows:
        return {
            "found": True,
            "answer": "All journal entries have corresponding payments. No open receivables found.",
            "evidence": {},
            "highlight": {"nodes": [], "edges": []},
        }

    data = [{"entry_id": r[0], "billing_id": r[1], "customer_id": r[2], "posting_date": r[3], "amount": r[4], "currency": r[5]} for r in rows]
    total = sum(d["amount"] or 0 for d in data)
    lines = [f"**Open Receivables Without Payment ({len(data)} entries, total: {total:.2f})**"]
    for d in data[:20]:
        lines.append(f"- JE {d['entry_id']} | Billing: {d['billing_id']} | Customer: {d['customer_id']} | Amount: {d['amount']} {d['currency']} | Posted: {d['posting_date']}")

    return {
        "found": True,
        "answer": "\n".join(lines),
        "evidence": {"open_receivables": data},
        "highlight": {"nodes": [_node_id("JournalEntry", d["entry_id"]) for d in data[:20]], "edges": []},
    }


def cancelled_billing_documents(db: Session) -> dict:
    rows = db.execute(text("""
        SELECT bd.billing_id, bd.customer_id, bd.billing_date, bd.net_value, bd.currency,
               bc.cancellation_id, bc.cancel_date, bc.reason
        FROM billing_documents bd
        JOIN billing_cancellations bc ON bd.billing_id = bc.original_billing_id
        LIMIT 100
    """)).fetchall()

    if not rows:
        # Also try the cancelled flag
        rows = db.execute(text("""
            SELECT billing_id, customer_id, billing_date, net_value, currency,
                   NULL, NULL, NULL
            FROM billing_documents WHERE cancelled = 1 LIMIT 100
        """)).fetchall()

    if not rows:
        return {
            "found": True,
            "answer": "No cancelled billing documents found in the dataset.",
            "evidence": {},
            "highlight": {"nodes": [], "edges": []},
        }

    data = [{"billing_id": r[0], "customer_id": r[1], "billing_date": r[2],
             "net_value": r[3], "currency": r[4], "cancellation_id": r[5],
             "cancel_date": r[6], "reason": r[7]} for r in rows]
    lines = [f"**Cancelled Billing Documents ({len(data)} found)**"]
    for d in data[:20]:
        lines.append(f"- Billing {d['billing_id']} | Customer: {d['customer_id']} | Date: {d['billing_date']} | Value: {d['net_value']} {d['currency']}")
        if d.get("cancel_date"):
            lines.append(f"  Cancelled on: {d['cancel_date']} (Ref: {d['cancellation_id']})")

    return {
        "found": True,
        "answer": "\n".join(lines),
        "evidence": {"cancelled": data},
        "highlight": {"nodes": [_node_id("BillingDocument", d["billing_id"]) for d in data[:20]], "edges": []},
    }


def entity_neighbors(db: Session, node_id: str) -> dict:
    outgoing = db.execute(text("""
        SELECT ge.target_id, ge.edge_type, gn.node_type, gn.label
        FROM graph_edges ge
        JOIN graph_nodes gn ON ge.target_id = gn.node_id
        WHERE ge.source_id = :nid
    """), {"nid": node_id}).fetchall()

    incoming = db.execute(text("""
        SELECT ge.source_id, ge.edge_type, gn.node_type, gn.label
        FROM graph_edges ge
        JOIN graph_nodes gn ON ge.source_id = gn.node_id
        WHERE ge.target_id = :nid
    """), {"nid": node_id}).fetchall()

    node = db.execute(text(
        "SELECT * FROM graph_nodes WHERE node_id = :nid"
    ), {"nid": node_id}).mappings().first()

    if not node:
        return {"found": False, "answer": f"Node {node_id} not found.", "evidence": {}, "highlight": {"nodes": [], "edges": []}}

    lines = [f"**Neighbors of {node['label']} ({node_id})**"]
    out_data = [{"id": r[0], "edge": r[1], "type": r[2], "label": r[3]} for r in outgoing]
    in_data = [{"id": r[0], "edge": r[1], "type": r[2], "label": r[3]} for r in incoming]

    if out_data:
        lines.append(f"\nOutgoing ({len(out_data)}):")
        for d in out_data[:10]:
            lines.append(f"  → [{d['edge']}] {d['label']} ({d['id']})")
    if in_data:
        lines.append(f"\nIncoming ({len(in_data)}):")
        for d in in_data[:10]:
            lines.append(f"  ← [{d['edge']}] {d['label']} ({d['id']})")

    all_nodes = [node_id] + [d["id"] for d in out_data + in_data]

    return {
        "found": True,
        "answer": "\n".join(lines),
        "evidence": {"node": dict(node), "outgoing": out_data, "incoming": in_data},
        "highlight": {"nodes": all_nodes[:50], "edges": []},
    }


def lookup_document(db: Session, entity_type: str, entity_id: str) -> dict:
    table_map = {
        "Customer": ("customers", "customer_id"),
        "SalesOrder": ("sales_orders", "order_id"),
        "Delivery": ("deliveries", "delivery_id"),
        "BillingDocument": ("billing_documents", "billing_id"),
        "JournalEntry": ("journal_entries", "entry_id"),
        "Payment": ("payments", "payment_id"),
        "Product": ("products", "product_id"),
        "Plant": ("plants", "plant_id"),
    }

    if entity_type not in table_map:
        return {"found": False, "answer": f"Unknown entity type: {entity_type}", "evidence": {}, "highlight": {"nodes": [], "edges": []}}

    table, id_col = table_map[entity_type]
    row = db.execute(text(f"SELECT * FROM {table} WHERE {id_col} = :eid"), {"eid": entity_id}).mappings().first()

    if not row:
        return {"found": False, "answer": f"{entity_type} with ID {entity_id} not found.", "evidence": {}, "highlight": {"nodes": [], "edges": []}}

    data = dict(row)
    data.pop("raw_json", None)
    lines = [f"**{entity_type}: {entity_id}**"]
    for k, v in data.items():
        if v not in (None, ""):
            lines.append(f"- {k}: {v}")

    nid = _node_id(entity_type, entity_id)
    return {
        "found": True,
        "answer": "\n".join(lines),
        "evidence": {entity_type.lower(): data},
        "highlight": {"nodes": [nid], "edges": []},
    }


def execute_query(db: Session, spec: dict) -> dict:
    """Main dispatcher for query execution."""
    action = spec.get("action")

    if action == "reject":
        return {
            "found": False,
            "answer": "This system is designed to answer questions related to the provided Order-to-Cash dataset only.",
            "evidence": {},
            "highlight": {"nodes": [], "edges": []},
        }

    dispatch = {
        "trace_billing_flow": lambda: trace_billing_flow(db, spec["billing_document"]),
        "lookup_journal_entry_for_billing": lambda: lookup_journal_entry_for_billing(db, spec["billing_document"]),
        "top_products_by_billing_count": lambda: top_products_by_billing_count(db, spec.get("limit", 10)),
        "top_customers_by_billing_value": lambda: top_customers_by_billing_value(db, spec.get("limit", 10)),
        "delivered_not_billed": lambda: delivered_not_billed(db),
        "billed_without_delivery": lambda: billed_without_delivery(db),
        "open_receivables_without_payment": lambda: open_receivables_without_payment(db),
        "cancelled_billing_documents": lambda: cancelled_billing_documents(db),
        "entity_neighbors": lambda: entity_neighbors(db, spec["node_id"]),
        "lookup_document": lambda: lookup_document(db, spec["entity_type"], spec["entity_id"]),
    }

    handler = dispatch.get(action)
    if not handler:
        return {
            "found": False,
            "answer": f"Unknown action: {action}",
            "evidence": {},
            "highlight": {"nodes": [], "edges": []},
        }

    try:
        return handler()
    except Exception as e:
        return {
            "found": False,
            "answer": f"Query execution error: {str(e)}",
            "evidence": {},
            "highlight": {"nodes": [], "edges": []},
        }
