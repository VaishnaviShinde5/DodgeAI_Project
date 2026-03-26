from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import re

from db import init_db, get_connection
from graph import build_graph, G
from utils import load_folder
from llm import generate_sql

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str


# -----------------------------
# Insert helpers
# -----------------------------
def safe_float(val):
    try:
        return float(val)
    except:
        return 0.0

def safe_str(val):
    return str(val) if val is not None else ""


def insert_invoices(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM invoices")
    rows = []
    for r in data:
        bid = r.get("billingDocument")
        if not bid:
            continue
        rows.append((
            safe_str(bid),
            safe_str(r.get("accountingDocument", "")),
            safe_str(r.get("soldToParty", "")),
            safe_float(r.get("totalNetAmount")),
            safe_str(r.get("billingDocumentDate", "")),
            safe_str(r.get("billingDocumentType", "")),
        ))
    c.executemany("INSERT INTO invoices VALUES (?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(rows)} invoices")


def insert_sales_orders(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sales_orders")
    rows = []
    for r in data:
        so = r.get("salesOrder")
        if not so:
            continue
        rows.append((
            safe_str(so),
            safe_str(r.get("soldToParty", "")),
            safe_str(r.get("creationDate", "")),
            safe_float(r.get("totalNetAmount")),
            safe_str(r.get("salesOrderType", "")),
            safe_str(r.get("salesOrganization", "")),
        ))
    c.executemany("INSERT INTO sales_orders VALUES (?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(rows)} sales orders")


def insert_deliveries(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM deliveries")
    rows = []
    for r in data:
        dd = r.get("deliveryDocument")
        if not dd:
            continue
        rows.append((
            safe_str(dd),
            safe_str(r.get("salesOrder", "")),
            safe_str(r.get("soldToParty", "")),
            safe_str(r.get("creationDate", "")),
            safe_str(r.get("shippingPoint", "")),
            safe_str(r.get("plant", "")),
        ))
    c.executemany("INSERT INTO deliveries VALUES (?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(rows)} deliveries")


def insert_payments(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM payments")
    rows = []
    for r in data:
        pd = r.get("accountingDocument")
        if not pd:
            continue
        rows.append((
            safe_str(r.get("clearingAccountingDocument", "")),
            safe_str(pd),
            safe_str(r.get("customer", "")),
            safe_float(r.get("amountInCompanyCodeCurrency")),
            safe_str(r.get("postingDate", "")),
            safe_str(r.get("companyCode", "")),
        ))
    c.executemany("INSERT INTO payments VALUES (?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(rows)} payments")


def insert_journals(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM journals")
    rows = []
    for r in data:
        ad = r.get("accountingDocument")
        if not ad:
            continue
        rows.append((
            safe_str(ad),
            safe_str(r.get("referenceDocument", "")),
            safe_str(r.get("companyCode", "")),
            safe_str(r.get("fiscalYear", "")),
            safe_str(r.get("postingDate", "")),
            safe_float(r.get("amountInCompanyCodeCurrency")),
        ))
    c.executemany("INSERT INTO journals VALUES (?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(rows)} journal entries")


def insert_products(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM products")
    rows = []
    for r in data:
        p = r.get("product")
        if not p:
            continue
        rows.append((
            safe_str(p),
            safe_str(r.get("productType", "")),
            safe_str(r.get("baseUnit", "")),
            safe_str(r.get("productGroup", "")),
            safe_str(r.get("division", "")),
        ))
    c.executemany("INSERT INTO products VALUES (?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(rows)} products")


def insert_business_partners(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM business_partners")
    rows = []
    for r in data:
        bp = r.get("businessPartner")
        if not bp:
            continue
        rows.append((
            safe_str(bp),
            safe_str(r.get("businessPartnerName", "")),
            safe_str(r.get("businessPartnerCategory", "")),
            safe_str(r.get("country", "")),
            safe_str(r.get("city", "")),
        ))
    c.executemany("INSERT INTO business_partners VALUES (?,?,?,?,?)", rows)
    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(rows)} business partners")


def insert_plants(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM plants")
    rows = []
    for r in data:
        pl = r.get("plant")
        if not pl:
            continue
        rows.append((
            safe_str(pl),
            safe_str(r.get("plantName", "")),
            safe_str(r.get("country", "")),
            safe_str(r.get("city", "")),
        ))
    c.executemany("INSERT INTO plants VALUES (?,?,?,?)", rows)
    conn.commit()
    conn.close()
    print(f"✅ Inserted {len(rows)} plants")


# -----------------------------
# Startup
# -----------------------------
@app.on_event("startup")
def startup():
    init_db()

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_PATH = os.path.join(BASE_DIR, "data", "sap-o2c-data")

    invoices      = load_folder(os.path.join(DATA_PATH, "billing_document_headers"))
    sales_orders  = load_folder(os.path.join(DATA_PATH, "sales_order_headers"))
    deliveries    = load_folder(os.path.join(DATA_PATH, "outbound_delivery_headers"))
    payments      = load_folder(os.path.join(DATA_PATH, "payments_accounts_receivable"))
    journals      = load_folder(os.path.join(DATA_PATH, "journal_entry_items_accounts_receivable"))
    products      = load_folder(os.path.join(DATA_PATH, "products"))
    partners      = load_folder(os.path.join(DATA_PATH, "business_partners"))
    plants_data   = load_folder(os.path.join(DATA_PATH, "plants"))

    print(f"📦 Loaded — invoices:{len(invoices)} orders:{len(sales_orders)} deliveries:{len(deliveries)} payments:{len(payments)} journals:{len(journals)}")

    data_map = {
        "invoices": invoices,
        "sales_orders": sales_orders,
        "deliveries": deliveries,
        "payments": payments,
        "journals": journals,
    }
    build_graph(data_map)
    print("🔗 Graph built")

    insert_invoices(invoices)
    insert_sales_orders(sales_orders)
    insert_deliveries(deliveries)
    insert_payments(payments)
    insert_journals(journals)
    insert_products(products)
    insert_business_partners(partners)
    insert_plants(plants_data)

    print("✅ All data loaded!")


# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def home():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_path = os.path.join(BASE_DIR, "frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Backend running 🚀"}


@app.get("/health")
def health():
    return {"message": "Backend running 🚀"}


@app.get("/graph")
def get_graph():
    nodes = [{"id": n, "type": G.nodes[n].get("type", "unknown")} for n in G.nodes()]
    edges = [{"source": u, "target": v, "relation": G[u][v].get("relation", "")} for u, v in G.edges()]
    return {"nodes": nodes, "edges": edges}


# -----------------------------
# Guardrails
# -----------------------------
ALLOWED_KEYWORDS = [
    "invoice", "billing", "billing document", "delivery", "payment",
    "journal", "journal entry", "order", "sales order", "customer",
    "amount", "document", "trace", "flow", "top", "highest", "lowest",
    "total", "show", "list", "find", "which", "how many", "count",
    "broken", "incomplete", "billed", "sold", "party", "accounting",
    "net", "material", "product", "plant", "dispatch", "shipment",
    "accounts receivable", "revenue", "outstanding", "paid", "unpaid",
    "first", "last", "all", "give", "get", "partner", "business partner",
    "sales", "organization", "date", "status", "currency",
]

OFF_TOPIC_KEYWORDS = [
    "weather", "temperature", "forecast",
    "who is", "what is your name", "your name",
    "capital of", "capital city",
    "joke", "tell me a joke", "funny",
    "write a", "write me", "poem", "story", "essay", "creative",
    "recipe", "cook",
    "movie", "film", "actor", "actress",
    "sport", "cricket", "football", "ipl",
    "music", "song", "singer",
    "news", "politics", "election",
    "how are you", "how r you",
    "good morning", "good night", "good evening",
    "what can you do", "who made you", "are you human", "are you a bot",
    "translate", "language",
]

GUARDRAIL_RESPONSE = {
    "type": "guardrail",
    "answer": "This system is designed to answer questions related to the SAP Order-to-Cash dataset only. Please ask about invoices, billing documents, sales orders, deliveries, payments, or journal entries."
}


def is_valid_question(question: str) -> bool:
    for kw in OFF_TOPIC_KEYWORDS:
        if kw in question:
            return False
    if len(question.strip()) < 5:
        return False
    for kw in ALLOWED_KEYWORDS:
        if kw in question:
            return True
    return False


# -----------------------------
# Query Endpoint
# -----------------------------
@app.post("/query")
def query(q: Query):
    question = q.question.lower().strip()

    if not is_valid_question(question):
        return GUARDRAIL_RESPONSE

    # Flow trace using graph
    if "trace" in question:
        match = re.search(r'\d+', question)
        if not match:
            return {"type": "error", "error": "Please provide a valid document ID to trace."}

        doc_id = match.group()

        # Try to find in graph as invoice, delivery or sales order
        candidates = [f"invoice_{doc_id}", f"delivery_{doc_id}", f"order_{doc_id}"]
        found_node = next((n for n in candidates if n in G), None)

        if not found_node:
            return {"type": "error", "error": f"Document {doc_id} not found in graph."}

        def node_label(n):
            if "invoice" in n:   return ("Billing Doc", n.split("_")[1])
            if "delivery" in n:  return ("Delivery", n.split("_")[1])
            if "order" in n:     return ("Sales Order", n.split("_")[1])
            if "journal" in n:   return ("Journal Entry", n.split("_")[1])
            if "customer" in n:  return ("Customer", n.split("_")[1])
            if "payment" in n:   return ("Payment", n.split("_")[1])
            return ("Node", n)

        # BFS up to 3 hops
        visited = set()
        queue = [found_node]
        steps = []
        while queue and len(steps) < 10:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            label, id_ = node_label(current)
            steps.append({"type": label, "id": id_})
            for neighbor in list(G.successors(current)) + list(G.predecessors(current)):
                if neighbor not in visited:
                    queue.append(neighbor)

        flow_text = " → ".join(f"{s['type']} {s['id']}" for s in steps)

        return {
            "type": "graph_trace",
            "flow": {
                "start": {"type": steps[0]["type"], "id": steps[0]["id"]} if steps else {},
                "next_steps": steps[1:],
                "summary": flow_text,
                "highlighted_nodes": [f"{s['type'].lower().replace(' ', '_')}_{s['id']}" for s in steps]
            }
        }

    # LLM → SQL
    sql = generate_sql(question)
    print("🧠 Generated SQL:", sql)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        col_names = [d[0] for d in cursor.description] if cursor.description else []
    except Exception as e:
        return {"type": "error", "error": str(e), "sql": sql}
    finally:
        conn.close()

    return {
        "type": "sql_query",
        "sql": sql,
        "columns": col_names,
        "result": rows
    }