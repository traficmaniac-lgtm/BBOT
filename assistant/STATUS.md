# STATUS
- Rebuilt UI into 3-screen flow (Setup → Pair Select → Trade) with bottom status bar and banner messaging.
- Setup screen captures Binance/OpenAI keys with live connectivity tests and persists to local config.
- Pair Select pulls symbols, spreads, and 24h volume directly from Binance REST, with search/quote/fee-free filters.
- Trade screen shows live market snapshot + filters, editable bot settings with preview, AI chat (explanation + JSON apply), and live log.
- OpenAI client wired for real chat completions with retries and validation; falls back to mock only when no key.
