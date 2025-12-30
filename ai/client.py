from __future__ import annotations

import json
import time
from typing import Dict, Optional

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ValidationError

from core.logger import mask_secret
from core.state import AppState, StateMachine


class TradeSettingsSchema(BaseModel):
    budget_usdt: float
    max_orders: int
    grid_step_pct: float
    take_profit_pct: float
    stop_loss_pct: float
    cooldown_seconds: int
    update_interval_ms: int


class AiChatResult(BaseModel):
    explanation: str
    settings: TradeSettingsSchema


class AiClient:
    def __init__(
        self,
        state: StateMachine,
        logger,
        *,
        api_key: Optional[str] = None,
        model: str = "gpt-4.1-mini",
        temperature: float = 0.2,
        timeout_seconds: int = 20,
        max_retries: int = 2,
    ) -> None:
        self.state = state
        self.logger = logger
        self.api_key = api_key or ""
        self.model = model
        self.temperature = temperature
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def run_chat(self, prompt: str, user_message: str) -> Dict:
        for attempt in range(self.max_retries + 1):
            try:
                payload = self._run(prompt, user_message)
                parsed = AiChatResult(**payload)
                self.state.set_state(AppState.AI_READY)
                self.logger.info("AI response valid with settings: %s", parsed.settings.model_dump())
                return parsed.model_dump()
            except (ValidationError, ValueError) as exc:
                self.state.set_state(AppState.ERROR, str(exc))
                self.logger.error("AI response validation failed (attempt %s): %s", attempt + 1, exc)
        raise ValueError("AI analysis failed after retries")

    def _run(self, prompt: str, user_message: str) -> Dict:
        if not self.client:
            return self._mock_response(user_message)
        start = time.time()
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=self.temperature,
                timeout=self.timeout_seconds,
            )
        except OpenAIError as exc:  # noqa: BLE001
            self.logger.error("OpenAI call failed: %s", exc)
            raise ValueError(f"OpenAI error: {exc}") from exc
        finally:
            latency = (time.time() - start) * 1000
            self.logger.info("OpenAI latency: %.0fms", latency)
        content = completion.choices[0].message.content if completion.choices else ""
        return self._parse_content(content)

    def _parse_content(self, content: str) -> Dict:
        explanation, settings_blob = self._split_blocks(content)
        try:
            settings_data = json.loads(settings_blob)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse SETTINGS_JSON: {exc}") from exc
        return {"explanation": explanation.strip(), "settings": settings_data}

    @staticmethod
    def _split_blocks(content: str) -> tuple[str, str]:
        lower = content.lower()
        exp_anchor = lower.find("### explanation")
        settings_anchor = lower.find("### settings_json")
        if settings_anchor == -1:
            raise ValueError("Missing SETTINGS_JSON block in AI response")
        if exp_anchor == -1:
            exp_text = ""
        else:
            exp_text = content[exp_anchor + len("### EXPLANATION") : settings_anchor].strip()
        settings_text = content[settings_anchor + len("### SETTINGS_JSON") :].strip()
        return exp_text, settings_text

    def _mock_response(self, user_message: str) -> Dict:
        self.logger.info("Running mock AI (no key). User message: %s", user_message)
        return {
            "explanation": "Mock AI because no OpenAI key was provided.",
            "settings": {
                "budget_usdt": 150,
                "max_orders": 4,
                "grid_step_pct": 0.4,
                "take_profit_pct": 1.8,
                "stop_loss_pct": 1.2,
                "cooldown_seconds": 12,
                "update_interval_ms": 1200,
            },
        }

    def describe(self) -> str:
        if not self.client:
            return "Mock AI client (no key)"
        return f"OpenAI client (key: {mask_secret(self.api_key)})"

    def can_run_live(self) -> bool:
        return bool(self.client)

    def healthcheck(self) -> bool:
        if not self.client:
            return False
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "Say OK"}, {"role": "user", "content": "Ping"}],
                temperature=0,
                timeout=5,
            )
            return bool(completion.choices)
        except OpenAIError:
            return False

