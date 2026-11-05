from db import get_admin_conn, get_readonly_conn, run_readonly_query
print("1) Read-only user can read:")
cols, rows, _ = run_readonly_query("SELECT COUNT(*) AS customers FROM customers")
print("  ", cols, rows)
print("2) Read-only user CANNOT delete (this should fail):")
conn = get_readonly_conn()
try:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM shop.customers")
    print("   PROBLEM: delete worked!")
except Exception as e:
    print("   Blocked as expected:", str(e).strip().splitlines()[0])
finally:
    conn.close()
print("3) Read-only user CANNOT read other schemas (this should fail):")
try:
    run_readonly_query("SELECT * FROM public.some_table")
    print("   PROBLEM: it worked!")
except Exception as e:
    print("   Blocked as expected:", str(e).strip().splitlines()[0])
print("4) Admin user sees the same data:")
conn = get_admin_conn()
with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM shop.orders")
    print("   orders:", cur.fetchone()[0])
conn.close()