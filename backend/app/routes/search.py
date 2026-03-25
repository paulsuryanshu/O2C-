"""Search endpoint - fuzzy search across documents, customers, products."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db

router = APIRouter()


@router.get("")
def search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """Search across customers, billing documents, sales orders, products."""
    like = f"%{q}%"
    results = []

    # Customers
    rows = db.execute(text("""
        SELECT customer_id, name, country, city FROM customers
        WHERE customer_id LIKE :q OR name LIKE :q
        LIMIT 10
    """), {"q": like}).fetchall()
    for r in rows:
        results.append({"type": "Customer", "id": r[0], "label": r[1] or r[0],
                        "node_id": f"CUS:{r[0]}", "meta": {"country": r[2], "city": r[3]}})

    # Billing Documents
    rows = db.execute(text("""
        SELECT billing_id, customer_id, billing_date, net_value, currency FROM billing_documents
        WHERE billing_id LIKE :q
        LIMIT 10
    """), {"q": like}).fetchall()
    for r in rows:
        results.append({"type": "BillingDocument", "id": r[0], "label": f"BIL {r[0]}",
                        "node_id": f"BIL:{r[0]}", "meta": {"customer": r[1], "date": r[2], "value": r[3]}})

    # Sales Orders
    rows = db.execute(text("""
        SELECT order_id, customer_id, order_date, net_value FROM sales_orders
        WHERE order_id LIKE :q
        LIMIT 10
    """), {"q": like}).fetchall()
    for r in rows:
        results.append({"type": "SalesOrder", "id": r[0], "label": f"SO {r[0]}",
                        "node_id": f"SO:{r[0]}", "meta": {"customer": r[1], "date": r[2], "value": r[3]}})

    # Products
    rows = db.execute(text("""
        SELECT product_id, description FROM products
        WHERE product_id LIKE :q OR description LIKE :q
        LIMIT 10
    """), {"q": like}).fetchall()
    for r in rows:
        results.append({"type": "Product", "id": r[0], "label": r[1] or r[0],
                        "node_id": f"PRD:{r[0]}", "meta": {}})

    return {"query": q, "results": results, "count": len(results)}
