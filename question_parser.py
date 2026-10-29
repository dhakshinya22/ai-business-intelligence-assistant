import json
import os
import re
from datetime import datetime

ALLOWED_INTENTS = {
    "total_revenue", "top_product", "monthly_trend", "top_region", "compare_months"
}
MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6,
    "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11,
    "december": 12, "dec": 12
}

def _extract_months(question):
    q = question.lower()
    found = []
    for name, number in MONTHS.items():
        if re.search(rf"\b{name}\b", q) and number not in found:
            found.append(number)
    # Preserve chronological order for comparison.
    return sorted(found)

def rule_based_parse(question):
    q = question.lower().strip()
    months = _extract_months(q)
    if any(w in q for w in ["compare", "change", "difference", "increased", "decreased", "between"]) and len(months) >= 2:
        return {"intent": "compare_months", "months": months[:2], "year": 2026}
    if any(w in q for w in ["trend", "monthly", "month-wise", "month wise"]):
        return {"intent": "monthly_trend", "months": [], "year": 2026}
    if any(w in q for w in ["region", "state", "area"]) and any(w in q for w in ["highest", "top", "best", "sales", "revenue"]):
        return {"intent": "top_region", "months": [], "year": 2026}
    if any(w in q for w in ["product", "item"]) and any(w in q for w in ["highest", "top", "best", "revenue", "sales"]):
        return {"intent": "top_product", "months": [], "year": 2026}
    if any(w in q for w in ["total", "overall", "revenue", "sales"]):
        return {"intent": "total_revenue", "months": [], "year": 2026}
    return {"intent": "unsupported", "months": [], "year": 2026}

def parse_question(question):
    """Use an LLM to classify intent when configured; otherwise use a deterministic parser."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return rule_based_parse(question), "rule-based fallback"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content":
                 "Classify a sales analytics question. Return JSON with keys intent, months, year. "
                 "Allowed intents: total_revenue, top_product, monthly_trend, top_region, "
                 "compare_months, unsupported. months must be an array of month numbers 1-12. "
                 "Use year 2026 unless another year is explicitly stated. Never write SQL."},
                {"role": "user", "content": question}
            ],
            temperature=0
        )
        parsed = json.loads(response.choices[0].message.content)
        intent = parsed.get("intent")
        months = parsed.get("months", [])
        year = parsed.get("year", 2026)
        if intent not in ALLOWED_INTENTS:
            return {"intent": "unsupported", "months": [], "year": 2026}, "LLM (rejected unsupported intent)"
        if not isinstance(months, list) or any(not isinstance(m, int) or m < 1 or m > 12 for m in months):
            return rule_based_parse(question), "rule-based fallback (invalid LLM month values)"
        if intent == "compare_months" and len(months) < 2:
            return rule_based_parse(question), "rule-based fallback (two months required)"
        if not isinstance(year, int) or year < 2000 or year > 2100:
            year = 2026
        return {"intent": intent, "months": months[:2], "year": year}, "LLM"
    except Exception:
        return rule_based_parse(question), "rule-based fallback (LLM unavailable)"
