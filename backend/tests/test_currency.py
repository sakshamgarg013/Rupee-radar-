from app.utils.currency import format_inr


def test_format_inr_basic():
    assert format_inr(500) == "₹500"
    assert format_inr(1000) == "₹1,000"
    assert format_inr(15000) == "₹15,000"
    assert format_inr(125000) == "₹1,25,000"
    assert format_inr(1000000) == "₹10,00,000"
    assert format_inr(12345678) == "₹1,23,45,678"


def test_format_inr_negative():
    assert format_inr(-450) == "-₹450"
    assert format_inr(-125000) == "-₹1,25,000"


def test_format_inr_with_decimals():
    assert format_inr(125000.50, include_decimals=True) == "₹1,25,000.50"
    assert format_inr(450.0, include_decimals=True) == "₹450.00"
