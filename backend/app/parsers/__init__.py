from typing import Optional, List
from app.parsers.base import StatementParser
from app.parsers.generic_csv import GenericCSVParser

PARSER_REGISTRY: List[StatementParser] = [
    # Bank-specific parsers will be added here in Phase 5
    GenericCSVParser(),
]


def get_parser(file_path: str, bank_hint: Optional[str] = None) -> StatementParser:
    """
    Find and return the first parser in the registry capable of handling the file.
    Raises ValueError if no suitable parser is found.
    """
    for parser in PARSER_REGISTRY:
        if parser.can_parse(file_path, bank_hint=bank_hint):
            return parser

    raise ValueError("No compatible parser found for the uploaded file format.")
