import os
import re
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

# Column keywords for automatic mapping
DATE_KEYWORDS = ["date", "txn date", "transaction date", "value date", "posting date", "trans date", "txndate"]
DESC_KEYWORDS = ["narration", "description", "particulars", "remarks", "transaction details", "details", "memo", "summary", "payee"]
DEBIT_KEYWORDS = ["debit", "dr", "withdrawal", "withdrawal amt", "withdrawal amount", "debit amount", "dr amount"]
CREDIT_KEYWORDS = ["credit", "cr", "deposit", "deposit amt", "deposit amount", "credit amount", "cr amount"]
AMOUNT_KEYWORDS = ["amount", "txn amount", "transaction amount", "net amount"]
TYPE_KEYWORDS = ["type", "cr/dr", "dr/cr", "txn type", "transaction type"]
BALANCE_KEYWORDS = ["balance", "closing balance", "available balance", "bal", "account balance"]

DATE_FORMATS = [
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%d/%m/%y",
    "%d-%m-%y",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d-%b-%Y",
    "%d %B %Y",
    "%d-%B-%Y",
]


class GenericCSVParser:
    """
    Parser for generic tabular CSV statements with heuristic column mapping.
    """

    def can_parse(self, file_path: str, bank_hint: Optional[str] = None) -> bool:
        if not os.path.exists(file_path):
            return False
        if not file_path.lower().endswith(".csv"):
            return False

        # Attempt to inspect headers to see if we can find date and amount/debit/credit
        try:
            df, _, _, _ = self._load_and_detect_columns(file_path)
            return df is not None and not df.empty
        except Exception:
            return False

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        df, col_map, debit_col, credit_col = self._load_and_detect_columns(file_path)
        if df is None or df.empty:
            raise ValueError("No transaction data found in the CSV file.")

        date_col = col_map.get("date")
        desc_col = col_map.get("desc")
        amount_col = col_map.get("amount")
        type_col = col_map.get("type")
        balance_col = col_map.get("balance")

        if not date_col:
            raise ValueError("Could not identify a transaction Date column in the CSV.")
        if not desc_col:
            raise ValueError("Could not identify a Description/Narration column in the CSV.")
        if not amount_col and not (debit_col and credit_col):
            raise ValueError("Could not identify Amount or Debit/Credit columns in the CSV.")

        canonical_txns: List[Dict[str, Any]] = []
        seen_signatures = set()

        for idx, row in df.iterrows():
            raw_date = row.get(date_col)
            raw_desc = row.get(desc_col)

            # Skip rows where date or description is missing/null
            if pd.isna(raw_date) or pd.isna(raw_desc):
                continue

            parsed_date = self._parse_date(str(raw_date).strip())
            if not parsed_date:
                logger.warning(f"Row {idx}: Unable to parse date '{raw_date}', skipping.")
                continue

            description_raw = str(raw_desc).strip()
            if not description_raw:
                continue

            amount = 0.0
            txn_type = "debit"

            if debit_col and credit_col:
                debit_val = self._parse_amount_value(row.get(debit_col))
                credit_val = self._parse_amount_value(row.get(credit_col))

                if credit_val is not None and credit_val > 0:
                    amount = credit_val
                    txn_type = "credit"
                elif debit_val is not None and debit_val > 0:
                    amount = -debit_val
                    txn_type = "debit"
                elif credit_val is not None and credit_val < 0:
                    # Some files use negative credit as debit
                    amount = credit_val
                    txn_type = "debit"
                elif debit_val is not None and debit_val < 0:
                    amount = debit_val
                    txn_type = "debit"
                else:
                    # Both are zero or empty
                    continue
            elif amount_col:
                val = self._parse_amount_value(row.get(amount_col))
                if val is None or val == 0:
                    continue

                if type_col and pd.notna(row.get(type_col)):
                    type_str = str(row.get(type_col)).strip().lower()
                    if "cr" in type_str or "credit" in type_str or "deposit" in type_str:
                        amount = abs(val)
                        txn_type = "credit"
                    else:
                        amount = -abs(val)
                        txn_type = "debit"
                else:
                    # Look at sign of amount or description keywords
                    if val < 0:
                        amount = val
                        txn_type = "debit"
                    else:
                        # Check if raw amount string had 'Dr' or 'Cr'
                        raw_amt_str = str(row.get(amount_col)).strip().lower()
                        if "cr" in raw_amt_str:
                            amount = val
                            txn_type = "credit"
                        elif "dr" in raw_amt_str:
                            amount = -val
                            txn_type = "debit"
                        else:
                            # Default positive as credit, negative as debit
                            amount = val
                            txn_type = "credit" if val > 0 else "debit"

            balance = None
            if balance_col and pd.notna(row.get(balance_col)):
                balance = self._parse_amount_value(row.get(balance_col))

            # Deduplication signature within session: (date, amount, description_raw)
            sig = (parsed_date.isoformat(), round(amount, 2), description_raw)
            if sig in seen_signatures:
                logger.info(f"Duplicate row detected: {sig}, keeping first instance.")
                continue
            seen_signatures.add(sig)

            canonical_txns.append({
                "date": parsed_date,
                "description_raw": description_raw,
                "amount": round(amount, 2),
                "type": txn_type,
                "balance": round(balance, 2) if balance is not None else None,
            })

        if not canonical_txns:
            raise ValueError("No valid transaction rows could be parsed from the CSV.")

        # Sort chronologically by date
        canonical_txns.sort(key=lambda t: t["date"])
        return canonical_txns

    def _load_and_detect_columns(
        self, file_path: str
    ) -> Tuple[Optional[pd.DataFrame], Dict[str, str], Optional[str], Optional[str]]:
        """
        Loads CSV detecting encoding and header position, and maps column headers.
        """
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        lines = []

        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    lines = f.readlines()
                break
            except Exception:
                continue

        if not lines:
            return None, {}, None, None

        # Filter out empty lines
        non_empty = [(i, line.strip()) for i, line in enumerate(lines) if line.strip()]
        if not non_empty:
            return None, {}, None, None

        # Scan for header line (first line containing both date and (amount or (debit and credit)))
        header_idx = 0
        best_match_score = -1

        for line_idx, line in non_empty[:25]:  # Check first 25 non-empty lines
            lower_line = line.lower()
            score = 0
            if any(k in lower_line for k in DATE_KEYWORDS):
                score += 2
            if any(k in lower_line for k in DESC_KEYWORDS):
                score += 2
            if any(k in lower_line for k in DEBIT_KEYWORDS):
                score += 1
            if any(k in lower_line for k in CREDIT_KEYWORDS):
                score += 1
            if any(k in lower_line for k in AMOUNT_KEYWORDS):
                score += 1

            if score > best_match_score and score >= 3:
                best_match_score = score
                header_idx = line_idx

        # Read CSV with pandas starting at header_idx
        df = None
        for enc in encodings:
            for sep in [",", ";", "\t"]:
                try:
                    candidate_df = pd.read_csv(
                        file_path,
                        skiprows=header_idx,
                        sep=sep,
                        encoding=enc,
                        on_bad_lines="skip",
                    )
                    if candidate_df is not None and len(candidate_df.columns) >= 2:
                        df = candidate_df
                        break
                except Exception:
                    continue
            if df is not None:
                break

        if df is None or df.empty:
            return None, {}, None, None

        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]

        # Map columns
        col_map: Dict[str, str] = {}
        debit_col: Optional[str] = None
        credit_col: Optional[str] = None

        for col in df.columns:
            col_lower = col.lower().strip()

            # Date
            if not col_map.get("date") and any(k == col_lower or f" {k}" in col_lower or f"{k} " in col_lower for k in DATE_KEYWORDS):
                col_map["date"] = col
            # Description
            elif not col_map.get("desc") and any(k == col_lower or f" {k}" in col_lower or f"{k} " in col_lower for k in DESC_KEYWORDS):
                col_map["desc"] = col
            # Debit
            elif not debit_col and any(k == col_lower or f" {k}" in col_lower or f"{k} " in col_lower for k in DEBIT_KEYWORDS):
                debit_col = col
            # Credit
            elif not credit_col and any(k == col_lower or f" {k}" in col_lower or f"{k} " in col_lower for k in CREDIT_KEYWORDS):
                credit_col = col
            # Balance
            elif not col_map.get("balance") and any(k == col_lower or f" {k}" in col_lower or f"{k} " in col_lower for k in BALANCE_KEYWORDS):
                col_map["balance"] = col
            # Type
            elif not col_map.get("type") and any(k == col_lower for k in TYPE_KEYWORDS):
                col_map["type"] = col
            # Amount
            elif not col_map.get("amount") and any(k == col_lower or f" {k}" in col_lower or f"{k} " in col_lower for k in AMOUNT_KEYWORDS):
                col_map["amount"] = col

        return df, col_map, debit_col, credit_col

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Attempt multiple date parsing formats."""
        if not date_str or date_str.lower() in ("nan", "none", "null", ""):
            return None

        # Clean any trailing time component if separated by space or T
        date_part = date_str.split(" ")[0].split("T")[0].strip()

        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(date_part, fmt).date()
            except ValueError:
                continue

        # Try pandas to_datetime with dayfirst=True
        try:
            parsed = pd.to_datetime(date_str, dayfirst=True, errors="coerce")
            if pd.notna(parsed):
                return parsed.date()
        except Exception:
            pass

        return None

    def _parse_amount_value(self, val: Any) -> Optional[float]:
        """Convert raw amount strings or numbers to float."""
        if pd.isna(val) or val is None:
            return None

        if isinstance(val, (int, float)):
            return float(val)

        val_str = str(val).strip()
        if not val_str or val_str.lower() in ("-", "--", "nan", "none", "null"):
            return None

        is_neg = False
        # Handle parentheses e.g. (1200.50)
        if val_str.startswith("(") and val_str.endswith(")"):
            is_neg = True
            val_str = val_str[1:-1]

        # Check for Dr / Cr suffix
        val_lower = val_str.lower()
        if val_lower.endswith("dr"):
            is_neg = True
            val_str = val_str[:-2]
        elif val_lower.endswith("cr"):
            val_str = val_str[:-2]

        # Remove currency symbols and formatting commas
        clean_num_str = re.sub(r"[^\d.-]", "", val_str)
        if not clean_num_str:
            return None

        try:
            num = float(clean_num_str)
            return -abs(num) if is_neg else num
        except ValueError:
            return None
