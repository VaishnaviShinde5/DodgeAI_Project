# Graph-Based Order-to-Cash Query System

A context graph system with an LLM-powered natural language query interface built on SAP Order-to-Cash data.

---

## Live Demo

> https://dodgeai-project.onrender.com

## GitHub

> [Insert your GitHub repo URL here]

---
### Live Link 
>  https://dodgeai-fde-project-1.onrender.com
---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (HTML + D3.js)           │
│   Graph Visualization  │  Conversational Chat UI    │
└────────────────┬───────────────────┬────────────────┘
                 │  REST API         │
┌────────────────▼───────────────────▼────────────────┐
│                 FastAPI Backend (Python)             │
│                                                     │
│   /graph endpoint        /query endpoint            │
│   NetworkX DiGraph        Guardrail check           │
│                           ↓                         │
│                     "trace" keyword?                │
│                      ↓         ↓                   │
│               Graph BFS    LLM (Groq)              │
│                            → SQL query             │
│                            → SQLite                │
└─────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│              SQLite Database (data.db)              │
│  invoices | sales_orders | deliveries | payments   │
│  journals | products | business_partners | plants  │
└─────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Backend | FastAPI (Python) | Fast async API, auto Swagger docs, easy to run |
| Database | SQLite | Zero setup, file-based, perfect for this dataset size, full SQL support |
| Graph | NetworkX DiGraph | Lightweight, Pythonic, no external server needed |
| Graph UI | D3.js force simulation | Industry standard, interactive, zero cost |
| LLM | Groq (LLaMA 3.1 8B) | Free tier, very fast inference, reliable JSON output |
| LLM API format | OpenAI-compatible | Easy to swap providers if needed |

---

## Database Design

All 8 entity types from the SAP O2C dataset are loaded into SQLite tables:

| Table | Source | Key Fields |
|-------|--------|------------|
| `invoices` | billing_document_headers | billingDocument, soldToParty, totalNetAmount |
| `sales_orders` | sales_order_headers | salesOrder, soldToParty, netAmount |
| `deliveries` | outbound_delivery_headers | deliveryDocument, salesOrder, plant |
| `payments` | payments_accounts_receivable | accountingDocument, soldToParty, amount |
| `journals` | journal_entry_items_accounts_receivable | accountingDocument, billingDocument |
| `products` | products | product, productType, productGroup |
| `business_partners` | business_partners | businessPartner, businessPartnerName |
| `plants` | plants | plant, plantName, country |

**Why SQLite over a graph DB (e.g. Neo4j)?**
The dataset is relational in nature — entities link by foreign keys. SQL is excellent for aggregations (top N, totals, counts) which is what most business queries need. NetworkX handles the graph traversal use case (flow tracing). Using two specialized tools for two different query patterns is cleaner than forcing everything into one paradigm.

---

## Graph Model

Nodes represent business entities. Edges represent business relationships.

**Node types:** `customer`, `sales_order`, `delivery`, `invoice`, `journal`, `payment`

**Edge relationships:**
- `customer → sales_order` (placed)
- `sales_order → delivery` (delivered_via)
- `customer → invoice` (billed)
- `invoice → journal` (accounted)
- `journal → payment` (settled_by)

This models the full O2C flow: **Customer → Order → Delivery → Invoice → Journal → Payment**

---

## LLM Prompting Strategy

The LLM (LLaMA 3.1 8B via Groq) is given:

1. **Full schema** — all 8 tables with column names and descriptions
2. **SQLite-specific rules** — no `FETCH FIRST`, no square brackets, `LIMIT` only
3. **Few-shot examples** — 5 example Q→SQL pairs covering the most common query types
4. **Output constraint** — raw SQL only, no markdown, no explanation

After generation, the SQL is post-processed to:
- Strip markdown code fences
- Extract only the SELECT line if the LLM added explanation text
- Fix backtick/double-quote column wrapping

**Fallback:** If the LLM returns invalid SQL, a safe default query is used.

---

## Guardrail System

The system restricts queries to the O2C domain using a two-layer keyword approach:

**Layer 1 — Blocklist:** Off-topic keywords (weather, jokes, movie, sport, recipe, etc.) trigger an immediate rejection with a domain-restriction message.

**Layer 2 — Allowlist:** The question must contain at least one domain keyword (invoice, billing, delivery, payment, sales order, product, plant, etc.) to proceed.

**Edge cases handled:**
- Very short inputs (< 5 chars) are rejected
- Single-word nonsense inputs with no vowels are rejected
- The guardrail runs before the LLM is called, saving latency and API cost

**Example rejection:**
> "Tell me a joke" → `"This system is designed to answer questions related to the SAP Order-to-Cash dataset only."`

---

