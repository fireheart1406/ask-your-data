import psycopg2
from config import (
    DB_HOST, DB_PORT, DB_NAME,
    ADMIN_USER, ADMIN_PASSWORD, READONLY_USER, READONLY_PASSWORD,
    SCHEMA_NAME, QUERY_TIMEOUT_MS, MAX_ROWS,
)
def _connect(user, password):
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=user, password=password,
        sslmode="require", connect_timeout=10,
    )
def get_admin_conn():
    """Used only by our own code (seeding, reading the schema). Never for AI-written SQL."""
    return _connect(ADMIN_USER, ADMIN_PASSWORD)
def get_readonly_conn():
    return _connect(READONLY_USER, READONLY_PASSWORD)
def run_readonly_query(query):
    """Runs one query as the read-only user. Returns (columns, rows, truncated)."""
    conn = get_readonly_conn()
    try:
        conn.set_session(readonly=True)            
        with conn.cursor() as cur:
            cur.execute(f"SET statement_timeout = {int(QUERY_TIMEOUT_MS)}")   
            cur.execute(f"SET search_path TO {SCHEMA_NAME}")
            cur.execute(query)
            if cur.description is None:
                return [], [], False
            columns = [d[0] for d in cur.description]
            rows = cur.fetchmany(MAX_ROWS + 1)    
        truncated = len(rows) > MAX_ROWS
        return columns, rows[:MAX_ROWS], truncated
    finally:
        conn.close()