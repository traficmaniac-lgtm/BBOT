# AI Contract

## Запрос
- Формат: текстовый промт с описанием пары, бюджета, предпочтений риска и ограничений биржи.
- AI обязан ответить СТРОГО JSON, без префиксов/суффиксов.

## Ответ JSON (пример)
```json
{
  "pair": "BTCUSDT",
  "budget_usdt": 250,
  "leverage": 3,
  "timeframe": "1h",
  "take_profit_pct": 4.5,
  "stop_loss_pct": 2.0,
  "rationale": "Trend is bullish on higher timeframe, risk balanced.",
  "risk_notes": "Keep exposure under 5% account, tighten if volatility spikes."
}
```

## Валидация
- `pair`: строка, не пустая.
- `budget_usdt`: float > 0.
- `leverage`: int >= 1.
- `timeframe`: строка из списка [`15m`, `1h`, `4h`, `1d`].
- `take_profit_pct`, `stop_loss_pct`: float >= 0.
- `rationale`, `risk_notes`: строки, могут быть пустыми, но ключи обязательны.

## Ошибки
- Любое отклонение формата → state = ERROR, запись в лог, повтор запроса (до 2 раз в мок-режиме).

