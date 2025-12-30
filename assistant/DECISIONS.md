# DECISIONS
- AI prompt format forces two blocks: `### EXPLANATION` followed by `### SETTINGS_JSON` that must validate against TradeSettingsSchema.
- Binance REST endpoints are the only market source: exchangeInfo for filters, ticker/24hr + bookTicker for last/bid/ask/spread/vol.
- Fee-free column relies on Binance tradeFee when available, then heuristic quote whitelist or manual config whitelist with method labeling.
- Status bar reports Binance latency from the last REST call; OpenAI indicator shows live vs mock depending on key presence.
- Mode locked to paper in UI; live trading toggle intentionally disabled pending further requirements.
