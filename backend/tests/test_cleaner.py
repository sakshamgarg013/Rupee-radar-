from datetime import date
from app.pipeline.cleaner import clean_description, detect_payment_mode, clean_transactions


def test_clean_description():
    assert "SWIGGY" in clean_description("UPI/DR/412589102931/SWIGGY/swiggy@okhdfcbank")
    assert "ZOMATO" in clean_description("POS 49123819 ZOMATO GURGAON IN")
    assert "INFOSYS" in clean_description("NEFT CR-INFOSYS LTD-SALARY-MAY2024")
    assert "AIRTEL BROADBAND" in clean_description("BIL/AIRTEL BROADBAND/BIL-192839")
    assert "BESCOM" in clean_description("BIL/BESCOM ELECTRICITY BILL/BES1928")


def test_detect_payment_mode():
    assert detect_payment_mode("UPI/DR/123/SWIGGY/swiggy@oksbi") == "UPI"
    assert detect_payment_mode("NEFT CR-COMPANY-SALARY") == "NEFT"
    assert detect_payment_mode("IMPS/P2A/4123891029/TRANSFER") == "IMPS"
    assert detect_payment_mode("POS 49123819 ZOMATO") == "CARD"
    assert detect_payment_mode("ATM WDL/HDFC ATM KORAMANGALA") == "ATM"
    assert detect_payment_mode("ACH/SIP/ZERODHA") == "AUTO_DEBIT"


def test_clean_transactions():
    raw_txns = [
        {
            "date": date(2024, 5, 5),
            "description_raw": "UPI/DR/412589102931/SWIGGY/swiggy@okhdfcbank",
            "amount": 450.0,
            "type": "debit",
            "balance": 10000.0,
        },
        {
            "date": date(2024, 5, 1),
            "description_raw": "NEFT CR-INFOSYS LTD-SALARY",
            "amount": 75000.0,
            "type": "credit",
            "balance": 85000.0,
        },
    ]

    cleaned = clean_transactions(raw_txns)
    assert len(cleaned) == 2

    # Check debit transaction
    t0 = cleaned[0]
    assert t0["amount"] == -450.0
    assert t0["type"] == "debit"
    assert "SWIGGY" in t0["description_clean"]
    assert t0["payment_mode"] == "UPI"
    assert t0["merchant"] == "Swiggy"

    # Check credit transaction
    t1 = cleaned[1]
    assert t1["amount"] == 75000.0
    assert t1["type"] == "credit"
    assert t1["payment_mode"] == "NEFT"
