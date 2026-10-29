from question_parser import rule_based_parse
from analytics import answer_question

def ask(q, db):
    parsed = rule_based_parse(q)
    return answer_question(q, parsed, db_path=db)

def test_total_revenue(test_db):
    db, stats = test_db
    result = ask("What is the total revenue?", db)
    assert result["success"] is True
    assert result["supporting_data"]["total_revenue"] == 1439200.0
    assert result["supporting_data"]["valid_transactions"] == 48

def test_top_product(test_db):
    db, _ = test_db
    result = ask("Which product generated the highest revenue?", db)
    assert result["supporting_data"]["top_product"]["product"] == "Monitor"

def test_monthly_trend(test_db):
    db, _ = test_db
    result = ask("Show monthly revenue trend", db)
    assert len(result["supporting_data"]["monthly_revenue"]) == 6
    assert result["supporting_data"]["monthly_revenue"][0]["revenue"] == 210250.0

def test_top_region(test_db):
    db, _ = test_db
    result = ask("Which region generated the highest sales?", db)
    assert result["supporting_data"]["top_region"]["region"] == "South"

def test_month_comparison(test_db):
    db, _ = test_db
    result = ask("Compare January and February revenue", db)
    assert result["supporting_data"]["difference"] == 24350.0
    assert round(result["supporting_data"]["percentage_change"], 2) == 11.58

def test_invalid_question_is_unsupported(test_db):
    db, _ = test_db
    parsed = rule_based_parse("Tell me a joke")
    assert parsed["intent"] == "unsupported"
    response = answer_question("Tell me a joke", parsed, db_path=db)
    assert response["success"] is False

def test_invalid_rows_are_excluded(test_db):
    db, stats = test_db
    assert stats == {"loaded": 51, "valid": 48, "excluded": 3}
