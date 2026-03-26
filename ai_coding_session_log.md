# AI Coding Session Log
## Project: Order to Cash — Graph-Based Data Modeling & LLM Query System
**Candidate:** Vaishnavi Shinde
**Tools Used:** Claude (claude.ai), GitHub Copilot
**Submission For:** Dodge AI — Forward Deployed Engineer (FDE) Assessment

---

## Overview

Throughout this project I used Claude as my primary AI coding assistant for architecture decisions, debugging, and implementation. GitHub Copilot was used inline during coding for autocompletion and boilerplate. This document captures the key sessions, prompts, decisions, and iterations.

---

## Session 1 — Project Scoping & Architecture Design

**Goal:** Understand the SAP O2C dataset structure and decide on a system architecture.

**Key Prompts Used:**

> "I have SAP Order-to-Cash data in JSONL format — billing documents, deliveries, payments, journal entries. I need to build a system that models this as a graph and lets users query it in natural language. What architecture would you recommend?"

**AI Response Summary:**
Claude recommended a three-layer architecture:
- A graph layer (NetworkX) for relationship modeling and traversal
- A relational layer (SQLite) for analytical queries
- An LLM layer (via API) for natural language → SQL translation

**Decision Made:**
I went with this split because it plays to each technology's strengths — graphs for flow tracing, SQL for aggregation. Claude also suggested FastAPI as the backend for its async support and minimal setup, which I adopted.

**Follow-up prompt:**

> "Should I use Neo4j or NetworkX for the graph? The dataset is about 163 billing documents."

**AI Response Summary:**
Claude recommended NetworkX for this scale — Neo4j adds infrastructure overhead with no benefit at ~163 nodes. It noted the graph could be built in-memory at startup with O(1) edge traversal.

**Outcome:** Finalized architecture: FastAPI + NetworkX + SQLite + Groq LLM + D3.js frontend.

---

## Session 2 — Graph Model Design

**Goal:** Define the node and edge model for the O2C graph.

**Key Prompt:**

> "In SAP O2C, a billing document links to a customer (soldToParty) and an accounting document (accountingDocument). How should I model this as a directed graph? What should nodes and edges represent?"

**AI Response Summary:**
Claude suggested:
- **Nodes:** Invoice, Customer, Journal Entry
- **Edges:** `billed` (Customer → Invoice), `accounted` (Invoice → Journal Entry)
- Direction matters: follow edges forward to trace the full O2C flow

**Iteration:**
I initially modeled edges as undirected. Claude caught this issue when I described my traversal logic:

> "If edges are undirected, how do I know which direction the flow goes? I'm getting both parent and child nodes in traversal."

Claude explained DiGraph vs Graph in NetworkX and showed me how to use `.successors()` for forward traversal. I refactored to `nx.DiGraph`.

**Code Claude helped write:**

```python
G = nx.DiGraph()
G.add_node(f"invoice_{doc['billingDocument']}", type="Invoice", ...)
G.add_node(f"customer_{doc['soldToParty']}", type="Customer", ...)
G.add_edge(f"customer_{doc['soldToParty']}", f"invoice_{doc['billingDocument']}", relation="billed")
G.add_edge(f"invoice_{doc['billingDocument']}", f"journal_{doc['accountingDocument']}", relation="accounted")
```

---

## Session 3 — LLM Prompting Strategy

**Goal:** Get the LLM to reliably generate valid SQLite queries from natural language.

**Key Prompt:**

> "I'm using Groq's LLaMA 3.1 8B to convert user questions into SQL. My schema is: invoices(billingDocument, accountingDocument, soldToParty, totalNetAmount). What prompt structure should I use to get consistent, correct SQL?"

**AI Response Summary:**
Claude recommended:
- Provide the exact schema with column descriptions
- Explicitly list SQLite constraints (no `FETCH FIRST`, always `LIMIT`)
- Give concrete pattern examples for common query types
- Ask the model to return plain SQL only — no markdown, no explanation

**Prompt Template Claude helped design:**

```
You are a SQLite query generator for an SAP Order-to-Cash dataset.
Schema: invoices(billingDocument, accountingDocument, soldToParty, totalNetAmount)
Rules:
- SQLite only. Use LIMIT, not FETCH FIRST.
- Return plain SQL only. No markdown, no explanation.
- Always include a FROM clause.
Patterns:
- "top N by amount" → ORDER BY totalNetAmount DESC LIMIT N
- "highest customer" → GROUP BY soldToParty + SUM
- "broken flows" → WHERE accountingDocument IS NULL
- "total revenue" → SUM(totalNetAmount)
Question: {user_question}
```

**Debugging Iteration:**
Initial outputs had issues:

```
Problem 1: LLM wrapped output in ```sql ... ``` fences
Problem 2: Column names had backtick wrapping → broke SQLite
Problem 3: LLM sometimes returned "FETCH FIRST 5 ROWS ONLY" instead of LIMIT
```

**Prompt to Claude:**

> "My LLM keeps returning SQL with markdown fences and backtick-wrapped column names. How do I clean this reliably in Python before executing?"

