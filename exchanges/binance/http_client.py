from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests

DEFAULT_TIMEOUT = 10


class BinanceHttpClient:
    def __init__(
        self,
        *,
        base_url: str = "https://api.binance.com",
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        logger=None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logger
        self.cooldown_until = 0
        self.last_latency_ms: float | None = None

    def _log(self, level: str, message: str, *args: Any) -> None:
        if self.logger:
            getattr(self.logger, level)(message, *args)

    def get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        url = f"{self.base_url}{path}"
        attempt = 0
        backoff = 1
        while True:
            attempt += 1
            now = time.time()
            if now < self.cooldown_until:
                time.sleep(self.cooldown_until - now)
            try:
                start = time.time()
                response = self.session.get(url, params=params, timeout=self.timeout)
                self.last_latency_ms = (time.time() - start) * 1000
                if response.status_code in (418, 429):
                    wait_for = int(response.headers.get("Retry-After", backoff))
                    self.cooldown_until = time.time() + wait_for
                    self._log("warning", "Binance rate limit hit (%s), cooling down %ss", response.status_code, wait_for)
                    if attempt > self.max_retries:
                        response.raise_for_status()
                    time.sleep(wait_for)
                    backoff *= 2
                    continue
                response.raise_for_status()
                return response.json()
            except requests.RequestException as exc:
                self._log("warning", "Binance request failed (attempt %s/%s): %s", attempt, self.max_retries, exc)
                if attempt >= self.max_retries:
                    raise
                time.sleep(backoff)
                backoff *= 2

    def fetch_exchange_info(self) -> Dict:
        return self.get_json("/api/v3/exchangeInfo")

    def fetch_ticker_24h(self, symbol: str | None = None) -> Dict | list:
        params = {"symbol": symbol} if symbol else None
        return self.get_json("/api/v3/ticker/24hr", params=params)

    def fetch_book_ticker(self, symbol: str) -> Dict:
        return self.get_json("/api/v3/ticker/bookTicker", params={"symbol": symbol})

    def fetch_all_book_ticker(self) -> list:
        return self.get_json("/api/v3/ticker/bookTicker")

    def fetch_time(self) -> Dict:
        return self.get_json("/api/v3/time")

    def measure_time_offset(self) -> int:
        start = int(time.time() * 1000)
        server_time = self.fetch_time().get("serverTime")
        end = int(time.time() * 1000)
        if server_time is None:
            return 0
        round_trip = (end - start) // 2
        return int(server_time - end + round_trip)
