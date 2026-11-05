from datetime import date, datetime
from decimal import Decimal
import psycopg2
from sqlglot.errors import SqlglotError
from config import MAX_RETRIES
from db import run_readonly_query
from llm import fix_sql, generate_sql
from schema_reader import get_schema_text
from sql_guard import UnsafeSQLError, validate_sql
def _jsonable(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value
def ask(question, max_retries=MAX_RETRIES):
    schema = get_schema_text()
    attempts = []
    sql = generate_sql(question, schema)
    for attempt_number in range(1, max_retries + 2):   
        try:
            safe_sql = validate_sql(sql)
            columns, rows, truncated = run_readonly_query(safe_sql)
            attempts.append({"sql": sql, "error": None})
            return {
                "question": question,
                "ok": True,
                "sql": safe_sql,
                "columns": columns,
                "rows": [[_jsonable(v) for v in row] for row in rows],
                "row_count": len(rows),
                "truncated": truncated,
                "attempts": attempts,
                "attempt_count": len(attempts),
                "error": None,
            }
        except (UnsafeSQLError, SqlglotError, psycopg2.Error) as e:
            error_text = str(e).strip()[:500]
            attempts.append({"sql": sql, "error": error_text})
            if attempt_number > max_retries:
                break
            sql = fix_sql(question, schema, sql, error_text)
    return {
        "question": question,
        "ok": False,
        "sql": attempts[-1]["sql"],
        "columns": [],
        "rows": [],
        "row_count": 0,
        "truncated": False,
        "attempts": attempts,
        "attempt_count": len(attempts),
        "error": attempts[-1]["error"],
    }