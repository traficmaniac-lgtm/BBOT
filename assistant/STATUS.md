# STATUS
- Rebuilt UI into 3-screen flow (Setup → Pair Select → Trade) with bottom status bar and banner messaging.
- Setup screen captures Binance/OpenAI keys with live connectivity tests and persists to local config.
- Pair Select now formats prices/spreads/volumes cleanly, adds quote/search/TRADING filters, sortable headers, and better selection UX.
- Trade screen formats snapshot by tickSize, adds auto-refresh, highlights critical filters, presets + inline validation, and “Effective Settings” JSON copy.
- AI panel is gated when no OpenAI key (Not configured + Open Setup), chat disabled until configured.
