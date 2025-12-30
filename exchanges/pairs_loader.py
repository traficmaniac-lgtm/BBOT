from __future__ import annotations

from typing import Dict, Iterable, List

from .binance_client import BinanceClient
from .mock import load_fee_free_pairs

FEE_METHOD_STANDARD = "Standard"
FEE_METHOD_API = "API"
FEE_METHOD_HEURISTIC = "Heuristic"
FEE_METHOD_MANUAL = "Manual"


class PairLoader:
    """Load pairs from Binance with fee-free detection and fallbacks."""

    def __init__(
        self,
        client: BinanceClient,
        *,
        manual_fee_free: Iterable[str] | None = None,
        heuristic_quote_whitelist: Iterable[str] | None = None,
        logger=None,
    ) -> None:
        self.client = client
        self.manual_fee_free = {s.upper() for s in (manual_fee_free or [])}
        self.heuristic_quote_whitelist = {q.upper() for q in (heuristic_quote_whitelist or [])}
        self.logger = logger

    def load(self) -> List[Dict]:
        try:
            symbols = self.client.fetch_symbols()
            fee_data = self.client.fetch_fee_data()
            pairs = self._build_pairs(symbols, fee_data)
            if not pairs:
                raise ValueError("No pairs returned from Binance")
            if self.logger:
                self.logger.info("Loaded %s pairs from Binance", len(pairs))
            return pairs
        except Exception as exc:  # noqa: BLE001
            if self.logger:
                self.logger.warning("Falling back to mock fee-free pairs: %s", exc)
            return self._load_mock()

    def _build_pairs(self, symbols: List[Dict], fee_data: List[Dict]) -> List[Dict]:
        fee_map = {entry.get("symbol", ""): entry for entry in fee_data}
        pairs: List[Dict] = []
        for symbol_data in symbols:
            status = symbol_data.get("status")
            if status != "TRADING":
                continue
            base = symbol_data.get("baseAsset")
            quote = symbol_data.get("quoteAsset")
            symbol = symbol_data.get("symbol", "")
            fee_free, method = self._detect_fee_free(symbol, quote, fee_map)
            pairs.append(
                {
                    "symbol": symbol,
                    "base": base,
                    "quote": quote,
                    "fee_free": fee_free,
                    "fee_method": method,
                }
            )
        return sorted(pairs, key=lambda p: p["symbol"])

    def _detect_fee_free(self, symbol: str, quote: str, fee_map: Dict[str, Dict]) -> tuple[bool, str]:
        fee_entry = fee_map.get(symbol)
        if fee_entry and self._is_zero_fee(fee_entry):
            return True, FEE_METHOD_API
        if quote and quote.upper() in self.heuristic_quote_whitelist:
            return True, FEE_METHOD_HEURISTIC
        if symbol.upper() in self.manual_fee_free:
            return True, FEE_METHOD_MANUAL
        return False, FEE_METHOD_STANDARD

    @staticmethod
    def _is_zero_fee(entry: Dict) -> bool:
        maker = float(entry.get("makerCommission", entry.get("maker", 0)) or 0)
        taker = float(entry.get("takerCommission", entry.get("taker", 0)) or 0)
        return maker == 0 and taker == 0

    def _load_mock(self) -> List[Dict]:
        mock_pairs = load_fee_free_pairs()
        for item in mock_pairs:
            item.setdefault("fee_free", True)
            item.setdefault("fee_method", FEE_METHOD_HEURISTIC)
            if not item.get("base") or not item.get("quote"):
                symbol = item.get("symbol", "")
                if len(symbol) > 4:
                    item["base"] = symbol[:-4]
                    item["quote"] = symbol[-4:]
        return mock_pairs
