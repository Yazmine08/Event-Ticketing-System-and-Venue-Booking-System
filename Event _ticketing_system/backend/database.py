"""
Database helper module for MySQL connection and queries.
Connects to XAMPP MySQL database 'event_ticketing_db'.
Enforces dictionary row conversion and serializes dates/times/decimals.
"""
import os
import decimal
import datetime
from typing import Generator, Any, Dict, List, Optional
import pymysql
import pymysql.cursors

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "event_ticketing_db")
DB_PORT = int(os.environ.get("DB_PORT", 3306))

def get_db_connection() -> pymysql.Connection:
    """Creates and returns an active PyMySQL connection with DictCursor."""
    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        charset="utf8mb4"
    )
    return conn

def get_db() -> Generator[pymysql.Connection, None, None]:
    """FastAPI dependency generator yielding an active database connection."""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

def serialize_value(val: Any) -> Any:
    """Converts MySQL-specific data types (Decimal, Date, Time, Timedelta, Datetime) to JSON-serializable types."""
    if isinstance(val, decimal.Decimal):
        return float(val)
    elif isinstance(val, datetime.datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(val, datetime.date):
        return val.strftime("%Y-%m-%d")
    elif isinstance(val, (datetime.time, datetime.timedelta)):
        return str(val)
    return val

def serialize_row(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Recursively serializes dictionary values from a MySQL DictCursor row."""
    if row is None:
        return None
    return {k: serialize_value(v) for k, v in row.items()}

def serialize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Serializes a list of dictionary rows."""
    return [serialize_row(r) for r in rows if r is not None]
