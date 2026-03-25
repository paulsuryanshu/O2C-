"""
Ingestion Service
=================
Loads SAP-style JSON files from DATA_DIR, normalizes them,
and inserts into relational tables. Idempotent via INSERT OR REPLACE.
"""
import os
import json
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.utils.field_mapping import (
    BP_FIELDS, ADDR_FIELDS, PLANT_FIELDS, PRODUCT_FIELDS,
    SO_FIELDS, SOI_FIELDS, SL_FIELDS,
    DLV_FIELDS, DLVI_FIELDS,
    BIL_FIELDS, BILI_FIELDS, BILC_FIELDS,
    JE_FIELDS, PAY_FIELDS,
    pick, safe_float
)

DATA_DIR = os.getenv("DATA_DIR", "./data")


def load_json_folder(folder_name: str) -> list:
    """Load all JSON records from a folder. Supports array or NDJSON format."""
    path = Path(DATA_DIR) / folder_name
    records = []
    if not path.exists():
        return records
    # Support both .json and .jsonl extensions
    files = list(path.glob("*.json")) + list(path.glob("*.jsonl"))
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            continue
        # .jsonl files and any file with newline-delimited JSON
        if file.suffix == ".jsonl":
            for line in content.splitlines():
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        pass
        else:
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    records.extend(data)
                elif isinstance(data, dict):
                    # Some SAP exports wrap data in a "value" key
                    if "value" in data:
                        records.extend(data["value"])
                    else:
                        records.append(data)
            except json.JSONDecodeError:
                # Fallback: try line-by-line NDJSON
                for line in content.splitlines():
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except Exception:
                            pass
    return records


def ingest_customers(db: Session):
    records = load_json_folder("business_partners")
    count = 0
    for r in records:
        cid = pick(r, BP_FIELDS["customer_id"])
        if not cid:
            continue
        db.execute(text("""
            INSERT OR REPLACE INTO customers (customer_id, name, country, city, region, raw_json)
            VALUES (:cid, :name, :country, :city, :region, :raw)
        """), {
            "cid": str(cid),
            "name": pick(r, BP_FIELDS["name"], ""),
            "country": pick(r, BP_FIELDS["country"], ""),
            "city": pick(r, BP_FIELDS["city"], ""),
            "region": pick(r, BP_FIELDS["region"], ""),
            "raw": json.dumps(r),
        })
        count += 1
    db.commit()
    return count


def ingest_addresses(db: Session):
    records = load_json_folder("business_partner_addresses")
    count = 0
    for r in records:
        aid = pick(r, ADDR_FIELDS["address_id"])
        cid = pick(r, ADDR_FIELDS["customer_id"])
        if not aid:
            aid = str(uuid.uuid4())
        if not cid:
            continue
        db.execute(text("""
            INSERT OR REPLACE INTO addresses (address_id, customer_id, street, city, postal_code, country, raw_json)
            VALUES (:aid, :cid, :street, :city, :postal, :country, :raw)
        """), {
            "aid": str(aid),
            "cid": str(cid),
            "street": pick(r, ADDR_FIELDS["street"], ""),
            "city": pick(r, ADDR_FIELDS["city"], ""),
            "postal": pick(r, ADDR_FIELDS["postal_code"], ""),
            "country": pick(r, ADDR_FIELDS["country"], ""),
            "raw": json.dumps(r),
        })
        count += 1
    db.commit()
    return count


def ingest_plants(db: Session):
    records = load_json_folder("plants")
    count = 0
    for r in records:
        pid = pick(r, PLANT_FIELDS["plant_id"])
        if not pid:
            continue
        db.execute(text("""
            INSERT OR REPLACE INTO plants (plant_id, name, country, city, raw_json)
            VALUES (:pid, :name, :country, :city, :raw)
        """), {
            "pid": str(pid),
            "name": pick(r, PLANT_FIELDS["name"], ""),
            "country": pick(r, PLANT_FIELDS["country"], ""),
            "city": pick(r, PLANT_FIELDS["city"], ""),
            "raw": json.dumps(r),
        })
        count += 1
    db.commit()
    return count


def ingest_products(db: Session):
    count = 0
    desc_map = {}
    for r in load_json_folder("product_descriptions"):
        pid = pick(r, PRODUCT_FIELDS["product_id"])
        desc = pick(r, PRODUCT_FIELDS["description"], "")
        if pid and desc:
            desc_map[str(pid)] = desc

    for r in load_json_folder("products"):
        pid = pick(r, PRODUCT_FIELDS["product_id"])
        if not pid:
            continue
        db.execute(text("""
            INSERT OR REPLACE INTO products (product_id, description, product_group, base_unit, raw_json)
            VALUES (:pid, :desc, :pg, :bu, :raw)
        """), {
            "pid": str(pid),
            "desc": desc_map.get(str(pid), pick(r, PRODUCT_FIELDS["description"], "")),
            "pg": pick(r, PRODUCT_FIELDS["product_group"], ""),
            "bu": pick(r, PRODUCT_FIELDS["base_unit"], ""),
            "raw": json.dumps(r),
        })
        count += 1
    db.commit()
    return count


