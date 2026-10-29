import os
import pandas as pd
from db import get_connection, initialize_database

REQUIRED_COLUMNS = [
    "Transaction_Id", "Order_date", "Product", "Category", "Region",
    "Sales_channel", "Quantity", "Unit_price", "Discount_amount", "Status"
]

def load_csv(csv_path=None, db_path=None):
    csv_path = csv_path or os.getenv("CSV_PATH", "sales_data.csv")
    df = pd.read_csv(csv_path)
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

    df = df[REQUIRED_COLUMNS].copy()
    df["Order_date"] = pd.to_datetime(
        df["Order_date"], format="%d-%m-%Y", errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    for col in ["Quantity", "Unit_price", "Discount_amount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    records = []
    for _, row in df.iterrows():
        reasons = []
        if pd.isna(row["Order_date"]): reasons.append("invalid/missing order date")
        if pd.isna(row["Quantity"]) or row["Quantity"] <= 0: reasons.append("missing or non-positive quantity")
        if pd.isna(row["Unit_price"]) or row["Unit_price"] < 0: reasons.append("missing or negative unit price")
        if pd.isna(row["Discount_amount"]) or row["Discount_amount"] < 0: reasons.append("missing or negative discount")
        if str(row["Status"]).strip().lower() != "completed": reasons.append("transaction is not completed")
        if not str(row["Transaction_Id"]).strip(): reasons.append("missing transaction id")

        records.append((
            str(row["Transaction_Id"]).strip(),
            None if pd.isna(row["Order_date"]) else row["Order_date"],
            None if pd.isna(row["Product"]) else str(row["Product"]).strip(),
            None if pd.isna(row["Category"]) else str(row["Category"]).strip(),
            None if pd.isna(row["Region"]) else str(row["Region"]).strip(),
            None if pd.isna(row["Sales_channel"]) else str(row["Sales_channel"]).strip(),
            None if pd.isna(row["Quantity"]) else float(row["Quantity"]),
            None if pd.isna(row["Unit_price"]) else float(row["Unit_price"]),
            None if pd.isna(row["Discount_amount"]) else float(row["Discount_amount"]),
            str(row["Status"]).strip(),
            0 if reasons else 1,
            "; ".join(reasons) if reasons else None
        ))

    initialize_database(db_path)
    with get_connection(db_path) as conn:
        conn.executemany("""
            INSERT OR REPLACE INTO sales
            (transaction_id, order_date, product, category, region, sales_channel,
             quantity, unit_price, discount_amount, status, is_valid, exclusion_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, records)
        conn.commit()

    return {
        "loaded": len(records),
        "valid": sum(1 for r in records if r[10] == 1),
        "excluded": sum(1 for r in records if r[10] == 0)
    }
