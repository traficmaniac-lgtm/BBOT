from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field, ValidationError


class ApiKeys(BaseModel):
    exchange_key: str = ""
    exchange_secret: str = ""
    openai_key: str = ""

    def masked(self) -> "ApiKeys":
        def _mask(value: str) -> str:
            return value[:3] + "***" if value else ""

        return ApiKeys(
            exchange_key=_mask(self.exchange_key),
            exchange_secret=_mask(self.exchange_secret),
            openai_key=_mask(self.openai_key),
        )


class AppSettings(BaseModel):
    mode: str = Field("mock", description="mock | live")
    active_pair: str = "BTCUSDT"
    exchange: str = "binance"
    testnet: bool = True
    log_level: str = "INFO"


class AiSettings(BaseModel):
    model: str = "gpt-4.1-mini"
    temperature: float = 0.2
    max_retries: int = 2


class PairSettings(BaseModel):
    manual_fee_free: list[str] = []
    heuristic_quote_whitelist: list[str] = ["FDUSD"]


class TradingSettings(BaseModel):
    budget_usdt: float = 100
    leverage: int = 1
    timeframe: str = "1h"
    take_profit_pct: float = 3.0
    stop_loss_pct: float = 1.5


class RiskSettings(BaseModel):
    max_drawdown_pct: float = 15
    per_trade_risk_pct: float = 2
    max_concurrent_trades: int = 3


class Config(BaseModel):
    app: AppSettings = AppSettings()
    api_keys: ApiKeys = ApiKeys()
    ai: AiSettings = AiSettings()
    pairs: PairSettings = PairSettings()
    trading: TradingSettings = TradingSettings()
    risk: RiskSettings = RiskSettings()


class ConfigService:
    def __init__(self, default_path: Path = Path("config/config.yaml")) -> None:
        self.default_path = default_path
        self.config = Config()
        self.last_loaded: Optional[Path] = None

    def load(self, path: Optional[Path] = None) -> Config:
        path = path or self.default_path
        if not path.exists():
            raise FileNotFoundError(f"Config not found: {path}")

        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        try:
            self.config = Config(**data)
            self.last_loaded = path
            return self.config
        except ValidationError as exc:
            raise ValueError(f"Config validation error: {exc}") from exc

    def save(self, path: Optional[Path] = None) -> Path:
        path = path or self.default_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(self.config.model_dump(), fh, allow_unicode=True)
        self.last_loaded = path
        return path

    def active_config_name(self) -> str:
        return self.last_loaded.name if self.last_loaded else self.default_path.name

