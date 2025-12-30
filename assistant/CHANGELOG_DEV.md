# CHANGELOG_DEV
- Rebuilt Tkinter app into router-driven screens (setup/pair-select/trade) and removed legacy tabs/panels.
- Added OpenAI chat client with real completions, retries, schema validation, and mock fallback when no key.
- Tightened Binance data path to REST-only sources (exchangeInfo, ticker/24hr, bookTicker, time) with latency tracking and overview aggregation.
- Trade screen now surfaces market snapshot, symbol filters, settings preview, AI chat apply/copy actions, and start/stop controls for paper mode.
- Updated config schema and example to new trading fields (budget/max_orders/grid_step/take_profit/stop_loss/cooldown/update_interval).
- Pair Select polished with Binance-grade formatting (price/spread/volume), quote/search/TRADING filters, sortable headers, and double-click/select safeguards.
- Trade view adds tickSize-aware LAST/BID/ASK, percent spread, auto-refresh cadence picker, highlighted filters, presets with inline validation, and “Effective Settings” JSON copy button.
- AI copilot now surfaces “AI not configured” + Open Setup CTA when no key; compact status bar shows Binance/OpenAI/pair/state succinctly.
