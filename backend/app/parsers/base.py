from typing import Protocol, Optional, List, Dict, Any


class StatementParser(Protocol):
    """
    Protocol that all bank and format statement parsers must implement.
    """

    def can_parse(self, file_path: str, bank_hint: Optional[str] = None) -> bool:
        """
        Check whether this parser is able to parse the given statement file.
        """
        ...

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract canonical transaction rows from the file.
        Each item in the returned list must adhere to the canonical schema:
        {
            "date": datetime.date,
            "description_raw": str,
            "amount": float,  # negative for debits, positive for credits
            "type": "debit" | "credit",
            "balance": Optional[float]
        }
        """
        ...
