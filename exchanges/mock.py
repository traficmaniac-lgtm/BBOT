from typing import List, Dict

FEE_FREE_PAIRS = [
    {"symbol": "BTCUSDT", "type": "spot", "fee": 0.0},
    {"symbol": "ETHUSDT", "type": "spot", "fee": 0.0},
    {"symbol": "BNBUSDT", "type": "spot", "fee": 0.0},
    {"symbol": "SOLUSDT", "type": "spot", "fee": 0.0},
]


def load_fee_free_pairs() -> List[Dict[str, str]]:
    return FEE_FREE_PAIRS.copy()

