"""Do not infer REST/WS economic identity from timestamps, values or trade IDs."""
from bot1.adapters.binance.parsing import ParsedFrame
from bot1.adapters.binance.contracts import require_verified, UnsupportedContract


class BinanceEventCorrelation:
    def link(self, rest: ParsedFrame, websocket: ParsedFrame) -> str:
        require_verified(rest.contract_id)
        require_verified(websocket.contract_id)
        raise UnsupportedContract("BINANCE_CORRELATION_RULE_NOT_IMPLEMENTED")
