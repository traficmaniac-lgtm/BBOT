from __future__ import annotations

from typing import Protocol


class GuardRule(Protocol):
    def allow(self, action) -> bool:  # pragma: no cover - interface method
        ...


class PolicyGuard:
    """Applies safety checks before actions are executed."""

    def __init__(self, *, rules: list[GuardRule] | None = None) -> None:
        self.rules = rules or []

    def allow(self, action) -> bool:
        for rule in self.rules:
            if not rule.allow(action):
                return False
        return True
