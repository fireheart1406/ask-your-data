import re
import time
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL
_client = None
def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client
SYSTEM_PROMPT = """You are an expert PostgreSQL data analyst. You turn questions into SQL.
Rules:
1. Write exactly ONE read-only PostgreSQL SELECT query (CTEs are allowed).
2. Use only the tables and columns in the schema you are given.
3. Use table names without a schema prefix (write customers, not shop.customers).
4. Return ONLY the SQL. No explanation and no markdown fences.
5. Give result columns short readable aliases.
6. For "top N" questions, ORDER BY the right column and LIMIT N.
7. Only return the columns the question asks for. Do not add extra columns.
8. When the question asks for a rounded number, use ROUND(value, 2) on a numeric value.
Business definitions:
- Anything about sales, "sold", revenue, spend, or order value is calculated from
  order_items as quantity * unit_price, and EXCLUDES orders whose status is 'cancelled',
  unless the question says otherwise.
- "Order value" means the total of all items in one order.
- Questions about "placing" or "ordering" count every order regardless of status.
- When a question names a year or month, filter with EXTRACT(YEAR FROM ...) / EXTRACT(MONTH FROM ...).
  Month numbers are 1 to 12.
If the question cannot be answered from this schema, return exactly:
SELECT 'This cannot be answered from the available data' AS message
"""
def _clean_sql(text):
    text = (text or "").strip()
    text = re.sub(r"^```(?:sql)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()
def _call_model(contents):
    last_error = None
    for attempt in range(4):
        try:
            response = _get_client().models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0,
                ),
            )
            return response.text or ""
        except Exception as e:
            last_error = e
            message = str(e)
            # Rate limit or temporary overload: wait and try again.
            if "429" in message or "RESOURCE_EXHAUSTED" in message or "503" in message:
                time.sleep(6 * (attempt + 1))
                continue
            raise
    raise last_error
def generate_sql(question, schema_text):
    contents = (
        f"DATABASE SCHEMA:\n{schema_text}\n\n"
        f"QUESTION: {question}\n\n"
        "SQL:"
    )
    return _clean_sql(_call_model(contents))
def fix_sql(question, schema_text, bad_sql, error_message):
    contents = (
        f"DATABASE SCHEMA:\n{schema_text}\n\n"
        f"QUESTION: {question}\n\n"
        f"You wrote this SQL:\n{bad_sql}\n\n"
        f"It failed with this error:\n{error_message}\n\n"
        "Write a corrected SQL query. Return ONLY the SQL."
    )
    return _clean_sql(_call_model(contents))