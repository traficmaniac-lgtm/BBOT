from __future__ import annotations

from typing import Dict, Iterable, List

from exchanges.binance import BinanceDataService

FEE_METHOD_STANDARD = "Standard"
FEE_METHOD_API = "API"
FEE_METHOD_HEURISTIC = "Heuristic"
FEE_METHOD_MANUAL = "Manual"


class PairLoader:
    """Load pairs from Binance with fee-free detection and fallbacks."""

    def __init__(
        self,
        service: BinanceDataService,
        *,
        manual_fee_free: Iterable[str] | None = None,
        heuristic_quote_whitelist: Iterable[str] | None = None,
        logger=None,
    ) -> None:
        self.service = service
        self.manual_fee_free = {s.upper() for s in (manual_fee_free or [])}
        self.heuristic_quote_whitelist = {q.upper() for q in (heuristic_quote_whitelist or [])}
        self.logger = logger

    def load(self) -> List[Dict]:
        try:
            pairs = self.service.list_pairs()
            if not pairs:
                raise ValueError("No pairs returned from Binance")
            normalized: List[Dict] = []
            for pair in pairs:
                normalized.append(
                    {
                        "symbol": pair.symbol,
                        "base": pair.base,
                        "quote": pair.quote,
                        "status": pair.status,
                        "tick_size": pair.filters.tick_size,
                        "step_size": pair.filters.step_size,
                        "min_notional": pair.filters.min_notional,
                        "fee_free": pair.fee.fee_free,
                        "fee_method": pair.fee.method,
                    }
                )
            if self.logger:
                self.logger.info("Loaded %s pairs from Binance", len(normalized))
            return normalized
        except Exception as exc:  # noqa: BLE001
            if self.logger:
                self.logger.error("Binance pair fetch failed: %s", exc)
            raise