## Example Queries the System Can Answer

- *Which customers have the highest total billed amount?*
- *Show me the top 10 invoices by amount*
- *How many sales orders are there?*
- *Find invoices with no journal entry (broken flow)*
- *Find deliveries with no matching invoice*
- *Trace billing document 90504248*
- *How many payments were made in total?*
- *How many product are there in dataset?*

---

## Running Locally

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Set your API key
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 3. Start the server
uvicorn main:app --reload

# 4. Open in browser
# http://localhost:8000
```

---

## Project Structure

```
dodge-fde-project/
├── backend/
│   ├── main.py          # FastAPI app, routes, startup data loading
│   ├── db.py            # SQLite schema + connection
│   ├── graph.py         # NetworkX graph construction
│   ├── llm.py           # Groq LLM integration + SQL generation
│   ├── utils.py         # JSONL folder loader
│   └── requirements.txt
├── frontend/
│   └── index.html       # Single-file frontend: D3 graph + chat UI
├── data/
│   └── sap-o2c-data/    # Raw JSONL dataset files
└── README.md
```

---

## Tradeoffs & What I'd Improve With More Time

<<<<<<< HEAD
- **Graph DB (Neo4j/ArangoDB):** For deeper graph queries (multi-hop paths, subgraph patterns) a native graph DB would be more expressive than NetworkX + SQLite
- **Streaming responses:** Groq supports streaming; adding it would make the chat feel faster
- **Conversation memory:** Currently each query is stateless; adding message history would enable follow-up questions
- **Node highlighting:** Highlight graph nodes referenced in query responses
- **Vector search:** Embedding product/customer names for fuzzy matching
=======
### Prerequisites
- Python 3.8+
- pip

### One-time setup

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd dodge-fde-project

# 2. Install dependencies
cd backend
pip install fastapi uvicorn networkx pydantic python-dotenv requests aiofiles

# 3. Start backend (also serves frontend)
uvicorn main:app --reload
```

### Open the app

```
http://localhost:8000
```

One command. One port. Full app. No separate frontend server needed.

---

## Example Queries

| Query | Type | Expected Result |
|---|---|---|
| `trace billing document 91150187` | Graph trace | BillingDoc → Journal Entry → Customer → Payment → Sales Order |
| `show top 5 billing documents by amount` | SQL | Top 5 invoices by totalNetAmount |
| `which customer has the highest total amount` | SQL | Customer 320000083 — ₹55,337.76 |
| `how many invoices are there` | SQL | 163 |
| `show incomplete or broken order flows` | SQL | Invoices with no journal entry |
| `show total revenue from all invoices` | SQL | ₹60,908.76 |
| `hi` / `tell me a joke` / `weather` | Guardrail | 🚫 Off-topic rejection message |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Serves frontend UI |
| GET | `/health` | Health check — `{"message": "Backend running 🚀"}` |
| GET | `/graph` | All graph nodes and edges as JSON |
| POST | `/query` | `{"question": "..."}` → typed response |

### Response Types

```json
// SQL result
{
  "type": "sql_query",
  "sql": "SELECT ...",
  "columns": ["billingDocument", "totalNetAmount"],
  "result": [["90504243", 2033.65], ...]
}

// Graph flow trace
{
  "type": "graph_trace",
  "flow": {
    "start": {"type": "Invoice", "id": "91150187"},
    "next_steps": [{"type": "Journal Entry", "id": "9400635958"}],
    "summary": "Invoice 91150187 → Journal Entry 9400635958"
  }
}

// Guardrail triggered
{
  "type": "guardrail",
  "answer": "This system is designed to answer questions related to the provided SAP Order-to-Cash dataset only."
}
```

---

## Requirements Coverage

| Requirement | Status | Implementation |
|---|---|---|
| Graph Construction | ✅ | NetworkX DiGraph — Invoice, Customer, Journal nodes + edges |
| Graph Visualization | ✅ | D3.js force-directed — zoom, pan, drag, click popups |
| Conversational Query Interface | ✅ | Chat UI with real-time LLM responses |
| Natural language → SQL | ✅ | Groq LLaMA 3.1 8B with structured prompt + post-processing |
| Flow Trace (Invoice → Journal) | ✅ | Graph traversal using NetworkX successors |
| Broken/incomplete flow detection | ✅ | SQL: WHERE accountingDocument IS NULL |
| Highest billing documents query | ✅ | ORDER BY totalNetAmount DESC |
| Guardrails | ✅ | 3-layer: blocklist + allowlist + gibberish detection |
| No authentication required | ✅ | Fully open, no login |
| Single deployable unit | ✅ | Backend serves frontend on single port 8000 |
>>>>>>> a52adb8cc92804a5db092a9851e334ebb606c9ba
