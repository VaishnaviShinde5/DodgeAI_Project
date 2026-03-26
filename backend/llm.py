import requests
import os
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY", "")  # set in .env file


def generate_sql(question):
    prompt = f"""You are a SQL expert for an SAP Order-to-Cash (O2C) dataset stored in SQLite.

Available tables and columns:

invoices(billingDocument, accountingDocument, soldToParty, totalNetAmount, billingDocumentDate, billingDocumentType)
- billingDocument = billing/invoice document number
- accountingDocument = linked journal entry number
- soldToParty = customer ID
- totalNetAmount = invoice amount
- billingDocumentDate = date of billing
- billingDocumentType = type code e.g. F2

sales_orders(salesOrder, soldToParty, salesOrderDate, netAmount, salesOrderType, salesOrganization)
- salesOrder = sales order number
- soldToParty = customer ID
- netAmount = order value

deliveries(deliveryDocument, salesOrder, soldToParty, deliveryDate, shippingPoint, plant)
- deliveryDocument = delivery number
- salesOrder = linked sales order number
- plant = shipping plant

payments(paymentDocument, accountingDocument, soldToParty, amountInCompanyCodeCurrency, paymentDate, companyCode)
- paymentDocument = payment document number
- accountingDocument = linked journal entry
- soldToParty = customer ID

journals(accountingDocument, billingDocument, companyCode, fiscalYear, postingDate, amountInCompanyCodeCurrency)
- accountingDocument = journal entry number
- billingDocument = linked billing document

products(product, productType, baseUnit, productGroup, division)
- product = product/material ID

business_partners(businessPartner, businessPartnerName, businessPartnerType, country, city)
- businessPartner = partner ID (same as soldToParty/customer)

plants(plant, plantName, country, city)

STRICT RULES:
- SQLite syntax only
- Use LIMIT not TOP or FETCH FIRST
- No square brackets around column names
- Only output a single raw SQL query, no explanation, no markdown
- When joining invoices to business_partners, join on invoices.soldToParty = business_partners.businessPartner

EXAMPLE QUERIES:
Q: Which products have the most billing documents?
A: SELECT product, COUNT(*) as billing_count FROM invoices JOIN products ON invoices.soldToParty = products.product GROUP BY product ORDER BY billing_count DESC LIMIT 10

Q: Which customer has the highest total billed amount?
A: SELECT soldToParty, SUM(totalNetAmount) as total FROM invoices GROUP BY soldToParty ORDER BY total DESC LIMIT 5

Q: Find broken flows — sales orders delivered but not billed
A: SELECT d.salesOrder, d.deliveryDocument FROM deliveries d LEFT JOIN invoices i ON d.salesOrder = i.billingDocument WHERE i.billingDocument IS NULL LIMIT 20

Q: Find invoices with no journal entry (incomplete flow)
A: SELECT billingDocument, soldToParty, totalNetAmount FROM invoices WHERE accountingDocument IS NULL OR accountingDocument = '' LIMIT 20

Q: Show top invoices by amount
A: SELECT billingDocument, soldToParty, totalNetAmount FROM invoices ORDER BY totalNetAmount DESC LIMIT 10

User question: {question}
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=15
        )

        data = response.json()

        if "choices" not in data:
            print("LLM error:", data)
            return "SELECT billingDocument, soldToParty, totalNetAmount FROM invoices ORDER BY totalNetAmount DESC LIMIT 10"

        sql = data["choices"][0]["message"]["content"]

        # Clean markdown fences
        sql = sql.replace("```sql", "").replace("```", "").strip()

        # Take only the SELECT line if LLM adds explanation
        lines = [l.strip() for l in sql.splitlines() if l.strip()]
        sql_lines = [l for l in lines if any(
            l.upper().startswith(k) for k in ["SELECT", "WITH"]
        )]
        if sql_lines:
            sql = " ".join(sql_lines)

        # Fix common column name quoting issues
        for col in ["billingDocument", "accountingDocument", "soldToParty", "totalNetAmount",
                    "salesOrder", "deliveryDocument", "paymentDocument", "businessPartner",
                    "businessPartnerName", "plant", "plantName", "product"]:
            sql = sql.replace(f'`{col}`', col).replace(f'"{col}"', col)

        if not sql.strip().upper().startswith("SELECT"):
            sql = "SELECT billingDocument, soldToParty, totalNetAmount FROM invoices ORDER BY totalNetAmount DESC LIMIT 10"

        print("✅ SQL:", sql)
        return sql

    except Exception as e:
        print("LLM ERROR:", e)
        return "SELECT billingDocument, soldToParty, totalNetAmount FROM invoices ORDER BY totalNetAmount DESC LIMIT 10"