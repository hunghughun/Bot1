"""Lossless JSON syntax decoding only; successful decode is not schema validation."""
from dataclasses import dataclass
import hashlib
import json
from typing import Any


class ParseError(ValueError):
    pass


@dataclass(frozen=True)
class JsonNumber:
    lexeme: str


@dataclass(frozen=True)
class ParsedFrame:
    contract_id: str
    channel: str
    data: Any
    sha256: str


def _number(token: str) -> JsonNumber:
    if len(token) > 96:
        raise ParseError("JSON_NUMBER_LENGTH")
    return JsonNumber(token)


def _constant(token: str) -> None:
    raise ParseError("JSON_NONFINITE")


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ParseError("JSON_DUPLICATE_KEY")
        result[key] = value
    return result


def decode(raw: str | bytes) -> tuple[Any, str]:
    if type(raw) not in (str, bytes):
        raise ParseError("JSON_RAW_TYPE")
    if len(raw) > 1_048_576:
        raise ParseError("JSON_SIZE")
    try:
        blob = raw.encode("utf-8") if isinstance(raw, str) else raw
        text = blob.decode("utf-8", errors="strict")
        if len(blob) > 1_048_576:
            raise ParseError("JSON_SIZE")
        data = json.loads(text, parse_float=_number, parse_int=_number,
                          parse_constant=_constant, object_pairs_hook=_object)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ParseError("JSON_INVALID") from None
    queue = [(data, 0)]
    count = 0
    while queue:
        item, depth = queue.pop()
        count += 1
        if depth > 32 or count > 10000:
            raise ParseError("JSON_COMPLEXITY")
        if isinstance(item, dict):
            queue.extend((value, depth + 1) for value in item.values())
        elif isinstance(item, list):
            queue.extend((value, depth + 1) for value in item)
    return data, hashlib.sha256(blob).hexdigest()


class RestResponseParser:
    def parse(self, raw: str | bytes, contract_id: str) -> ParsedFrame:
        data, digest = decode(raw)
        if not isinstance(data, (dict, list)):
            raise ParseError("JSON_RESPONSE_CONTAINER")
        return ParsedFrame(contract_id, "rest", data, digest)
