import json
import random
from typing import Dict, Optional

from pydantic import BaseModel, ValidationError

from core.logger import mask_secret
from core.state import AppState, StateMachine


class AiResponse(BaseModel):
    pair: str
    budget_usdt: float
    leverage: int
    timeframe: str
    take_profit_pct: float
    stop_loss_pct: float
    rationale: str
    risk_notes: str


class AiClient:
    def __init__(self, state: StateMachine, logger, mock: bool = True, api_key: Optional[str] = None) -> None:
        self.state = state
        self.logger = logger
        self.mock = mock
        self.api_key = api_key

    def run_analysis(self, prompt: str, retries: int = 2) -> Dict:
        for attempt in range(retries + 1):
            try:
                payload = self._run(prompt)
                parsed = AiResponse(**payload)
                self.state.set_state(AppState.AI_READY)
                self.logger.info("AI analysis successful: %s", parsed.json())
                return parsed.model_dump()
            except (ValidationError, ValueError) as exc:
                self.state.set_state(AppState.ERROR, str(exc))
                self.logger.error("AI response validation failed (attempt %s): %s", attempt + 1, exc)
        raise ValueError("AI analysis failed after retries")

    def _run(self, prompt: str) -> Dict:
        if self.mock:
            return self._mock_response(prompt)
        # Placeholder for real OpenAI call
        raise NotImplementedError("Live OpenAI mode not implemented yet")

    def _mock_response(self, prompt: str) -> Dict:
        self.logger.info("Running mock AI with prompt: %s", prompt)
        leverage = random.choice([1, 2, 3])
        take_profit = round(random.uniform(2, 5), 2)
        stop_loss = round(random.uniform(1, 3), 2)
        return {
            "pair": "BTCUSDT",
            "budget_usdt": 200,
            "leverage": leverage,
            "timeframe": random.choice(["15m", "1h", "4h"]),
            "take_profit_pct": take_profit,
            "stop_loss_pct": stop_loss,
            "rationale": "Mocked rationale based on prompt length {}".format(len(prompt)),
            "risk_notes": "Keep exposure under 5%",
        }

    def describe(self) -> str:
        if self.mock:
            return "Mock AI client"
        return f"OpenAI client (key: {mask_secret(self.api_key)})"

