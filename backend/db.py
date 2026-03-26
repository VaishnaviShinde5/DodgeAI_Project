import sqlite3

DB_PATH = "data.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
    DROP TABLE IF EXISTS invoices;
    DROP TABLE IF EXISTS sales_orders;
    DROP TABLE IF EXISTS deliveries;
    DROP TABLE IF EXISTS payments;
    DROP TABLE IF EXISTS journals;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS business_partners;
    DROP TABLE IF EXISTS plants;

    CREATE TABLE invoices (
        billingDocument TEXT,
        accountingDocument TEXT,
        soldToParty TEXT,
        totalNetAmount REAL,
        billingDocumentDate TEXT,
        billingDocumentType TEXT
    );

    CREATE TABLE sales_orders (
        salesOrder TEXT,
        soldToParty TEXT,
        salesOrderDate TEXT,
        netAmount REAL,
        salesOrderType TEXT,
        salesOrganization TEXT
    );

    CREATE TABLE deliveries (
        deliveryDocument TEXT,
        salesOrder TEXT,
        soldToParty TEXT,
        deliveryDate TEXT,
        shippingPoint TEXT,
        plant TEXT
    );

    CREATE TABLE payments (
        paymentDocument TEXT,
        accountingDocument TEXT,
        soldToParty TEXT,
        amountInCompanyCodeCurrency REAL,
        paymentDate TEXT,
        companyCode TEXT
    );

    CREATE TABLE journals (
        accountingDocument TEXT,
        billingDocument TEXT,
        companyCode TEXT,
        fiscalYear TEXT,
        postingDate TEXT,
        amountInCompanyCodeCurrency REAL
    );

    CREATE TABLE products (
        product TEXT,
        productType TEXT,
        baseUnit TEXT,
        productGroup TEXT,
        division TEXT
    );

    CREATE TABLE business_partners (
        businessPartner TEXT,
        businessPartnerName TEXT,
        businessPartnerType TEXT,
        country TEXT,
        city TEXT
    );

    CREATE TABLE plants (
        plant TEXT,
        plantName TEXT,
        country TEXT,
        city TEXT
    );
    """)

    conn.commit()
    conn.close()