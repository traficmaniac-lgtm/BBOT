from typing import Dict, List

FEE_FREE_PAIRS = [
    {"symbol": "BTCUSDT", "base": "BTC", "quote": "USDT", "fee_free": True, "fee_method": "Heuristic"},
    {"symbol": "ETHUSDT", "base": "ETH", "quote": "USDT", "fee_free": True, "fee_method": "Heuristic"},
    {"symbol": "BNBUSDT", "base": "BNB", "quote": "USDT", "fee_free": True, "fee_method": "Heuristic"},
    {"symbol": "SOLUSDT", "base": "SOL", "quote": "USDT", "fee_free": True, "fee_method": "Heuristic"},
]


def load_fee_free_pairs() -> List[Dict[str, str]]:
    return [pair.copy() for pair in FEE_FREE_PAIRS]
