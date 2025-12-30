from __future__ import annotations

from typing import List, Protocol

from exchanges.binance import MarketSnapshot


class Action(Protocol):
    """Marker protocol for trade actions."""

    def describe(self) -> str:  # pragma: no cover - interface method
        ...


class DecisionEngine:
    """AI-driven decision maker placeholder."""

    def propose_actions(self, state: dict, market_snapshot: MarketSnapshot, settings: dict) -> List[Action]:
        """Return proposed actions from AI logic.

        Concrete implementation will evaluate the state and market snapshot to suggest
        trades or risk adjustments.
        """

        raise NotImplementedError
