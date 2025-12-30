# CONFIG Spec

Формат: YAML.

```yaml
app:
  mode: "mock"            # mock | live
  active_pair: "BTCUSDT"
  exchange: "binance"
  testnet: true
  log_level: "INFO"

api_keys:
  exchange_key: ""
  exchange_secret: ""
  openai_key: ""

ai:
  model: "gpt-4.1-mini"
  temperature: 0.2
  max_retries: 2

trading:
  budget_usdt: 100
  leverage: 1
  timeframe: "1h"
  take_profit_pct: 3.0
  stop_loss_pct: 1.5

risk:
  max_drawdown_pct: 15
  per_trade_risk_pct: 2
  max_concurrent_trades: 3
```

### Правила
- Все секреты задаются только в `config/config.yaml`, пример — `config/config.example.yaml`.
- Значения валидируются через pydantic схемы в `core/config_service.py`.
- В UI отображается активное имя файла конфига и предупреждения о невалидных полях.

