"""
Database Setup & Reset Script
Executes ddl.sql and dml.sql directly against the MySQL database.
Course: SWC3633 / SWC4443 Web API Development
"""
import os
import sys
import pymysql

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_NAME = "event_ticketing_db"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DDL_PATH = os.path.join(CURRENT_DIR, "ddl.sql")
DML_PATH = os.path.join(CURRENT_DIR, "dml.sql")

def execute_sql_file(cursor, file_path):
    print(f"[+] Executing: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()

    # Split statements safely by semicolon
    statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
    for stmt in statements:
        if stmt.startswith("--") or stmt.startswith("/*"):
            # Skip pure comment blocks
            lines = [l for l in stmt.splitlines() if not l.strip().startswith("--") and not l.strip().startswith("/*")]
            stmt = "\n".join(lines).strip()
            if not stmt:
                continue
        cursor.execute(stmt)

def main():
    print("======================================================================")
    print("  Event Ticketing Database Setup / Reset Utility")
    print(f"  Target: {DB_HOST}:{DB_PORT} (DB: {DB_NAME})")
    print("======================================================================")

    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            autocommit=True,
            charset="utf8mb4"
        )
        cursor = conn.cursor()
        print("[+] Connected to MySQL Server.")

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4;")
        cursor.execute(f"USE `{DB_NAME}`;")

        if os.path.exists(DDL_PATH):
            execute_sql_file(cursor, DDL_PATH)
            print("[OK] DDL tables created successfully.")
        else:
            print(f"[!] Warning: {DDL_PATH} not found.")

        if os.path.exists(DML_PATH):
            execute_sql_file(cursor, DML_PATH)
            print("[OK] DML sample data seeded successfully.")
        else:
            print(f"[!] Warning: {DML_PATH} not found.")

        conn.close()
        print("======================================================================")
        print("  Database Setup Complete! Ready for API execution.")
        print("======================================================================")
    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
