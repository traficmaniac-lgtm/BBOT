import unittest
from unittest.mock import MagicMock, patch

from exchanges.binance.models import FeeFreeFlag, MarketSnapshot, PairInfo
from exchanges.binance.ws import BookTickerStream


class BinanceModelTests(unittest.TestCase):
    def test_binance_exchange_info_parsing(self) -> None:
        data = {
            "symbol": "BTCUSDT",
            "baseAsset": "BTC",
            "quoteAsset": "USDT",
            "status": "TRADING",
            "filters": [
                {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                {"filterType": "LOT_SIZE", "stepSize": "0.001"},
                {"filterType": "MIN_NOTIONAL", "minNotional": "10"},
            ],
        }
        pair = PairInfo.from_exchange_info(data, fee_flag=FeeFreeFlag(False, "STANDARD"))
        self.assertEqual(pair.symbol, "BTCUSDT")
        self.assertEqual(pair.filters.tick_size, 0.01)
        self.assertEqual(pair.filters.step_size, 0.001)
        self.assertEqual(pair.filters.min_notional, 10.0)

    def test_pair_filters_present_for_active_pair(self) -> None:
        data = {
            "symbol": "ETHUSDT",
            "baseAsset": "ETH",
            "quoteAsset": "USDT",
            "status": "TRADING",
            "filters": [
                {"filterType": "PRICE_FILTER", "tickSize": "0.1"},
                {"filterType": "LOT_SIZE", "stepSize": "0.01"},
            ],
        }
        pair = PairInfo.from_exchange_info(data, fee_flag=FeeFreeFlag(True, "HEURISTIC"))
        self.assertIsNotNone(pair.filters.tick_size)
        self.assertIsNotNone(pair.filters.step_size)
        self.assertEqual(pair.fee.fee_free, True)

    def test_market_snapshot_fetch(self) -> None:
        book = {"bidPrice": "100.0", "askPrice": "101.0"}
        stats = {"lastPrice": "100.5", "volume": "2000", "closeTime": 12345}
        snapshot = MarketSnapshot.from_payload(symbol="BTCUSDT", book=book, stats=stats)
        self.assertEqual(snapshot.spread, 1.0)
        self.assertEqual(snapshot.volume_24h, 2000.0)
        self.assertEqual(snapshot.timestamp, 12345)

    def test_ws_reconnect_logic(self) -> None:
        received = []
        dummy_client = MagicMock()
        with patch("exchanges.binance.ws.ThreadedWebsocketManager", return_value=dummy_client):
            with patch("time.sleep", return_value=None):
                stream = BookTickerStream("BTCUSDT", on_message=lambda payload: received.append(payload))
                stream.start()
                stream.reconnect(delay_seconds=0)
        self.assertTrue(dummy_client.start.called)
        self.assertTrue(dummy_client.stop.called)
        self.assertTrue(dummy_client.start_book_ticker_socket.called)


if __name__ == "__main__":
    unittest.main()
