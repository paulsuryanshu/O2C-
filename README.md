# O2C Graph Explorer

A full-stack application that ingests SAP Order-to-Cash (O2C) JSON data, normalizes it into a relational database, projects it into a graph, visualizes the graph interactively, and provides a grounded natural-language query interface.

---

## Architecture Overview

```
JSON Files  →  Ingestion  →  SQLite (relational)
                                  ↓
                          Graph Projection
                        (graph_nodes + graph_edges)
                                  ↓
                            FastAPI Backend
                          ↙         ↘         ↘
                   Graph API    Node API    Chat API
                       ↓                      ↓
                  React Flow UI        LLM Planner (Gemini/Groq)
                                              ↓
                                     Query Spec (JSON)
                                              ↓
                                     Guardrails Validator
                                              ↓
                                     SQL Query Executor
                                              ↓
                                     Grounded Answer
```

### Why Relational + Graph Projection?

The O2C dataset is naturally relational: sales orders reference customers, deliveries reference orders, billing references deliveries. Storing this in normalized SQL tables gives us:
- Clean joins for aggregations (top customers by billing value, etc.)
- Easy gap detection (LEFT JOINs for "delivered but not billed")
- Standard tools for ad-hoc queries

The graph projection (`graph_nodes` + `graph_edges`) adds:
- Fast traversal for "trace a document" queries
- Visual representation of entity relationships
- Neighbor lookups without complex multi-table joins

This hybrid approach avoids the complexity of a dedicated graph database (Neo4j) while preserving full graph query capability.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS |
| Graph Viz | React Flow (@xyflow/react) |
| Backend | FastAPI + Python 3.11+ |
| Database | SQLite |
| ORM/DB Access | SQLAlchemy 2.0 |
| LLM | Gemini Flash (or Groq llama3) |
| HTTP Client | httpx |

---

## Graph Model

### Node Types (visible in UI)

| Node Type | Prefix | Entity |
|-----------|--------|--------|
| Customer | `CUS:` | Business Partner |
| SalesOrder | `SO:` | Sales Order Header |
| Delivery | `DLV:` | Outbound Delivery Header |
| BillingDocument | `BIL:` | Billing Document Header |
| JournalEntry | `JE:` | AR Journal Entry |
| Payment | `PAY:` | AR Payment |
| Product | `PRD:` | Material/Product |
| Plant | `PLANT:` | Plant/Shipping Point |

### Edge Types (O2C Flow)

```
Customer  ──PLACED_ORDER──►  SalesOrder
SalesOrder ──HAS_DELIVERY──►  Delivery
SalesOrder ──HAS_BILLING──►   BillingDocument
Delivery   ──BILLED_VIA──►    BillingDocument
Delivery   ──SHIPS_FROM──►    Plant
BillingDoc ──CREATES_JOURNAL_ENTRY──►  JournalEntry
JournalEntry ──CLEARED_BY──►  Payment
BillingDoc ──INCLUDES_PRODUCT──►  Product
Delivery   ──DELIVERS_PRODUCT──►  Product
```

---

## LLM Prompting Strategy

The LLM is used **only as a query intent classifier**, not as a free-form answering engine. The system prompt provides:
1. A strict list of allowed `action` names
2. Required fields per action
3. An instruction to return only JSON
4. A `reject` action for out-of-domain queries

The LLM output is then:
1. Parsed for valid JSON
2. Validated against the whitelist of actions
3. Executed as a typed SQL query
4. Formatted into a human-readable answer with evidence

If no LLM API key is set, a rule-based fallback handles common query patterns via keyword matching.

---

## Guardrails

- **Domain check**: Prompts must contain O2C-related keywords (billing, order, delivery, payment, etc.) and must not contain off-topic signals (poem, weather, write code, etc.)
- **Action whitelist**: Only 10 specific actions are permitted
- **Required field validation**: Each action validates its required parameters before execution
- **Read-only execution**: All queries are SELECT-only; no writes from the chat interface
- **No hallucination**: If no data is found, the system reports "not found" — it never invents data
- **LLM isolation**: The LLM never sees database contents, only classifies intent

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) Gemini or Groq API key for LLM features

### 1. Clone and configure

```bash
git clone <repo>
cd o2c-graph

# Copy env template
cp .env.example backend/.env
# Edit backend/.env and add your GEMINI_API_KEY or GROQ_API_KEY
```

### 2. Set up backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add data

**Option A — Use your real SAP JSON files:**
```
backend/data/
  business_partners/           ← JSON files here
  business_partner_addresses/
  sales_order_headers/
  ...
```

**Option B — Generate sample data:**
```bash
cd backend
python scripts/generate_sample_data.py
```

### 4. Ingest data

```bash
cd backend
python scripts/ingest.py
```

### 5. Start backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 6. Set up and start frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

---

## Using the UI

1. **Graph View** — All O2C entities rendered as colored nodes. Click any node to see its metadata and connections in the right panel.
2. **Filter by type** — Click type badges in the stats bar to show only that entity type.
3. **Search** — Use the search bar to find specific customers, billing documents, sales orders, or products by ID or name.
4. **Chat panel** — Type natural-language questions. Results highlight relevant nodes on the graph.
5. **Ingest Data** — Click the "Ingest Data" button in the top bar to reload data from disk (or trigger via API).

---

## Sample Prompts

```
Which customers generated the most billing volume?
Which products are associated with the highest number of billing documents?
Find sales orders that were delivered but not billed
Find billed documents without delivery
Find open receivables without payments
Find cancelled billing documents
Trace billing document 91150187
Find the journal entry linked to billing document 91150187
```

> **Note:** Replace `91150187` with an actual billing document ID from your dataset.
> You can find IDs by searching in the top search bar or clicking nodes in the graph.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/graph` | All nodes and edges (filterable) |
| GET | `/api/graph/stats` | Node/edge type counts |
| GET | `/api/node/{id}` | Full node metadata + neighbors |
| GET | `/api/search?q=...` | Search across entities |
| POST | `/api/chat` | Natural language query |
| POST | `/api/ingest/run` | Trigger full ingestion + graph build |
| POST | `/api/ingest/graph-only` | Rebuild graph projection only |

---

## Field Mapping

If your actual JSON field names differ from what's expected, edit:
```
backend/app/utils/field_mapping.py
```

Every entity's field candidates are listed as ordered arrays. The `pick()` function tries each candidate in order, with a case-insensitive fallback.

---

## Tradeoffs & Future Improvements

### Current tradeoffs
- **SQLite**: Simple but single-writer. Replace with PostgreSQL for production.
- **Auto-layout**: Simple column-based layout. A proper force-directed or Dagre layout would be more readable for large graphs.
- **Graph size limit**: The UI fetches up to 500 nodes by default to keep rendering fast. Adjust with the `limit` param.
- **LLM fallback**: Rule-based fallback works for common patterns but misses complex phrasings.

### Future improvements
- Add proper force-directed graph layout (ELK, Dagre)
- Add graph traversal depth controls in UI
- Support multi-hop path queries ("show all entities connected to customer X")
- Add time-series views (billing volume over time)
- Export graph as PNG or JSON
- Add Postgres support for multi-user deployments
- Streaming LLM responses for long answers
