from __future__ import annotations

import threading
import time
from typing import Callable, Optional

from binance import ThreadedWebsocketManager


class BookTickerStream:
    def __init__(
        self,
        symbol: str,
        *,
        on_message: Callable[[dict], None],
        on_disconnect: Optional[Callable[[], None]] = None,
        api_key: str | None = None,
        api_secret: str | None = None,
        logger=None,
    ) -> None:
        self.symbol = symbol.upper()
        self.on_message = on_message
        self.on_disconnect = on_disconnect
        self.logger = logger
        self._twm = ThreadedWebsocketManager(api_key=api_key or None, api_secret=api_secret or None)
        self._running = False
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
        self._twm.start()
        self._twm.start_book_ticker_socket(callback=self._handle, symbol=self.symbol)

    def _handle(self, message: dict) -> None:
        try:
            self.on_message(message)
        except Exception:  # noqa: BLE001
            if self.logger:
                self.logger.exception("Failed to handle websocket message")

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._running = False
        try:
            self._twm.stop()
        finally:
            if self.on_disconnect:
                self.on_disconnect()

    def reconnect(self, delay_seconds: int = 2) -> None:
        self.stop()
        time.sleep(delay_seconds)
        self.start()
