from __future__ import annotations

from typing import Dict, Optional

from core.config_service import Config
from exchanges.binance.models import MarketSnapshot, PairFilters

PROMPT_HEADER = "You are BBOT AI copilot. Respond with two sections: '### EXPLANATION' and '### SETTINGS_JSON'."


def build_prompt(
    *,
    config: Config,
    snapshot: Optional[MarketSnapshot],
    filters: Optional[PairFilters],
    constraints: Optional[Dict[str, str]] = None,
) -> str:
    pair = config.app.active_pair or "(not selected)"
    market_lines = []
    if snapshot:
        market_lines.append(f"Last: {snapshot.last_price} | Bid: {snapshot.bid} | Ask: {snapshot.ask} | Spread: {snapshot.spread}")
        market_lines.append(f"Vol24h: {snapshot.volume_24h} | Timestamp: {snapshot.timestamp}")
    else:
        market_lines.append("Market snapshot unavailable")
    filter_lines = []
    if filters:
        filter_lines.append(f"tickSize={filters.tick_size} stepSize={filters.step_size} minNotional={filters.min_notional}")
    else:
        filter_lines.append("No filters")
    constraint_lines = [f"- {k}: {v}" for k, v in (constraints or {}).items()]
    constraint_block = "\n".join(constraint_lines) if constraint_lines else "- Follow Binance trading rules"
    return "\n".join(
        [
            PROMPT_HEADER,
            "You must produce JSON that matches the schema exactly.",
            f"Active pair: {pair}",
            "Market:",
            "\n".join(market_lines),
            "Filters:",
            "\n".join(filter_lines),
            "Current settings:",
            str(config.trading.model_dump()),
            "Constraints:",
            constraint_block,
            "Required JSON keys: budget_usdt, max_orders, grid_step_pct, take_profit_pct, stop_loss_pct, cooldown_seconds, update_interval_ms",
            "Be concise and professional.",
        ]
    )

