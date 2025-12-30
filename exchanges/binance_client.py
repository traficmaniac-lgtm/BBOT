from __future__ import annotations

from typing import Dict, List

from binance.client import Client
from binance.exceptions import BinanceAPIException


class BinanceClient:
    """Thin wrapper around python-binance with graceful fallbacks."""

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        *,
        testnet: bool = False,
        logger=None,
    ) -> None:
        self.logger = logger
        self.client = Client(api_key=api_key or None, api_secret=api_secret or None, testnet=testnet)

    def fetch_exchange_info(self) -> Dict:
        return self.client.get_exchange_info()

    def fetch_symbols(self) -> List[Dict]:
        info = self.fetch_exchange_info()
        return info.get("symbols", [])

    def fetch_fee_data(self) -> List[Dict]:
        try:
            return self.client.get_trade_fee()
        except BinanceAPIException as exc:  # missing or invalid keys still allow rest of flow
            if self.logger:
                self.logger.warning("Binance trade fee endpoint unavailable: %s", exc)
            return []
        except Exception as exc:  # noqa: BLE001
            if self.logger:
                self.logger.error("Unexpected Binance fee fetch error: %s", exc)
            return []
