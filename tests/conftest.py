import pytest
from data_loader import load_csv

@pytest.fixture
def test_db(tmp_path):
    import os
    source = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sales_data.csv")
    db = str(tmp_path / "test_sales.db")
    stats = load_csv(source, db)
    return db, stats
