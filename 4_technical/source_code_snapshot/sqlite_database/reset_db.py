import os
import sqlite3
from pathlib import Path

DB_PATH = Path("mydb.sqlite")
SCHEMA_PATH = Path("schema.sql")

def reset_database():
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")

    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Deleted existing database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn.executescript(schema_sql)
        conn.commit()
        print(f"Created fresh database from schema: {DB_PATH}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_database()