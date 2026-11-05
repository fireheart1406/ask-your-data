import random
from datetime import date, timedelta
from faker import Faker
from psycopg2.extras import execute_values
from db import get_admin_conn
random.seed(42) #seeds are fixed getting the same data every time
Faker.seed(42)
fake = Faker("en_IN")
NUM_CUSTOMERS = 600
NUM_ORDERS = 4000
SIGNUP_START = date(2024, 6, 1)
SIGNUP_END = date(2026, 9, 30)
DATA_END = date(2026, 10, 31)
CITIES = [
    ("Mumbai", "Maharashtra"), ("Pune", "Maharashtra"), ("Delhi", "Delhi"),
    ("Bengaluru", "Karnataka"), ("Chennai", "Tamil Nadu"), ("Hyderabad", "Telangana"),
    ("Kolkata", "West Bengal"), ("Ahmedabad", "Gujarat"), ("Jaipur", "Rajasthan"),
    ("Lucknow", "Uttar Pradesh"),
]
CITY_WEIGHTS = [14, 8, 13, 13, 10, 10, 9, 8, 8, 7]
PRODUCTS = [
    ("Wireless Earbuds", "Electronics", 2499), ("Bluetooth Speaker", "Electronics", 1799),
    ("Smartwatch", "Electronics", 4999), ("Power Bank", "Electronics", 1299),
    ("USB-C Hub", "Electronics", 1549), ("Webcam", "Electronics", 2199),
    ("Cotton T-Shirt", "Clothing", 599), ("Denim Jeans", "Clothing", 1399),
    ("Hoodie", "Clothing", 1899), ("Formal Shirt", "Clothing", 1199),
    ("Winter Jacket", "Clothing", 3299), ("Track Pants", "Clothing", 799),
    ("Air Fryer", "Home & Kitchen", 4299), ("Non-stick Pan Set", "Home & Kitchen", 1749),
    ("Mixer Grinder", "Home & Kitchen", 2899), ("Water Bottle", "Home & Kitchen", 449),
    ("Bedsheet Set", "Home & Kitchen", 1649), ("Table Lamp", "Home & Kitchen", 999),
    ("Python Programming Guide", "Books", 699), ("Data Structures Handbook", "Books", 849),
    ("Fiction Bestseller", "Books", 399), ("Self-Help Paperback", "Books", 349),
    ("Algorithms Illustrated", "Books", 949), ("History of India", "Books", 549),
    ("Yoga Mat", "Sports", 899), ("Badminton Racket", "Sports", 1999),
    ("Cricket Bat", "Sports", 3499), ("Dumbbell Set", "Sports", 2599),
    ("Football", "Sports", 749), ("Running Shoes", "Sports", 3999),
    ("Face Wash", "Beauty", 249), ("Moisturizer", "Beauty", 579),
    ("Sunscreen", "Beauty", 429), ("Perfume", "Beauty", 2299),
    ("Shampoo", "Beauty", 379), ("Hair Dryer", "Beauty", 1499),
]
STATUSES = ["delivered", "shipped", "cancelled", "returned"]
STATUS_WEIGHTS = [70, 10, 12, 8]
PAYMENTS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash on Delivery"]
PAYMENT_WEIGHTS = [45, 20, 15, 10, 10]
DDL = """
DROP SCHEMA IF EXISTS shop CASCADE;
CREATE SCHEMA shop;
CREATE TABLE shop.customers (
    customer_id INTEGER PRIMARY KEY,
    full_name   TEXT NOT NULL,
    email       TEXT NOT NULL,
    city        TEXT NOT NULL,
    state       TEXT NOT NULL,
    signup_date DATE NOT NULL
);
CREATE TABLE shop.products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category     TEXT NOT NULL,
    unit_price   NUMERIC(10,2) NOT NULL
);
CREATE TABLE shop.orders (
    order_id       INTEGER PRIMARY KEY,
    customer_id    INTEGER NOT NULL REFERENCES shop.customers(customer_id),
    order_date     DATE NOT NULL,
    status         TEXT NOT NULL,
    payment_method TEXT NOT NULL
);
CREATE TABLE shop.order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id      INTEGER NOT NULL REFERENCES shop.orders(order_id),
    product_id    INTEGER NOT NULL REFERENCES shop.products(product_id),
    quantity      INTEGER NOT NULL,
    unit_price    NUMERIC(10,2) NOT NULL
);
"""
GRANTS = """
GRANT USAGE ON SCHEMA shop TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA shop TO readonly_user;
"""
def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))
def build_customers():
    rows = []
    for cid in range(1, NUM_CUSTOMERS + 1):
        first, last = fake.first_name(), fake.last_name()
        city, state = random.choices(CITIES, weights=CITY_WEIGHTS)[0]
        email = f"{first.lower()}.{last.lower()}{cid}@example.com"
        rows.append((cid, f"{first} {last}", email, city, state, random_date(SIGNUP_START, SIGNUP_END)))
    return rows
def build_products():
    return [(i, name, cat, price) for i, (name, cat, price) in enumerate(PRODUCTS, start=1)]
def build_orders_and_items(customers, products):
    weights = [random.expovariate(1.0) for _ in customers]
    orders, items = [], []
    item_id = 1
    for oid in range(1, NUM_ORDERS + 1):
        cust = random.choices(customers, weights=weights)[0]
        order_date = random_date(cust[5], DATA_END)   
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
        payment = random.choices(PAYMENTS, weights=PAYMENT_WEIGHTS)[0]
        orders.append((oid, cust[0], order_date, status, payment))
        how_many = random.choices([1, 2, 3, 4], weights=[45, 30, 15, 10])[0]
        for prod in random.sample(products, how_many):
            qty = random.choices([1, 2, 3], weights=[70, 22, 8])[0]
            items.append((item_id, oid, prod[0], qty, prod[3]))
            item_id += 1
    return orders, items
def main():
    customers = build_customers()
    products = build_products()
    orders, items = build_orders_and_items(customers, products)
    conn = get_admin_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(DDL)
            execute_values(cur, "INSERT INTO shop.customers VALUES %s", customers, page_size=1000)
            execute_values(cur, "INSERT INTO shop.products VALUES %s", products, page_size=1000)
            execute_values(cur, "INSERT INTO shop.orders VALUES %s", orders, page_size=1000)
            execute_values(cur, "INSERT INTO shop.order_items VALUES %s", items, page_size=1000)
            cur.execute(GRANTS)
        conn.commit()
    finally:
        conn.close()
    print(f"customers: {len(customers)}, products: {len(products)}, "
          f"orders: {len(orders)}, order_items: {len(items)}")
if __name__ == "__main__":
    main()