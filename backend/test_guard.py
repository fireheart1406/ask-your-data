from sql_guard import validate_sql, UnsafeSQLError
SHOULD_PASS = [
    "SELECT COUNT(*) FROM customers",
    "SELECT status, COUNT(*) FROM orders GROUP BY status",
    "WITH t AS (SELECT customer_id FROM orders) SELECT COUNT(*) FROM t",
]
SHOULD_FAIL = [
    "DROP TABLE customers",
    "SELECT 1; DELETE FROM orders",
    "UPDATE customers SET city = 'x'",
    "SELECT pg_sleep(10)",
    "SELECT * FROM pg_catalog.pg_tables",
    "SELECT * FROM information_schema.tables",
    "SELECT * FROM auth.users",
    "INSERT INTO customers VALUES (1)",
]
bad = 0
for q in SHOULD_PASS:
    try:
        validate_sql(q)
        print("PASS  allowed:", q)
    except UnsafeSQLError as e:
        bad += 1
        print("FAIL  wrongly blocked:", q, "->", e)
for q in SHOULD_FAIL:
    try:
        validate_sql(q)
        bad += 1
        print("FAIL  wrongly allowed:", q)
    except UnsafeSQLError as e:
        print("PASS  blocked:", q, "->", e)
print("\nAll good!" if bad == 0 else f"\n{bad} problem(s) found.")