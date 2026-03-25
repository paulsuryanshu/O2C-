# Architecture — O2C Graph Explorer

## 1. Ingestion Pipeline

```
backend/data/
  ├── business_partners/*.json
  ├── sales_order_headers/*.json
  ├── ...
```

Each folder is read by `app/services/ingestion.py`. Each function:
1. Calls `load_json_folder(folder_name)` — handles both JSON array files and NDJSON
2. Extracts fields using `pick(record, candidates)` from `field_mapping.py`
3. Executes `INSERT OR REPLACE` to make ingestion **idempotent**
4. Commits after each entity type

**Ingestion order matters:**
```
customers → addresses → plants → products
  → sales_orders → sales_order_items
  → deliveries → delivery_items
  → billing_documents → billing_items → billing_cancellations
  → journal_entries → payments
```

Foreign keys are not enforced at the SQLite level (for resilience with incomplete data), but relationships are encoded in the graph projection stage.

---

## 2. Normalization Strategy

Each SAP document type maps to one primary relational table:

| SAP Folder | Relational Table | Primary Key |
|-----------|-----------------|-------------|
| business_partners | customers | customer_id |
| business_partner_addresses | addresses | address_id |
| plants | plants | plant_id |
| products | products | product_id |
| sales_order_headers | sales_orders | order_id |
| sales_order_items | sales_order_items | order_id:item_id |
| outbound_delivery_headers | deliveries | delivery_id |
| outbound_delivery_items | delivery_items | delivery_id:item_id |
| billing_document_headers | billing_documents | billing_id |
| billing_document_items | billing_items | billing_id:item_id |
| billing_document_cancellations | billing_cancellations | cancellation_id |
| journal_entry_items_accounts_receivable | journal_entries | entry_id |
| payments_accounts_receivable | payments | payment_id |

Composite item keys (`order_id:item_id`) ensure uniqueness across re-runs and prevent duplicates.

---

## 3. Graph Projection Strategy

After relational data is loaded, `app/services/graph_builder.py` creates graph nodes and edges from the relational tables.

### Node creation
Each relational entity becomes a graph node with a stable, typed ID:
```
CUS:{customer_id}
SO:{order_id}
DLV:{delivery_id}
BIL:{billing_id}
JE:{entry_id}
PAY:{payment_id}
PRD:{product_id}
PLANT:{plant_id}
```

Node metadata (stored as JSON in `metadata_json`) includes the most important fields for the detail panel.

### Edge creation
Edges are derived from foreign key relationships in the relational tables:

```sql
-- SalesOrder → Delivery (from deliveries.order_id)
-- SalesOrder → BillingDocument (from billing_documents.order_id)
-- Delivery → BillingDocument (from billing_documents.delivery_id)
-- BillingDocument → JournalEntry (from journal_entries.billing_id)
-- JournalEntry → Payment (from payments.journal_entry_id)
-- BillingDocument → Product (from billing_items.product_id)
-- Delivery → Product (from delivery_items.product_id)
-- Delivery → Plant (from deliveries.plant_id)
-- Customer → SalesOrder (from sales_orders.customer_id)
```

Edge IDs use a deterministic format: `E:{source_id}--{edge_type}-->{target_id}`, so rebuilds are idempotent.

The graph is fully rebuilt on each ingestion run (DELETE then re-insert), ensuring consistency with the relational data.

---

## 4. Query Execution Path

```
User types prompt
      ↓
[Guardrails] is_in_domain(prompt)?
      ↓ yes
[LLM Planner] plan_query(prompt) → JSON spec
      ↓
[Guardrails] validate_query_spec(spec)
      ↓ valid
[Query Executor] execute_query(db, spec)
      ↓
SQL queries against SQLite
      ↓
Structured result + highlight node/edge IDs
      ↓
Formatted markdown answer returned to UI
```

### Allowed Actions

| Action | SQL Pattern |
|--------|------------|
| `trace_billing_flow` | JOIN billing_documents → sales_orders → deliveries → journal_entries → payments |
| `lookup_journal_entry_for_billing` | SELECT FROM journal_entries WHERE billing_id = ? |
| `top_products_by_billing_count` | GROUP BY product_id ORDER BY COUNT(billing_id) |
| `top_customers_by_billing_value` | GROUP BY customer_id ORDER BY SUM(net_value) |
| `delivered_not_billed` | LEFT JOIN deliveries → billing_documents WHERE billing_id IS NULL |
| `billed_without_delivery` | SELECT FROM billing_documents WHERE delivery_id IS NULL |
| `open_receivables_without_payment` | LEFT JOIN journal_entries → payments WHERE payment_id IS NULL |
| `cancelled_billing_documents` | JOIN billing_documents → billing_cancellations |
| `entity_neighbors` | SELECT FROM graph_edges WHERE source_id = ? OR target_id = ? |
| `lookup_document` | SELECT FROM {table} WHERE {id_col} = ? |

---

## 5. Guardrail Design

Two-layer guardrail system:

**Layer 1 — Domain Filter (pre-LLM)**
`is_in_domain(prompt)` scans for:
- Off-topic signals (poem, weather, write code, etc.) → immediate reject
- Domain keywords (billing, order, delivery, payment, etc.) → pass through
This prevents wasting LLM API calls on clearly off-domain requests.

**Layer 2 — Query Spec Validation (post-LLM)**
`validate_query_spec(spec)` checks:
- `action` is in `ALLOWED_ACTIONS` whitelist
- Required fields are present for the given action
- No SQL injection possible (parameterized queries only)

If either layer rejects the request, a standard message is returned:
> "This system is designed to answer questions related to the provided Order-to-Cash dataset only."

---

## 6. LLM Prompt Design

The system prompt is minimal and structured:

```
You are a query planner for an Order-to-Cash (O2C) business data system.
Your ONLY job is to convert a natural language question into a JSON query spec.
You must respond with ONLY valid JSON and nothing else.

Allowed actions: [list]
Rules:
1. Out-of-domain → {"action": "reject", "reason": "out_of_domain"}
2. Extract document IDs exactly as mentioned
3. Return ONLY JSON, no explanation, no markdown fences
```

Key design decisions:
- **Temperature = 0.1** — near-deterministic output for consistent JSON
- **Max tokens = 256** — query specs are small; limits cost
- **No database contents in prompt** — LLM never sees actual data values
- **Regex fallback** — if LLM fails or no API key configured, keyword rules handle common patterns

---

## 7. Tradeoffs

| Decision | Chosen | Alternative | Reason |
|----------|--------|-------------|--------|
| Graph DB | SQLite projection | Neo4j | No extra infrastructure; SQL handles O2C queries well |
| Layout | Column-by-type | Force-directed | Simpler, predictable; force-directed needs a library |
| LLM role | Intent classifier only | Free-form answering | Prevents hallucination; all answers grounded in SQL |
| Auth | None | JWT | Assignment scope; add for production |
| Ingestion | Idempotent INSERT OR REPLACE | Delta ingestion | Simpler; re-runs are safe |
| Graph size | 500 node limit in API | Unlimited | Browser performance |
