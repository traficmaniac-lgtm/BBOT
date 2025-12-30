from __future__ import annotations

from typing import Protocol

from core.policy_guard import PolicyGuard


class ActionResult(Protocol):
    """Result protocol for executed actions."""

    def status(self) -> str:  # pragma: no cover - interface method
        ...


class ExecutionEngine:
    """Executes approved actions against the exchange."""

    def __init__(self, *, policy_guard: PolicyGuard | None = None) -> None:
        self.policy_guard = policy_guard or PolicyGuard()

    def execute(self, action) -> ActionResult:
        if not self.policy_guard.allow(action):
            raise PermissionError("Action denied by policy guard")
        return self._execute_action(action)

    def _execute_action(self, action) -> ActionResult:
        raise NotImplementedError
