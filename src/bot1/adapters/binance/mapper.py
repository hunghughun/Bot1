"""Explicit offline SDK profiles; no default live or generic financial mapper."""
from bot1.adapters.binance.parsing import ParsedFrame
from bot1.adapters.binance.schema import SchemaCompatibilityValidator
from bot1.adapters.binance.contracts import UnsupportedContract


class AccountEventMapper:
    def map(self, frame: ParsedFrame, *, context=None) -> tuple[dict, ...]:
        if context is not None:
            from bot1.adapters.binance.balance import BalanceContext, map_balance
            if not isinstance(context, BalanceContext):
                raise UnsupportedContract("BALANCE_CONTEXT_REQUIRED")
            return map_balance(frame, context)
        SchemaCompatibilityValidator.validate(frame)
        # No generic field-name mapper or config override: semantics need reviewed code.
        raise UnsupportedContract("BINANCE_MAPPING_NOT_IMPLEMENTED")
