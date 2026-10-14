from datetime import date
from app.pipeline.categorizer import categorize_transactions
from app.models.schemas import CategoryEnum


def test_categorize_transactions_rules_and_merchants():
    txns = [
        {
            "date": date(2024, 5, 1),
            "description_raw": "NEFT CR-INFOSYS LTD-SALARY",
            "description_clean": "INFOSYS LTD SALARY",
            "amount": 75000.0,
            "type": "credit",
        },
        {
            "date": date(2024, 5, 2),
            "description_raw": "UPI/DR/123/RENT/nobroker",
            "description_clean": "RENT NOBROKER",
            "amount": -22000.0,
            "type": "debit",
        },
        {
            "date": date(2024, 5, 3),
            "description_raw": "ACH/HOME LOAN EMI/BAJAJ FINSERV",
            "description_clean": "HOME LOAN EMI BAJAJ FINSERV",
            "amount": -18500.0,
            "type": "debit",
        },
        {
            "date": date(2024, 5, 4),
            "description_raw": "ACH/SIP/ZERODHA BROKING",
            "description_clean": "SIP ZERODHA BROKING",
            "amount": -10000.0,
            "type": "debit",
        },
        {
            "date": date(2024, 5, 5),
            "description_raw": "UPI/DR/123/SWIGGY",
            "description_clean": "SWIGGY BANGALORE",
            "amount": -450.0,
            "type": "debit",
        },
        {
            "date": date(2024, 5, 6),
            "description_raw": "UPI/DR/123/UBER",
            "description_clean": "UBER INDIA",
            "amount": -320.0,
            "type": "debit",
        },
        {
            "date": date(2024, 5, 7),
            "description_raw": "AMAZON PAY INDIA",
            "description_clean": "AMAZON PAY INDIA",
            "amount": -1200.0,
            "type": "debit",
        },
        {
            "date": date(2024, 5, 8),
            "description_raw": "NETFLIX ENTERTAINMENT",
            "description_clean": "NETFLIX ENTERTAINMENT",
            "amount": -649.0,
            "type": "debit",
        },
        {
            "date": date(2024, 5, 9),
            "description_raw": "BESCOM ELECTRICITY BILL",
            "description_clean": "BESCOM ELECTRICITY BILL",
            "amount": -1400.0,
            "type": "debit",
        },
        {
            "date": date(2024, 5, 10),
            "description_raw": "SOME UNKNOWN STORE XYZ",
            "description_clean": "SOME UNKNOWN STORE XYZ",
            "amount": -100.0,
            "type": "debit",
        },
    ]

    categorized = categorize_transactions(txns)
    cat_map = {t["description_raw"]: (t["category"], t["category_confidence"]) for t in categorized}

    assert cat_map["NEFT CR-INFOSYS LTD-SALARY"][0] == CategoryEnum.SALARY.value
    assert cat_map["NEFT CR-INFOSYS LTD-SALARY"][1] >= 0.90

    assert cat_map["UPI/DR/123/RENT/nobroker"][0] == CategoryEnum.RENT.value
    assert cat_map["ACH/HOME LOAN EMI/BAJAJ FINSERV"][0] == CategoryEnum.EMI.value
    assert cat_map["ACH/SIP/ZERODHA BROKING"][0] == CategoryEnum.INVESTMENTS.value
    assert cat_map["UPI/DR/123/SWIGGY"][0] == CategoryEnum.FOOD.value
    assert cat_map["UPI/DR/123/UBER"][0] == CategoryEnum.TRAVEL.value
    assert cat_map["AMAZON PAY INDIA"][0] == CategoryEnum.SHOPPING.value
    assert cat_map["NETFLIX ENTERTAINMENT"][0] == CategoryEnum.SUBSCRIPTIONS.value
    assert cat_map["BESCOM ELECTRICITY BILL"][0] == CategoryEnum.BILLS.value
    assert cat_map["SOME UNKNOWN STORE XYZ"][0] == CategoryEnum.OTHER.value
    assert cat_map["SOME UNKNOWN STORE XYZ"][1] == 0.0
