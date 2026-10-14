import os
import pytest
import tempfile
from datetime import date
from app.parsers.generic_csv import GenericCSVParser
from app.parsers import get_parser


@pytest.fixture
def sample_csv_path():
    fixture_path = os.path.join(os.path.dirname(__file__), "fixtures", "generic_sample.csv")
    return fixture_path


def test_generic_csv_parser_can_parse(sample_csv_path):
    parser = GenericCSVParser()
    assert parser.can_parse(sample_csv_path) is True
    assert parser.can_parse("non_existent_file.csv") is False
    assert parser.can_parse(os.path.join(os.path.dirname(__file__), "test_health.py")) is False


def test_parser_registry(sample_csv_path):
    parser = get_parser(sample_csv_path)
    assert isinstance(parser, GenericCSVParser)


def test_generic_csv_parse_fixture(sample_csv_path):
    parser = GenericCSVParser()
    txns = parser.parse(sample_csv_path)
    assert len(txns) == 22

    # Verify canonical schema shape
    first_txn = txns[0]
    assert "date" in first_txn
    assert isinstance(first_txn["date"], date)
    assert "description_raw" in first_txn
    assert "amount" in first_txn
    assert "type" in first_txn
    assert "balance" in first_txn

    # First txn should be salary credit (85000.0)
    salary_txn = [t for t in txns if "SALARY" in t["description_raw"]][0]
    assert salary_txn["type"] == "credit"
    assert salary_txn["amount"] == 85000.0

    # Debit transaction (Swiggy)
    swiggy_txn = [t for t in txns if "SWIGGY" in t["description_raw"]][0]
    assert swiggy_txn["type"] == "debit"
    assert swiggy_txn["amount"] == -450.0


def test_single_amount_column_csv():
    content = """Txn Date,Description,Amount,Balance
01-05-2024,SALARY CREDIT,50000,60000
02-05-2024,UBER RIDE,-350,59650
03-05-2024,ZOMATO FOOD,450 Dr,59200
"""
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        parser = GenericCSVParser()
        assert parser.can_parse(temp_path) is True
        txns = parser.parse(temp_path)
        assert len(txns) == 3
        assert txns[0]["amount"] == 50000.0
        assert txns[0]["type"] == "credit"
        assert txns[1]["amount"] == -350.0
        assert txns[1]["type"] == "debit"
        assert txns[2]["amount"] == -450.0
        assert txns[2]["type"] == "debit"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_empty_csv_raises_error():
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write("")
        temp_path = f.name

    try:
        parser = GenericCSVParser()
        with pytest.raises(ValueError):
            parser.parse(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
