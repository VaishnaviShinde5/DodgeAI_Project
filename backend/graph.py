import networkx as nx

G = nx.DiGraph()

def build_graph(data_map):
    G.clear()

    invoices     = data_map.get("invoices", [])
    sales_orders = data_map.get("sales_orders", [])
    deliveries   = data_map.get("deliveries", [])
    payments     = data_map.get("payments", [])
    journals     = data_map.get("journals", [])

    # Sales Orders → Customers
    for so in sales_orders:
        so_id = so.get("salesOrder")
        if not so_id:
            continue
        so_node = f"order_{so_id}"
        G.add_node(so_node, type="sales_order", **{k: v for k, v in so.items() if isinstance(v, (str, int, float))})

        cust = so.get("soldToParty")
        if cust:
            cust_node = f"customer_{cust}"
            G.add_node(cust_node, type="customer")
            G.add_edge(cust_node, so_node, relation="placed")

    # Deliveries → Sales Orders
    for dv in deliveries:
        dv_id = dv.get("deliveryDocument")
        so_id = dv.get("salesOrder")
        if not dv_id:
            continue
        dv_node = f"delivery_{dv_id}"
        G.add_node(dv_node, type="delivery", **{k: v for k, v in dv.items() if isinstance(v, (str, int, float))})

        if so_id:
            so_node = f"order_{so_id}"
            if so_node not in G:
                G.add_node(so_node, type="sales_order")
            G.add_edge(so_node, dv_node, relation="delivered_via")

    # Invoices → Deliveries + Customers + Journals
    for inv in invoices:
        inv_id = inv.get("billingDocument")
        if not inv_id:
            continue
        inv_node = f"invoice_{inv_id}"
        G.add_node(inv_node, type="invoice", **{k: v for k, v in inv.items() if isinstance(v, (str, int, float))})

        cust = inv.get("soldToParty")
        if cust:
            cust_node = f"customer_{cust}"
            if cust_node not in G:
                G.add_node(cust_node, type="customer")
            G.add_edge(cust_node, inv_node, relation="billed")

        acc = inv.get("accountingDocument")
        if acc:
            journal_node = f"journal_{acc}"
            G.add_node(journal_node, type="journal")
            G.add_edge(inv_node, journal_node, relation="accounted")

    # Payments → Journals
    for pay in payments:
        acc = pay.get("accountingDocument")
        clearing = pay.get("clearingAccountingDocument") or pay.get("paymentDocument")
        if not acc:
            continue
        pay_node = f"payment_{acc}"
        G.add_node(pay_node, type="payment")

        journal_node = f"journal_{acc}"
        if journal_node in G:
            G.add_edge(journal_node, pay_node, relation="settled_by")

    print(f"📊 Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")