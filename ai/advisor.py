from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class AdvisorMode(str, Enum):
    ASSIST = "ASSIST"
    AUTOPILOT = "AUTOPILOT"


@dataclass
class AdvisorResponse:
    explanation: str
    settings_json: Dict[str, Any] | None = None
    actions_json: List[Dict[str, Any]] | None = None


class Advisor:
    """Produces AI guidance and future autopilot actions."""

    def __init__(self, *, mode: AdvisorMode = AdvisorMode.ASSIST) -> None:
        self.mode = mode

    def advise(self, state: dict) -> AdvisorResponse:
        """Return dual-output guidance stub.

        Real implementation will call the LLM and return both a human readable
        explanation and machine-readable JSON blobs for settings/actions.
        """

        explanation = "AI assistant is in %s mode" % self.mode.value
        return AdvisorResponse(explanation=explanation, settings_json=None, actions_json=None)
