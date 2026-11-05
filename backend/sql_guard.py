import sqlglot
from sqlglot import exp
from config import SCHEMA_NAME
class UnsafeSQLError(Exception):
    """Raised when a query is not allowed to run."""
_FORBIDDEN_NAMES = [
    "Insert", "Update", "Delete", "Drop", "Create", "Alter", "AlterTable",
    "Command", "Merge", "Into", "TruncateTable", "Grant", "Set", "Copy",
]
FORBIDDEN_NODES = tuple(getattr(exp, n) for n in _FORBIDDEN_NAMES if hasattr(exp, n))
BLOCKED_FUNCTIONS = {
    "pg_sleep", "pg_sleep_for", "pg_sleep_until", "pg_read_file", "pg_read_binary_file",
    "pg_ls_dir", "pg_stat_file", "set_config", "current_setting", "dblink",
    "lo_import", "lo_export", "pg_terminate_backend", "pg_cancel_backend",
    "query_to_xml", "txid_current",
}
def _function_name(node):
    if isinstance(node, exp.Anonymous):
        return str(node.name).lower()
    return str(node.sql_name()).lower()
def validate_sql(sql: str) -> str:
    """Returns a safe version of the query, or raises UnsafeSQLError."""
    sql = (sql or "").strip().rstrip(";").strip()
    if not sql:
        raise UnsafeSQLError("The query is empty.")
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.SqlglotError as e:
        raise UnsafeSQLError(f"The query could not be parsed: {e}")
    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        raise UnsafeSQLError("Only a single SQL statement is allowed.")
    stmt = statements[0]
    if not isinstance(stmt, (exp.Select, exp.Union)):
        raise UnsafeSQLError("Only SELECT queries are allowed.")
    for node in stmt.find_all(exp.Expression):
        if isinstance(node, FORBIDDEN_NODES):
            raise UnsafeSQLError(f"Not allowed: {type(node).__name__} operations.")
    for table in stmt.find_all(exp.Table):
        schema = (table.db or "").lower()
        name = (table.name or "").lower()
        if schema and schema != SCHEMA_NAME:
            raise UnsafeSQLError(f"Not allowed to read from schema '{schema}'.")
        if name.startswith("pg_") or name == "information_schema":
            raise UnsafeSQLError(f"Not allowed to read system table '{name}'.")
    for func in stmt.find_all(exp.Func):
        if _function_name(func) in BLOCKED_FUNCTIONS:
            raise UnsafeSQLError(f"The function '{_function_name(func)}' is not allowed.")
    return stmt.sql(dialect="postgres")