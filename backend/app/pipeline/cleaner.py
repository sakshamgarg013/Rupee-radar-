import re
import json
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from app.utils.merchant_dict import find_merchant


def clean_description(raw_desc: str) -> str:
    """
    Clean noise, prefixes, bank codes, and reference IDs from transaction descriptions.
    """
    if not raw_desc:
        return "UNKNOWN"

    text = raw_desc.strip()

    # Normalize slashes and hyphens around prefixes
    text = re.sub(r"\s+", " ", text)

    # 1. Remove UPI prefix patterns e.g. UPI/DR/12345/..., UPI-SWIGGY-..., UPI/P2A/..., UPI/CR/...
    text = re.sub(r"^UPI\s*[/:\-]\s*(?:DR|CR|P2A|P2M|P2P|REV)?\s*[/:\-]?", "", text, flags=re.IGNORECASE)

    # 2. Remove IMPS/NEFT/RTGS/NACH/ACH/POS prefixes
    text = re.sub(
        r"^(?:NEFT|IMPS|RTGS|NACH|ACH|POS|INB|INF|VPS|EAW|ATM|MB)\s*[/:\-]\s*(?:DR|CR)?\s*[/:\-]?",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # 3. Strip known bank prefix codes like "BIL/", "BIL/ONL/", "CMS/", "TPT/", "NFT/"
    text = re.sub(r"^(?:BIL|BIL/ONL|CMS|TPT|NFT|MMT)\s*[/:\-]", "", text, flags=re.IGNORECASE)

    # 4. Remove common trailing or inline VPA handles (e.g. user@okhdfcbank, merchant@paytm)
    text = re.sub(r"\b[a-zA-Z0-9.\-_]+@(okaxis|oksbi|okhdfcbank|okicici|paytm|ybl|apl|upi|axl|ibl)\b", "", text, flags=re.IGNORECASE)

    # 5. Remove long numeric reference numbers (> 6 digits)
    text = re.sub(r"\b\d{7,}\b", "", text)

    # 6. Remove alphanumeric transaction reference strings like /202305011234/ or /REF123456/
    text = re.sub(r"[/:\-]\s*[A-Z0-9]{8,}\s*[/:\-]?", " ", text, flags=re.IGNORECASE)

    # 7. Remove isolated punctuation and symbols
    text = re.sub(r"[/*#\-_]{2,}", " ", text)
    text = re.sub(r"^[/:\-.\s]+|[/:\-.\s]+$", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Fallback to original stripped if regex wiped everything
    if not text:
        text = raw_desc.strip()

    return text.upper()


def detect_payment_mode(raw_desc: str) -> str:
    """
    Detect payment mode based on keywords in description.
    Returns: UPI, NEFT, IMPS, RTGS, CARD, ATM, NETBANKING, CHEQUE, CASH, OTHER
    """
    desc_upper = raw_desc.upper()

    if "UPI" in desc_upper or "@" in desc_upper:
        return "UPI"
    if "IMPS" in desc_upper:
        return "IMPS"
    if "NEFT" in desc_upper:
        return "NEFT"
    if "RTGS" in desc_upper:
        return "RTGS"
    if any(k in desc_upper for k in ["POS", "ECOM", "DEBIT CARD", "CREDIT CARD", "VISA", "MASTERCARD", "RUPAY"]):
        return "CARD"
    if any(k in desc_upper for k in ["ATM", "CASH WDL", "CWDR"]):
        return "ATM"
    if any(k in desc_upper for k in ["INB", "INF", "NETBANKING", "TRANSFER", "IBANK"]):
        return "NETBANKING"
    if any(k in desc_upper for k in ["ACH", "NACH", "AUTO-DEBIT", "STANDING INSTRUCTION"]):
        return "AUTO_DEBIT"
    if "CHQ" in desc_upper or "CHEQUE" in desc_upper:
        return "CHEQUE"

    return "OTHER"


def clean_transactions(raw_txns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich and normalize raw transaction records:
    - Clean description of noise and prefixes
    - Detect payment mode and extract merchant
    - Ensure correct sign on amounts (debit < 0, credit > 0)
    - Ensure date format is date object or ISO string
    """
    cleaned_txns: List[Dict[str, Any]] = []

    for txn in raw_txns:
        raw_desc = txn.get("description_raw", "")
        cleaned_desc = clean_description(raw_desc)
        payment_mode = detect_payment_mode(raw_desc)

        # Merchant extraction via dictionary
        merchant_match = find_merchant(cleaned_desc) or find_merchant(raw_desc)
        merchant_name = merchant_match[0] if merchant_match else None

        # Sign correction
        amount = float(txn.get("amount", 0.0))
        txn_type = txn.get("type", "debit").lower()

        if txn_type == "credit":
            corrected_amount = abs(amount)
        else:
            corrected_amount = -abs(amount)
            txn_type = "debit"

        # Ensure date format
        raw_date = txn.get("date")
        if isinstance(raw_date, datetime):
            parsed_date = raw_date.date()
        elif isinstance(raw_date, date):
            parsed_date = raw_date
        elif isinstance(raw_date, str):
            parsed_date = datetime.strptime(raw_date[:10], "%Y-%m-%d").date()
        else:
            parsed_date = date.today()

        metadata = {
            "payment_mode": payment_mode,
            "merchant": merchant_name,
        }

        # If existing metadata present, preserve it
        existing_meta = txn.get("metadata")
        if existing_meta:
            if isinstance(existing_meta, str):
                try:
                    metadata.update(json.loads(existing_meta))
                except Exception:
                    pass
            elif isinstance(existing_meta, dict):
                metadata.update(existing_meta)

        cleaned_txns.append({
            "date": parsed_date,
            "description_raw": raw_desc,
            "description_clean": cleaned_desc,
            "amount": round(corrected_amount, 2),
            "type": txn_type,
            "balance": round(float(txn["balance"]), 2) if txn.get("balance") is not None else None,
            "payment_mode": payment_mode,
            "merchant": merchant_name,
            "metadata_json": json.dumps(metadata),
        })

    return cleaned_txns
