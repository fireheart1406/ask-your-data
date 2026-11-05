from psycopg2 import sql
from config import SCHEMA_NAME
from db import get_admin_conn
_cache = None
def get_schema_text(refresh=False):
    global _cache
    if _cache is None or refresh:
        _cache = _build_schema_text()
    return _cache
def _build_schema_text():
    conn = get_admin_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s
                ORDER BY table_name, ordinal_position
                """,
                (SCHEMA_NAME,),
            )
            columns = cur.fetchall()
            cur.execute(
                """
                SELECT cl.relname, pg_get_constraintdef(c.oid)
                FROM pg_constraint c
                JOIN pg_class cl ON cl.oid = c.conrelid
                JOIN pg_namespace n ON n.oid = cl.relnamespace
                WHERE n.nspname = %s AND c.contype IN ('p', 'f')
                ORDER BY cl.relname
                """,
                (SCHEMA_NAME,),
            )
            constraints = {}
            for table, definition in cur.fetchall():
                constraints.setdefault(table, []).append(definition)
            tables = {}
            for table, column, dtype in columns:
                tables.setdefault(table, []).append((column, dtype))
            lines = []
            for table, cols in tables.items():
                lines.append(f"Table {table}")
                for column, dtype in cols:
                    note = ""
                    if dtype in ("text", "character varying"):
                        query = sql.SQL(
                            "SELECT DISTINCT {c} FROM {s}.{t} WHERE {c} IS NOT NULL ORDER BY 1 LIMIT 13"
                        ).format(c=sql.Identifier(column), s=sql.Identifier(SCHEMA_NAME), t=sql.Identifier(table))
                        cur.execute(query)
                        values = [r[0] for r in cur.fetchall()]
                        if len(values) <= 12:
                            note = f"  allowed values: {values}"
                    lines.append(f"  - {column} ({dtype}){note}")
                for definition in constraints.get(table, []):
                    lines.append(f"  {definition}")
                lines.append("")
            return "\n".join(lines)
    finally:
        conn.close()    
if __name__ == "__main__":
    print(get_schema_text())