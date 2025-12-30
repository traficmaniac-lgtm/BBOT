# DECISIONS
- Binance API is sole source of pair and market data; PairLoader no longer falls back to mocks. Offline failures surface in UI dialogs.
- Fee-free flagging uses Binance tradeFee endpoint when available, then heuristic quote whitelist and manual overrides; noted as Binance limitation for explicit fee-free list.
- ExchangeInfo is cached via BinanceDataService with optional manual refresh via UI retry.
- Websocket integration uses python-binance SpotWebsocketClient with reconnect helper; tests mock the socket to avoid network reliance.
- Time sync derived from /api/v3/time measuring round-trip latency; displayed as offset in trading panel.
