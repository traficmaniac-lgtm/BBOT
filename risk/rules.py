from typing import Dict


def validate_risk(settings: Dict[str, float]) -> Dict[str, str]:
    notes = []
    if settings.get("max_drawdown_pct", 0) > 30:
        notes.append("Max drawdown too high for conservative mode")
    if settings.get("per_trade_risk_pct", 0) > 5:
        notes.append("Per trade risk exceeds 5%")
    if settings.get("max_concurrent_trades", 1) > 10:
        notes.append("Too many concurrent trades")
    return {
        "status": "ok" if not notes else "warn",
        "notes": "; ".join(notes) or "Risk profile accepted",
    }

