"""
Generate sample SAP-style O2C JSON data for local testing.
Run: python scripts/generate_sample_data.py
Creates ./data/ folder with sample JSON files.
"""
import json
import os
import random
from pathlib import Path

DATA_DIR = Path("./data")

FOLDERS = [
    "business_partners", "business_partner_addresses",
    "plants", "products", "product_descriptions",
    "sales_order_headers", "sales_order_items",
    "outbound_delivery_headers", "outbound_delivery_items",
    "billing_document_headers", "billing_document_items",
    "billing_document_cancellations",
    "journal_entry_items_accounts_receivable",
    "payments_accounts_receivable",
]


def mkdirs():
    for f in FOLDERS:
        (DATA_DIR / f).mkdir(parents=True, exist_ok=True)


def write(folder, filename, data):
    with open(DATA_DIR / folder / filename, "w") as f:
        json.dump(data, f, indent=2)


def rand_date(year=2024):
    return f"{year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"


def main():
    mkdirs()
    random.seed(42)

    # ---- Business Partners ----
    customers = []
    for i in range(1, 21):
        customers.append({
            "BusinessPartner": f"BP{100000 + i}",
            "BusinessPartnerFullName": f"Customer {i} GmbH",
            "Country": random.choice(["DE", "US", "FR", "GB", "NL"]),
            "CityName": random.choice(["Berlin", "New York", "Paris", "London", "Amsterdam"]),
            "Region": f"R{i:02d}",
        })
    write("business_partners", "partners.json", customers)

    # ---- Addresses ----
    addresses = [
        {
            "BusinessPartner": c["BusinessPartner"],
            "AddressID": f"ADDR{1000 + i}",
            "StreetName": f"{i+1} Main Street",
            "CityName": c["CityName"],
            "PostalCode": f"{10000 + i}",
            "Country": c["Country"],
        }
        for i, c in enumerate(customers)
    ]
    write("business_partner_addresses", "addresses.json", addresses)

    # ---- Plants ----
    plants = [
        {
            "Plant": f"PLANT{1000 + i}",
            "PlantName": f"Plant {i}",
            "Country": random.choice(["DE", "US", "FR"]),
            "CityName": random.choice(["Berlin", "Hamburg", "Munich"]),
        }
        for i in range(1, 6)
    ]
    write("plants", "plants.json", plants)

    # ---- Products ----
    products = []
    descs = []
    for i in range(1, 16):
        pid = f"MAT{7000 + i}"
        products.append({"Product": pid, "ProductGroup": f"GRP{i % 3 + 1}", "BaseUnit": random.choice(["EA", "KG", "L"])})
        descs.append({"Product": pid, "ProductDescription": f"Product {i} - Industrial Grade"})
    write("products", "products.json", products)
    write("product_descriptions", "descriptions.json", descs)

    plant_ids = [p["Plant"] for p in plants]
    product_ids = [p["Product"] for p in products]
    customer_ids = [c["BusinessPartner"] for c in customers]

    so_headers, so_items = [], []
    dlv_headers, dlv_items = [], []
    bil_headers, bil_items, bil_cancels = [], [], []
    je_items, payments = [], []

    for i in range(1, 51):
        so_id = f"SO{5000000 + i}"
        cust = random.choice(customer_ids)
        so_val = round(random.uniform(1000, 50000), 2)
        so_headers.append({
            "SalesOrder": so_id, "SoldToParty": cust,
            "SalesOrderDate": rand_date(), "TotalNetAmount": so_val,
            "TransactionCurrency": "EUR",
            "SalesOrderProcessingStatus": random.choice(["C", "A", "B"]),
            "SalesOrganization": "1000",
        })

        # Items
        order_products = random.sample(product_ids, k=random.randint(1, 3))
        for j, prod in enumerate(order_products, 1):
            so_items.append({
                "SalesOrder": so_id, "SalesOrderItem": f"{j * 10:05d}",
                "Material": prod, "OrderQuantity": random.randint(1, 100),
                "NetAmount": round(so_val / len(order_products), 2),
                "TransactionCurrency": "EUR",
            })

        # Delivery (90%)
        if random.random() > 0.1:
            dlv_id = f"DLV{8000000 + i}"
            plant = random.choice(plant_ids)
            dlv_headers.append({
                "DeliveryDocument": dlv_id, "SalesOrder": so_id,
                "ShippingPoint": plant, "PlannedGoodsIssueDate": rand_date(),
                "ActualGoodsMovementDate": rand_date(), "OverallSDProcessStatus": "C",
            })
            for j, soi in enumerate([x for x in so_items if x["SalesOrder"] == so_id], 1):
                dlv_items.append({
                    "DeliveryDocument": dlv_id, "DeliveryDocumentItem": f"{j * 10:05d}",
                    "Material": soi["Material"], "ReferenceSDDocument": so_id,
                    "ActualDeliveryQuantity": soi["OrderQuantity"],
                })

            # Billing (85%)
            if random.random() > 0.15:
                bil_id = f"9{1000000 + i}"
                bil_val = round(so_val * random.uniform(0.95, 1.05), 2)
                bil_headers.append({
                    "BillingDocument": bil_id, "SalesOrder": so_id,
                    "DeliveryDocument": dlv_id, "PayerParty": cust,
                    "BillingDocumentDate": rand_date(), "TotalNetAmount": bil_val,
                    "TransactionCurrency": "EUR", "BillingDocumentProcessingStatus": "C",
                })
                for j, soi in enumerate([x for x in so_items if x["SalesOrder"] == so_id], 1):
                    bil_items.append({
                        "BillingDocument": bil_id, "BillingDocumentItem": f"{j * 10:05d}",
                        "Material": soi["Material"], "BillingQuantity": soi["OrderQuantity"],
                        "NetAmount": round(bil_val / max(1, len(order_products)), 2),
                        "TransactionCurrency": "EUR",
                    })

                # Journal Entry
                je_id = f"JE{2000000 + i}"
                je_items.append({
                    "AccountingDocument": je_id, "BillingDocument": bil_id,
                    "Customer": cust, "PostingDate": rand_date(),
                    "AmountInTransactionCurrency": bil_val,
                    "TransactionCurrency": "EUR", "GLAccount": "140000",
                })

                # Payment (75%)
                if random.random() > 0.25:
                    pay_id = f"PAY{3000000 + i}"
                    payments.append({
                        "PaymentDocument": pay_id, "Customer": cust,
                        "BillingDocument": bil_id, "AccountingDocument": je_id,
                        "PostingDate": rand_date(),
                        "AmountInTransactionCurrency": bil_val,
                        "TransactionCurrency": "EUR",
                    })

    # Cancellations (first 3 billed docs)
    for idx in range(min(3, len(bil_headers))):
        orig = bil_headers[idx]["BillingDocument"]
        bil_cancels.append({
            "BillingDocument": f"CANC{9900000 + idx}",
            "CancelledBillingDocument": orig,
            "BillingDocumentDate": "2024-06-15",
            "BillingDocumentCategory": "S",
        })

    write("sales_order_headers", "so_headers.json", so_headers)
    write("sales_order_items", "so_items.json", so_items)
    write("outbound_delivery_headers", "dlv_headers.json", dlv_headers)
    write("outbound_delivery_items", "dlv_items.json", dlv_items)
    write("billing_document_headers", "bil_headers.json", bil_headers)
    write("billing_document_items", "bil_items.json", bil_items)
    write("billing_document_cancellations", "bil_cancels.json", bil_cancels)
    write("journal_entry_items_accounts_receivable", "je_items.json", je_items)
    write("payments_accounts_receivable", "payments.json", payments)

    print(f"Sample data written to {DATA_DIR}/")
    print(f"  customers={len(customers)}, products={len(products)}, plants={len(plants)}")
    print(f"  sales_orders={len(so_headers)}, deliveries={len(dlv_headers)}")
    print(f"  billing={len(bil_headers)}, journal_entries={len(je_items)}, payments={len(payments)}")
    print(f"  cancellations={len(bil_cancels)}")


if __name__ == "__main__":
    main()
