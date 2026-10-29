import os
import sqlite3
from pathlib import Path

DB_PATH = os.getenv("DATABASE_PATH", "sales.db")

def get_connection(db_path=None):
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database(db_path=None):
    with get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                transaction_id TEXT PRIMARY KEY,
                order_date TEXT,
                product TEXT,
                category TEXT,
                region TEXT,
                sales_channel TEXT,
                quantity REAL,
                unit_price REAL,
                discount_amount REAL,
                status TEXT,
                is_valid INTEGER NOT NULL,
                exclusion_reason TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(order_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_region ON sales(region)")
        conn.commit()
