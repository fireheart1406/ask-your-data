import os
from dotenv import load_dotenv
load_dotenv()
REQUIRED = [
    "GEMINI_API_KEY", "DB_HOST", "DB_PORT", "DB_NAME",
    "ADMIN_USER", "ADMIN_PASSWORD", "READONLY_USER", "READONLY_PASSWORD",
]
missing = [name for name in REQUIRED if not os.getenv(name)]
if missing:
    raise RuntimeError(f"Missing values in .env: {', '.join(missing)}")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "postgres")
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
READONLY_USER = os.getenv("READONLY_USER")
READONLY_PASSWORD = os.getenv("READONLY_PASSWORD")
SCHEMA_NAME = "shop"                                   # the scheme that the AI is allowed to see
MAX_ROWS = int(os.getenv("MAX_ROWS", "500"))           
QUERY_TIMEOUT_MS = int(os.getenv("QUERY_TIMEOUT_MS", "5000"))   #keeping it 5 secs
MAX_RETRIES = 2                                        