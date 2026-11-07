from decimal import Decimal

from bot1.core.numeric import parse
from bot1.adapters.binance.contracts import require_verified
from bot1.adapters.binance.parsing import JsonNumber, ParsedFrame


class SchemaCompatibilityValidator:
    @staticmethod
    def money(value: object, domain: str = "signed") -> Decimal:
        """Field helper only: no automatic choice of which fields represent money."""
        return parse(value.lexeme if isinstance(value, JsonNumber) else value, domain)

    @staticmethod
    def validate(frame: ParsedFrame) -> None:
        require_verified(frame.contract_id)
