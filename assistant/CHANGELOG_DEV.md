# CHANGELOG_DEV
- Added Binance data layer (HTTP client with retries, data service, websocket helper) and models for PairInfo/MarketSnapshot/Fee flags.
- Updated UI to terminal-style panes with trading panel showing real-time market snapshot, filters, and connection status.
- Introduced AI autopilot skeleton (advisor, decision/execution/policy guard scaffolding).
- Added unit tests for Binance parsing and websocket reconnect handling; documented future AI actions contract.
- Fixed trading config schema by adding fee_free_whitelist with defaults and template update.
