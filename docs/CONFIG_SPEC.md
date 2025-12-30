# CONFIG Spec

Формат: YAML.

```yaml
app:
  mode: "paper"            # paper | live
  active_pair: ""
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
  timeout_seconds: 20

trading:
  budget_usdt: 100
  max_orders: 5
  grid_step_pct: 0.5
  take_profit_pct: 1.5
  stop_loss_pct: 1.0
  cooldown_seconds: 10
  update_interval_ms: 1000
```

### Правила
- Все секреты задаются только в `config/config.yaml`, пример — `config/config.example.yaml`.
- Значения валидируются через pydantic схемы в `core/config_service.py`.
- В UI отображается активное имя файла конфига и предупреждения о невалидных полях.
