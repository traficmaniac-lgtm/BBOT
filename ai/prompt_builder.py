from core.config_service import Config

PROMPT_TEMPLATE = (
    "You are an assistant that returns ONLY JSON following the provided schema. "
    "Pair: {pair}. Budget: {budget} USDT. Exchange: {exchange}. Mode: {mode}. "
    "Risk prefs: max drawdown {max_dd}%, per trade risk {risk_pct}%. "
    "Return precise trading parameters."
)


def build_prompt(config: Config) -> str:
    return PROMPT_TEMPLATE.format(
        pair=config.app.active_pair,
        budget=config.trading.budget_usdt,
        exchange=config.app.exchange,
        mode=config.app.mode,
        max_dd=config.risk.max_drawdown_pct,
        risk_pct=config.risk.per_trade_risk_pct,
    )

