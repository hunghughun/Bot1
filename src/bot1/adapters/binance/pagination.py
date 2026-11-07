"""Synthetic page coverage. No assumption of Binance cursor or retention semantics."""
from dataclasses import dataclass
import hashlib


class PageGap(ValueError):
    pass


@dataclass(frozen=True)
class SyntheticPage:
    index: int
    total: int
    payload: bytes


class PageWindow:
    def __init__(self, total_pages: int) -> None:
        if type(total_pages) is not int or not 1 <= total_pages <= 10000:
            raise PageGap("PAGE_COUNT")
        self.total = total_pages
        self.pages: dict[int, tuple[str, bytes]] = {}
        self.retention_gap = False

    def add(self, page: SyntheticPage) -> None:
        if type(page.index) is not int or not 1 <= page.index <= self.total or type(page.total) is not int or page.total != self.total or type(page.payload) is not bytes or len(page.payload) > 1_048_576:
            raise PageGap("PAGE_SCHEMA")
        fingerprint = hashlib.sha256(page.payload).hexdigest()
        old = self.pages.get(page.index)
        if old is not None and old[0] != fingerprint:
            raise PageGap("PAGE_CONFLICT")
        self.pages[page.index] = (fingerprint, page.payload)

    @property
    def missing(self) -> list[int]:
        return [i for i in range(1, self.total + 1) if i not in self.pages]

    @property
    def complete(self) -> bool:
        return not self.retention_gap and not self.missing

    def ordered(self) -> tuple[bytes, ...]:
        if not self.complete:
            raise PageGap("HISTORY_INCOMPLETE")
        return tuple(self.pages[i][1] for i in range(1, self.total + 1))
