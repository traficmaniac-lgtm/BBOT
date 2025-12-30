from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FeeFreeFlag:
    fee_free: bool
    method: str
    notes: str | None = None


@dataclass
class PairFilters:
    tick_size: Optional[float] = None
    step_size: Optional[float] = None
    min_notional: Optional[float] = None
    raw_filters: List[Dict] = field(default_factory=list)


@dataclass
class PairInfo:
    symbol: str
    base: str
    quote: str
    status: str
    filters: PairFilters
    fee: FeeFreeFlag

    @classmethod
    def from_exchange_info(
        cls,
        symbol_data: Dict,
        *,
        fee_flag: FeeFreeFlag,
    ) -> "PairInfo":
        filters = cls._parse_filters(symbol_data.get("filters", []))
        return cls(
            symbol=symbol_data.get("symbol", ""),
            base=symbol_data.get("baseAsset", ""),
            quote=symbol_data.get("quoteAsset", ""),
            status=symbol_data.get("status", ""),
            filters=filters,
            fee=fee_flag,
        )

    @staticmethod
    def _parse_filters(filters: List[Dict]) -> PairFilters:
        tick = None
        step = None
        min_notional = None
        for f in filters:
            ftype = f.get("filterType")
            if ftype == "PRICE_FILTER":
                tick = float(f.get("tickSize", "0"))
            elif ftype == "LOT_SIZE":
                step = float(f.get("stepSize", "0"))
            elif ftype == "MIN_NOTIONAL":
                min_notional = float(f.get("minNotional", "0"))
        return PairFilters(tick_size=tick, step_size=step, min_notional=min_notional, raw_filters=filters)


@dataclass
class MarketSnapshot:
    symbol: str
    last_price: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    volume_24h: Optional[float]
    spread: Optional[float]
    timestamp: int | None = None

    @classmethod
    def from_payload(cls, *, symbol: str, book: Dict, stats: Dict) -> "MarketSnapshot":
        bid_price = float(book.get("bidPrice")) if book and book.get("bidPrice") else None
        ask_price = float(book.get("askPrice")) if book and book.get("askPrice") else None
        last_price = float(stats.get("lastPrice")) if stats and stats.get("lastPrice") else None
        volume = float(stats.get("volume")) if stats and stats.get("volume") else None
        spread = None
        if bid_price is not None and ask_price is not None:
            spread = ask_price - bid_price
        ts = stats.get("closeTime") if stats else None
        return cls(
            symbol=symbol,
            last_price=last_price,
            bid=bid_price,
            ask=ask_price,
            volume_24h=volume,
            spread=spread,
            timestamp=ts,
        )
