"""Decode offline frames without guessing the current Binance event envelope."""
from bot1.adapters.binance.parsing import ParsedFrame, ParseError, decode


class WebSocketEventParser:
    def parse(self, raw: str | bytes, contract_id: str) -> ParsedFrame:
        data, digest = decode(raw)
        if not isinstance(data, dict):
            raise ParseError("JSON_FRAME_CONTAINER")
        return ParsedFrame(contract_id, "websocket", data, digest)