def ingest_sales_orders(db: Session):
    count = 0
    for r in load_json_folder("sales_order_headers"):
        oid = pick(r, SO_FIELDS["order_id"])
        if not oid:
            continue
        db.execute(text("""
            INSERT OR REPLACE INTO sales_orders
            (order_id, customer_id, order_date, net_value, currency, status, sales_org, raw_json)
            VALUES (:oid, :cid, :odate, :nv, :cur, :status, :sorg, :raw)
        """), {
            "oid": str(oid),
            "cid": pick(r, SO_FIELDS["customer_id"], ""),
            "odate": pick(r, SO_FIELDS["order_date"], ""),
            "nv": safe_float(pick(r, SO_FIELDS["net_value"])),
            "cur": pick(r, SO_FIELDS["currency"], ""),
            "status": pick(r, SO_FIELDS["status"], ""),
            "sorg": pick(r, SO_FIELDS["sales_org"], ""),
            "raw": json.dumps(r),
        })
        count += 1

    for r in load_json_folder("sales_order_items"):
        oid = pick(r, SOI_FIELDS["order_id"])
        iid = pick(r, SOI_FIELDS["item_id"])
        if not oid or not iid:
            continue
        composite = f"{oid}:{iid}"
        db.execute(text("""
            INSERT OR REPLACE INTO sales_order_items
            (item_id, order_id, product_id, quantity, net_value, currency, raw_json)
            VALUES (:iid, :oid, :pid, :qty, :nv, :cur, :raw)
        """), {
            "iid": composite,
            "oid": str(oid),
            "pid": pick(r, SOI_FIELDS["product_id"], ""),
            "qty": safe_float(pick(r, SOI_FIELDS["quantity"])),
            "nv": safe_float(pick(r, SOI_FIELDS["net_value"])),
            "cur": pick(r, SOI_FIELDS["currency"], ""),
            "raw": json.dumps(r),
        })
    db.commit()
    return count


def ingest_deliveries(db: Session):
    count = 0
    for r in load_json_folder("outbound_delivery_headers"):
        did = pick(r, DLV_FIELDS["delivery_id"])
        if not did:
            continue
        db.execute(text("""
            INSERT OR REPLACE INTO deliveries
            (delivery_id, order_id, plant_id, delivery_date, actual_goods_movement_date, status, raw_json)
            VALUES (:did, :oid, :pid, :ddate, :agmd, :status, :raw)
        """), {
            "did": str(did),
            "oid": pick(r, DLV_FIELDS["order_id"], ""),
            "pid": pick(r, DLV_FIELDS["plant_id"], ""),
            "ddate": pick(r, DLV_FIELDS["delivery_date"], ""),
            "agmd": pick(r, DLV_FIELDS["actual_goods_movement_date"], ""),
            "status": pick(r, DLV_FIELDS["status"], ""),
            "raw": json.dumps(r),
        })
        count += 1

    for r in load_json_folder("outbound_delivery_items"):
        iid = pick(r, DLVI_FIELDS["item_id"])
        did = pick(r, DLVI_FIELDS["delivery_id"])
        if not did or not iid:
            continue
        db.execute(text("""
            INSERT OR REPLACE INTO delivery_items
            (item_id, delivery_id, product_id, order_id, quantity, raw_json)
            VALUES (:iid, :did, :pid, :oid, :qty, :raw)
        """), {
            "iid": f"{did}:{iid}",
            "did": str(did),
            "pid": pick(r, DLVI_FIELDS["product_id"], ""),
            "oid": pick(r, DLVI_FIELDS["order_id"], ""),
            "qty": safe_float(pick(r, DLVI_FIELDS["quantity"])),
            "raw": json.dumps(r),
        })
    db.commit()
    return count


