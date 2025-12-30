from __future__ import annotations

import time
from typing import Dict, Iterable, List, Optional

from .http_client import BinanceHttpClient
from .models import FeeFreeFlag, MarketSnapshot, PairInfo


class BinanceDataService:
    def __init__(
        self,
        http_client: BinanceHttpClient,
        *,
        cache_ttl_seconds: int = 900,
        manual_fee_free: Iterable[str] | None = None,
        heuristic_quotes: Iterable[str] | None = None,
        logger=None,
    ) -> None:
        self.http_client = http_client
        self.cache_ttl_seconds = cache_ttl_seconds
        self.manual_fee_free = {s.upper() for s in (manual_fee_free or [])}
        self.heuristic_quotes = {q.upper() for q in (heuristic_quotes or [])}
        self.logger = logger
        self.exchange_info_cache: Dict | None = None
        self.exchange_info_fetched_at: float = 0
        self.last_time_offset_ms: int | None = None
        self.offline_mode = False

    def _log(self, level: str, msg: str, *args) -> None:
        if self.logger:
            getattr(self.logger, level)(msg, *args)

    def refresh_exchange_info(self, *, force: bool = False) -> Dict:
        now = time.time()
        if not force and self.exchange_info_cache and now - self.exchange_info_fetched_at < self.cache_ttl_seconds:
            return self.exchange_info_cache
        info = self.http_client.fetch_exchange_info()
        self.exchange_info_cache = info
        self.exchange_info_fetched_at = now
        self.offline_mode = False
        return info

    def _fee_flag_for(self, symbol: str, quote: str, fee_data: Dict[str, Dict]) -> FeeFreeFlag:
        entry = fee_data.get(symbol)
        if entry and self._is_zero_fee(entry):
            return FeeFreeFlag(True, "API", "Binance tradeFee=0")
        if quote.upper() in self.heuristic_quotes:
            return FeeFreeFlag(True, "HEURISTIC", "Quote whitelisted")
        if symbol.upper() in self.manual_fee_free:
            return FeeFreeFlag(True, "MANUAL", "User whitelist")
        return FeeFreeFlag(False, "STANDARD", None)

    @staticmethod
    def _is_zero_fee(entry: Dict) -> bool:
        maker = float(entry.get("makerCommission", entry.get("maker", 0)) or 0)
        taker = float(entry.get("takerCommission", entry.get("taker", 0)) or 0)
        return maker == 0 and taker == 0

    def list_pairs(self, *, quote_filter: Optional[str] = None) -> List[PairInfo]:
        info = self.refresh_exchange_info()
        symbols = info.get("symbols", [])
        fee_data_raw = self._safe_fetch_fee_data()
        fee_map = {entry.get("symbol", ""): entry for entry in fee_data_raw}
        pairs: List[PairInfo] = []
        for symbol_data in symbols:
            status = symbol_data.get("status")
            quote = symbol_data.get("quoteAsset", "").upper()
            if quote_filter and quote_filter != quote:
                continue
            fee_flag = self._fee_flag_for(symbol_data.get("symbol", ""), quote, fee_map)
            pair = PairInfo.from_exchange_info(symbol_data, fee_flag=fee_flag)
            pairs.append(pair)
        return pairs

    def _safe_fetch_fee_data(self) -> List[Dict]:
        try:
            return self.http_client.get_json("/sapi/v1/asset/tradeFee")
        except Exception as exc:  # noqa: BLE001
            self._log("warning", "Fee data unavailable from Binance: %s", exc)
            return []

    def fetch_market_snapshot(self, symbol: str) -> MarketSnapshot:
        stats = self.http_client.fetch_ticker_24h(symbol)
        book = self.http_client.fetch_book_ticker(symbol)
        return MarketSnapshot.from_payload(symbol=symbol, book=book, stats=stats)

    def time_sync_status(self) -> Dict[str, int | bool]:
        offset = self.http_client.measure_time_offset()
        self.last_time_offset_ms = offset
        return {"offset_ms": offset, "ok": abs(offset) < 1000}

    def connection_report(self) -> Dict[str, object]:
        return {
            "rest_ok": not self.offline_mode,
            "time_offset_ms": self.last_time_offset_ms,
            "cache_age": time.time() - self.exchange_info_fetched_at if self.exchange_info_fetched_at else None,
        }