**Claude's post-processing pipeline:**

```python
def clean_sql(raw):
    # Strip markdown fences
    raw = re.sub(r"```sql|```", "", raw).strip()
    # Remove backtick wrapping around identifiers
    raw = raw.replace("`", "")
    # Replace non-SQLite syntax
    raw = re.sub(r"FETCH FIRST \d+ ROWS ONLY", lambda m: f"LIMIT {m.group().split()[2]}", raw)
    # Extract first SELECT line if LLM added explanation
    lines = [l for l in raw.splitlines() if l.strip().upper().startswith("SELECT")]
    return lines[0] if lines else raw
```

---

## Session 4 — Guardrails Implementation

**Goal:** Block off-topic and gibberish queries without breaking legitimate domain queries.

**Key Prompt:**

> "My chat interface can receive any user input. I want to block off-topic queries (jokes, weather, math) while allowing SAP O2C questions. What's a clean guardrail approach that doesn't accidentally block legitimate queries?"

**AI Response Summary:**
Claude suggested a 3-layer approach rather than a single regex:
1. **Blocklist** — immediate reject on known off-topic keywords
2. **Allowlist** — at least one domain keyword must be present
3. **Gibberish detection** — single words with no vowels are rejected

**Code Claude helped write:**

```python
OFF_TOPIC = ["weather", "joke", "poem", "story", "who is", "capital of",
             "calculate", "translate", "movie", "sport", "music", "recipe"]

DOMAIN = ["invoice", "billing", "delivery", "payment", "journal", "customer",
          "amount", "trace", "flow", "revenue", "broken", "incomplete"]

def is_off_topic(question: str) -> bool:
    q = question.lower()
    if any(kw in q for kw in OFF_TOPIC):
        return True
    if not any(kw in q for kw in DOMAIN):
        return True
    # Gibberish: single word, no vowels
    words = q.split()
    if len(words) == 1 and not re.search(r'[aeiou]', words[0]):
        return True
    return False
```

**Iteration:**
I noticed "hi" was being blocked. Claude helped me add a short-message bypass:

> "Single word greetings like 'hi' have no vowels... wait, they do. But 'gggg' doesn't. Let me re-check my regex."

Claude pointed out that "hi" has a vowel (i) and my regex was fine — the issue was actually that "hi" hit the domain allowlist check (no domain keyword present), not the gibberish check. Claude suggested adding common greetings to an exceptions list.

---

## Session 5 — D3.js Graph Visualization

**Goal:** Render the NetworkX graph interactively in the browser.

**Key Prompt:**

> "My FastAPI backend returns graph nodes and edges as JSON. How do I render this as an interactive force-directed graph using D3.js? I want zoom, drag, and click-to-inspect functionality in a single HTML file."

**AI Response Summary:**
Claude provided a D3.js v7 force simulation template with:
- `d3.forceSimulation` with link force, charge, and center
- `zoom` behavior attached to an SVG group
- `click` handler on nodes to show a metadata popup

**Debugging:**
Nodes were colliding badly. Claude suggested tuning:

```javascript
.force("charge", d3.forceManyBody().strength(-300))
.force("collision", d3.forceCollide().radius(30))
```

---

## Session 6 — Deployment & Final Debugging

**Goal:** Deploy to Render.com as a single-port application.

**Key Prompt:**

> "I want to serve my frontend (index.html) directly from FastAPI so I only need one port and one deployment. How do I do this?"

**Claude's solution:**

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")
```

**Final bug fixed with Claude's help:**

> "My deployed app on Render shows the graph but queries return 500 errors. Works locally."

Claude asked: *"Is your Groq API key set as an environment variable on Render? Check your `.env` is not being committed."*

That was exactly the issue — I had the key in `.env` which wasn't pushed to the repo. Set it as a Render environment variable and it resolved.

---

## Summary of AI Tool Usage

| Phase | Tool | How It Was Used |
|---|---|---|
| Architecture design | Claude | Recommended tech stack, explained tradeoffs |
| Graph modeling | Claude | Node/edge design, DiGraph vs Graph distinction |
| LLM prompt design | Claude | Prompt template, pattern examples, constraints |
| SQL post-processing | Claude | Regex pipeline to clean LLM output |
| Guardrails | Claude | 3-layer guardrail logic and code |
| D3.js visualization | Claude | Force simulation setup, zoom/drag handlers |
| Deployment | Claude | FastAPI static serving, env variable debugging |
| Inline code | GitHub Copilot | Boilerplate, repetitive patterns, imports |

---

## Key Learnings from AI-Assisted Development

1. **AI is best for architecture decisions early** — getting the right structure upfront saved hours of refactoring later.
2. **Iterative prompting works better than one-shot** — I always followed up with "the output has this problem" rather than trying to write a perfect prompt upfront.
3. **AI catches logical bugs well** — the undirected graph issue and the API key deployment bug were both caught through describing symptoms to Claude.
4. **Post-process LLM output programmatically** — don't trust raw LLM SQL output; always clean it in code.
