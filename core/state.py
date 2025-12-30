from enum import Enum
from typing import Optional


class AppState(str, Enum):
    IDLE = "IDLE"
    CONFIGURED = "CONFIGURED"
    PAIRS_LOADED = "PAIRS_LOADED"
    AI_READY = "AI_READY"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class StateMachine:
    def __init__(self) -> None:
        self.state: AppState = AppState.IDLE
        self.last_error: Optional[str] = None

    def set_state(self, new_state: AppState, error: Optional[str] = None) -> None:
        self.state = new_state
        self.last_error = error

    def is_running(self) -> bool:
        return self.state == AppState.RUNNING

