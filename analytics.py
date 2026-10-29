from db import get_connection

VALID_WHERE = """
    WHERE is_valid = 1
      AND status = 'Completed'
      AND order_date IS NOT NULL
      AND quantity > 0
      AND unit_price IS NOT NULL
"""

def _month_label(month):
    import calendar
    return calendar.month_name[month]

def answer_question(question, parsed, parser_mode="rule-based fallback", db_path=None):
    intent = parsed.get("intent")
    year = parsed.get("year", 2026)
    months = parsed.get("months", [])

    with get_connection(db_path) as conn:
        if intent == "total_revenue":
            row = conn.execute(f"""
                SELECT ROUND(SUM(quantity * unit_price - discount_amount), 2) AS revenue,
                       COUNT(*) AS transactions
                FROM sales {VALID_WHERE}
            """).fetchone()
            value = float(row["revenue"] or 0)
            return _result("Total revenue", f"Total revenue is ₹{value:,.2f}.",
                           {"total_revenue": value, "valid_transactions": row["transactions"]},
                           "SUM(quantity * unit_price - discount_amount)", parser_mode)

        if intent == "top_product":
            rows = conn.execute(f"""
                SELECT product, ROUND(SUM(quantity * unit_price - discount_amount), 2) AS revenue
                FROM sales {VALID_WHERE}
                GROUP BY product ORDER BY revenue DESC
            """).fetchall()
            if not rows: return _empty(parser_mode)
            top = rows[0]
            return _result("Highest revenue product",
                f"{top['product']} generated the highest revenue: ₹{top['revenue']:,.2f}.",
                {"top_product": dict(top), "product_revenue": [dict(r) for r in rows]},
                "GROUP BY product; ORDER BY SUM(revenue) DESC", parser_mode)

        if intent == "top_region":
            rows = conn.execute(f"""
                SELECT region, ROUND(SUM(quantity * unit_price - discount_amount), 2) AS revenue
                FROM sales {VALID_WHERE}
                GROUP BY region ORDER BY revenue DESC
            """).fetchall()
            if not rows: return _empty(parser_mode)
            top = rows[0]
            return _result("Highest sales region",
                f"{top['region']} generated the highest sales revenue: ₹{top['revenue']:,.2f}.",
                {"top_region": dict(top), "region_revenue": [dict(r) for r in rows]},
                "GROUP BY region; ORDER BY SUM(revenue) DESC", parser_mode)

        if intent == "monthly_trend":
            rows = conn.execute(f"""
                SELECT substr(order_date, 1, 7) AS month,
                       ROUND(SUM(quantity * unit_price - discount_amount), 2) AS revenue
                FROM sales {VALID_WHERE}
                AND substr(order_date, 1, 4) = ?
                GROUP BY substr(order_date, 1, 7) ORDER BY month
            """, (str(year),)).fetchall()
            data = [dict(r) for r in rows]
            return _result("Monthly revenue trend", f"Monthly revenue trend for {year} is ready.",
                           {"monthly_revenue": data, "year": year},
                           "GROUP BY year-month; ORDER BY year-month", parser_mode)

        if intent == "compare_months":
            if len(months) < 2:
                return {"success": False, "error": "Please mention two months, for example: Compare January and February revenue."}
            values = []
            for month in months[:2]:
                month_key = f"{year}-{month:02d}"
                row = conn.execute(f"""
                    SELECT ROUND(SUM(quantity * unit_price - discount_amount), 2) AS revenue,
                           COUNT(*) AS transactions
                    FROM sales {VALID_WHERE}
                    AND substr(order_date, 1, 7) = ?
                """, (month_key,)).fetchone()
                values.append({"month": _month_label(month), "month_number": month,
                               "revenue": float(row["revenue"] or 0),
                               "transactions": row["transactions"]})
            difference = values[1]["revenue"] - values[0]["revenue"]
            pct = (difference / values[0]["revenue"] * 100) if values[0]["revenue"] else None
            direction = "increased" if difference > 0 else "decreased" if difference < 0 else "did not change"
            pct_text = f" ({abs(pct):.2f}%)" if pct is not None else ""
            return _result("Month-to-month comparison",
                f"Revenue {direction} by ₹{abs(difference):,.2f}{pct_text} from {values[0]['month']} to {values[1]['month']}.",
                {"comparison": values, "difference": difference, "percentage_change": pct},
                "Two parameterized monthly SUM queries", parser_mode)

    return {"success": False, "error": "I couldn't understand that question. Try asking about total revenue, top product, monthly trend, top region, or comparing two months."}

def _result(title, answer, supporting_data, calculation, parser_mode):
    return {"success": True, "title": title, "answer": answer,
            "supporting_data": supporting_data, "calculation": calculation,
            "question_interpreter": parser_mode}

def _empty(parser_mode):
    return _result("No data", "No valid completed transactions were found for this question.",
                   {}, "SQL aggregation", parser_mode)