def ingest_billing(db: Session):
    count = 0
    for r in load_json_folder("billing_document_headers"):
        bid = pick(r, BIL_FIELDS["billing_id"])
        if not bid:
            continue
        db.execute(text("""
            INSERT OR REPLACE INTO billing_documents
            (billing_id, order_id, delivery_id, customer_id, billing_date, net_value, currency, status, raw_json)
            VALUES (:bid, :oid, :did, :cid, :bdate, :nv, :cur, :status, :raw)
        """), {
            "bid": str(bid),
            "oid": pick(r, BIL_FIELDS["order_id"], ""),
            "did": pick(r, BIL_FIELDS["delivery_id"], ""),
            "cid": pick(r, BIL_FIELDS["customer_id"], ""),
            "bdate": pick(r, BIL_FIELDS["billing_date"], ""),
            "nv": safe_float(pick(r, BIL_FIELDS["net_value"])),
            "cur": pick(r, BIL_FIELDS["currency"], ""),
            "status": pick(r, BIL_FIELDS["status"], ""),
            "raw": json.dumps(r),
        })
        count += 1

    for r in load_json_folder("billing_document_items"):
        iid = pick(r, BILI_FIELDS["item_id"])
        bid = pick(r, BILI_FIELDS["billing_id"])
        if not bid or not iid:
            continue
        db.execute(text("""
            INSERT OR REPLACE INTO billing_items
            (item_id, billing_id, product_id, quantity, net_value, currency, raw_json)
            VALUES (:iid, :bid, :pid, :qty, :nv, :cur, :raw)
        """), {
            "iid": f"{bid}:{iid}",
            "bid": str(bid),
            "pid": pick(r, BILI_FIELDS["product_id"], ""),
            "qty": safe_float(pick(r, BILI_FIELDS["quantity"])),
            "nv": safe_float(pick(r, BILI_FIELDS["net_value"])),
            "cur": pick(r, BILI_FIELDS["currency"], ""),
            "raw": json.dumps(r),
        })

    # Cancellations
    cancellation_ids = set()
    for r in load_json_folder("billing_document_cancellations"):
        cid = pick(r, BILC_FIELDS["cancellation_id"])
        orig = pick(r, BILC_FIELDS["original_billing_id"])
        if not cid:
            continue
        cancellation_ids.add(str(orig) if orig else "")
        db.execute(text("""
            INSERT OR REPLACE INTO billing_cancellations
            (cancellation_id, original_billing_id, cancel_date, reason, raw_json)
            VALUES (:cid, :orig, :cdate, :reason, :raw)
        """), {
            "cid": str(cid),
            "orig": str(orig) if orig else "",
            "cdate": pick(r, BILC_FIELDS["cancel_date"], ""),
            "reason": pick(r, BILC_FIELDS["reason"], ""),
            "raw": json.dumps(r),
        })

    # Mark cancelled billing docs
    for orig_id in cancellation_ids:
        if orig_id:
            db.execute(text(
                "UPDATE billing_documents SET cancelled = 1 WHERE billing_id = :bid"
            ), {"bid": orig_id})

    db.commit()
    return count


def ingest_journal_entries(db: Session):
    count = 0
    seen = set()
    for r in load_json_folder("journal_entry_items_accounts_receivable"):
        eid = pick(r, JE_FIELDS["entry_id"])
        if not eid:
            continue
        if str(eid) in seen:
            continue
        seen.add(str(eid))
        db.execute(text("""
            INSERT OR REPLACE INTO journal_entries
            (entry_id, billing_id, customer_id, posting_date, amount, currency, account, raw_json)
            VALUES (:eid, :bid, :cid, :pdate, :amt, :cur, :acct, :raw)
        """), {
            "eid": str(eid),
            "bid": pick(r, JE_FIELDS["billing_id"], ""),
            "cid": pick(r, JE_FIELDS["customer_id"], ""),
            "pdate": pick(r, JE_FIELDS["posting_date"], ""),
            "amt": safe_float(pick(r, JE_FIELDS["amount"])),
            "cur": pick(r, JE_FIELDS["currency"], ""),
            "acct": pick(r, JE_FIELDS["account"], ""),
            "raw": json.dumps(r),
        })
        count += 1
    db.commit()
    return count


def ingest_payments(db: Session):
    count = 0
    for r in load_json_folder("payments_accounts_receivable"):
        pid = pick(r, PAY_FIELDS["payment_id"])
        if not pid:
            continue
        db.execute(text("""
            INSERT OR REPLACE INTO payments
            (payment_id, customer_id, billing_id, journal_entry_id, payment_date, amount, currency, raw_json)
            VALUES (:pid, :cid, :bid, :jid, :pdate, :amt, :cur, :raw)
        """), {
            "pid": str(pid),
            "cid": pick(r, PAY_FIELDS["customer_id"], ""),
            "bid": pick(r, PAY_FIELDS["billing_id"], ""),
            "jid": pick(r, PAY_FIELDS["journal_entry_id"], ""),
            "pdate": pick(r, PAY_FIELDS["payment_date"], ""),
            "amt": safe_float(pick(r, PAY_FIELDS["amount"])),
            "cur": pick(r, PAY_FIELDS["currency"], ""),
            "raw": json.dumps(r),
        })
        count += 1
    db.commit()
    return count


def ingest_customer_company_assignments(db: Session):
    """
    customer_company_assignments — links customer to company code.
    Stored as supplemental metadata on the customer record.
    Fields we try: BusinessPartner, CompanyCode, AccountGroup, etc.
    """
    count = 0
    for r in load_json_folder("customer_company_assignments"):
        cid = pick(r, ["BusinessPartner", "Customer", "customer_id"])
        company = pick(r, ["CompanyCode", "company_code", "CompanyCodeName"])
        if not cid:
            continue
        # Enrich the customer row with company code info
        db.execute(text("""
            UPDATE customers SET raw_json = json_patch(
                COALESCE(raw_json, '{}'),
                json_object('company_code', :company)
            ) WHERE customer_id = :cid
        """), {"cid": str(cid), "company": str(company or "")})
        count += 1
    db.commit()
    return count


def ingest_customer_sales_area_assignments(db: Session):
    """
    customer_sales_area_assignments — links customer to sales org / dist channel / division.
    Stored as supplemental metadata.
    """
    count = 0
    for r in load_json_folder("customer_sales_area_assignments"):
        cid = pick(r, ["BusinessPartner", "Customer", "customer_id"])
        sales_org = pick(r, ["SalesOrganization", "SalesOrg", "sales_org"])
        if not cid:
            continue
        db.execute(text("""
            UPDATE customers SET raw_json = json_patch(
                COALESCE(raw_json, '{}'),
                json_object('sales_org', :sorg)
            ) WHERE customer_id = :cid
        """), {"cid": str(cid), "sorg": str(sales_org or "")})
        count += 1
    db.commit()
    return count


def ingest_product_plants(db: Session):
    """
    product_plants — links products to the plants they're stored in.
    Stored as supplemental metadata; also used to enrich graph edges if needed.
    """
    count = 0
    for r in load_json_folder("product_plants"):
        pid = pick(r, ["Product", "Material", "product_id"])
        plant = pick(r, ["Plant", "plant_id"])
        if not pid:
            continue
        # Enrich product with plant info
        db.execute(text("""
            UPDATE products SET raw_json = json_patch(
                COALESCE(raw_json, '{}'),
                json_object('plant', :plant)
            ) WHERE product_id = :pid
        """), {"pid": str(pid), "plant": str(plant or "")})
        count += 1
    db.commit()
    return count


def ingest_product_storage_locations(db: Session):
    """
    product_storage_locations — storage location details per product/plant.
    Stored as supplemental metadata on the product.
    """
    count = 0
    for r in load_json_folder("product_storage_locations"):
        pid = pick(r, ["Product", "Material", "product_id"])
        sloc = pick(r, ["StorageLocation", "storage_location", "StorageLocationName"])
        if not pid:
            continue
        db.execute(text("""
            UPDATE products SET raw_json = json_patch(
                COALESCE(raw_json, '{}'),
                json_object('storage_location', :sloc)
            ) WHERE product_id = :pid
        """), {"pid": str(pid), "sloc": str(sloc or "")})
        count += 1
    db.commit()
    return count


def ingest_schedule_lines(db: Session):
    """
    sales_order_schedule_lines — confirmed delivery dates per SO item.
    Stored in schedule_lines table.
    """
    count = 0
    for r in load_json_folder("sales_order_schedule_lines"):
        oid = pick(r, SL_FIELDS["order_id"])
        iid = pick(r, SL_FIELDS["item_id"])
        if not oid:
            continue
        sl_id = f"{oid}:{iid}:{count}"
        db.execute(text("""
            INSERT OR REPLACE INTO schedule_lines
            (id, order_id, item_id, confirmed_qty, delivery_date, raw_json)
            VALUES (:id, :oid, :iid, :qty, :ddate, :raw)
        """), {
            "id": sl_id,
            "oid": str(oid),
            "iid": str(iid) if iid else "",
            "qty": safe_float(pick(r, SL_FIELDS["confirmed_qty"])),
            "ddate": pick(r, SL_FIELDS["delivery_date"], ""),
            "raw": json.dumps(r),
        })
        count += 1
    db.commit()
    return count


def run_full_ingestion(db: Session) -> dict:
    """Run all ingestion steps and return counts."""
    results = {}
    results["customers"] = ingest_customers(db)
    results["addresses"] = ingest_addresses(db)
    results["customer_company_assignments"] = ingest_customer_company_assignments(db)
    results["customer_sales_area_assignments"] = ingest_customer_sales_area_assignments(db)
    results["plants"] = ingest_plants(db)
    results["products"] = ingest_products(db)
    results["product_plants"] = ingest_product_plants(db)
    results["product_storage_locations"] = ingest_product_storage_locations(db)
    results["sales_orders"] = ingest_sales_orders(db)
    results["schedule_lines"] = ingest_schedule_lines(db)
    results["deliveries"] = ingest_deliveries(db)
    results["billing"] = ingest_billing(db)
    results["journal_entries"] = ingest_journal_entries(db)
    results["payments"] = ingest_payments(db)
    return results