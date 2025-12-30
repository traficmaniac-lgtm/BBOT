from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Dict, List

from ai.client import AiClient
from ai.prompt_builder import build_prompt
from core.config_service import ConfigService
from core.logger import setup_logger
from core.state import StateMachine
from exchanges.binance.http_client import BinanceHttpClient
from exchanges.binance.service import BinanceDataService
from exchanges.pairs_loader import PairLoader
from ui.screens.pair_select_screen import PairSelectScreen
from ui.screens.setup_screen import SetupScreen
from ui.screens.trade_screen import TradeScreen


class BBOTApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("BBOT Terminal Copilot")
        self.state = StateMachine()
        self.config_service = ConfigService()
        self._load_config_if_exists()
        self.logger = setup_logger(level=self.config_service.config.app.log_level)
        self.http_client = BinanceHttpClient(logger=self.logger)
        self.binance_service = BinanceDataService(
            self.http_client,
            manual_fee_free=self.config_service.config.pairs.manual_fee_free,
            heuristic_quotes=self.config_service.config.pairs.heuristic_quote_whitelist,
            logger=self.logger,
        )
        self.ai_client = AiClient(
            self.state,
            self.logger,
            api_key=self.config_service.config.api_keys.openai_key,
            model=self.config_service.config.ai.model,
            temperature=self.config_service.config.ai.temperature,
            timeout_seconds=self.config_service.config.ai.timeout_seconds,
            max_retries=self.config_service.config.ai.max_retries,
        )
        self.pairs: List[Dict] = []
        self.active_screen: tk.Frame | None = None
        self.market_snapshot = None

        self.banner_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self._build_shell()
        self.route_on_start()

    def _load_config_if_exists(self) -> None:
        try:
            if Path(self.config_service.default_path).exists():
                self.config_service.load()
        except Exception as exc:  # noqa: BLE001
            messagebox.showwarning("Config", f"Failed to load config: {exc}")

    # Layout
    def _build_shell(self) -> None:
        self.root.geometry("1200x760")
        shell = ttk.Frame(self.root)
        shell.pack(fill="both", expand=True)

        self.banner_label = ttk.Label(
            shell, textvariable=self.banner_var, foreground="white", background="#2d2f36", anchor="w"
        )
        self.banner_label.pack(fill="x", padx=4, pady=(0, 4))

        self.content_frame = ttk.Frame(shell)
        self.content_frame.pack(fill="both", expand=True)

        self.status_bar = ttk.Frame(shell)
        self.status_bar.pack(fill="x")
        self.status_var.set("Status initializing...")
        ttk.Label(self.status_bar, textvariable=self.status_var, anchor="w").pack(side="left", padx=6, pady=4)

    def _set_screen(self, screen: tk.Frame) -> None:
        if self.active_screen:
            self.active_screen.destroy()
        self.active_screen = screen
        self.active_screen.pack(fill="both", expand=True)
        self.refresh_status_bar()

    # Routing
    def route_on_start(self) -> None:
        if not self.config_service.has_required_keys():
            self.show_setup()
        else:
            self.show_pair_select()

    def show_setup(self) -> None:
        screen = SetupScreen(self.content_frame, app=self)
        self._set_screen(screen)
        self.banner_var.set("Setup: add Binance and OpenAI keys")

    def show_pair_select(self) -> None:
        screen = PairSelectScreen(self.content_frame, app=self)
        self._set_screen(screen)
        self.banner_var.set("Select a pair from Binance")
        screen.load_pairs()

    def show_trade(self, symbol: str) -> None:
        self.config_service.config.app.active_pair = symbol
        screen = TradeScreen(self.content_frame, app=self, symbol=symbol)
        self._set_screen(screen)
        self.banner_var.set(f"Trading setup for {symbol}")
        screen.refresh_market()

    # Callbacks for screens
    def save_keys(self, binance_key: str, binance_secret: str, openai_key: str, testnet: bool) -> None:
        cfg = self.config_service.config
        cfg.api_keys.exchange_key = binance_key
        cfg.api_keys.exchange_secret = binance_secret
        cfg.api_keys.openai_key = openai_key
        cfg.app.testnet = testnet
        self.config_service.save()
        self._rebuild_services()
        self.banner_var.set("Saved keys locally. Ready to continue.")
        self.show_pair_select()

    def test_binance(self) -> bool:
        try:
            self.http_client.fetch_time()
            self.refresh_status_bar()
            return True
        except Exception as exc:  # noqa: BLE001
            self.banner_var.set(f"Binance test failed: {exc}")
            return False

    def test_openai(self) -> bool:
        ok = self.ai_client.healthcheck()
        if not ok:
            self.banner_var.set("OpenAI not ready (no key or request failed)")
        self.refresh_status_bar()
        return ok

    def fetch_pairs(self) -> List[Dict]:
        loader = PairLoader(self.binance_service, logger=self.logger)
        pairs = loader.load()
        overview = self.binance_service.market_overview()
        merged = []
        for pair in pairs:
            metrics = overview.get(pair["symbol"], {})
            merged.append(
                {
                    **pair,
                    "last": metrics.get("last"),
                    "spread": metrics.get("spread"),
                    "volume": metrics.get("volume"),
                    "fee_free": pair.get("fee_free"),
                    "fee_method": pair.get("fee_method"),
                }
            )
        self.pairs = merged
        self.refresh_status_bar()
        return merged

    def select_pair(self, symbol: str) -> None:
        self.config_service.config.app.active_pair = symbol
        self.banner_var.set(f"Active pair: {symbol}")
        self.show_trade(symbol)

    def fetch_market_snapshot(self, symbol: str):
        try:
            snapshot = self.binance_service.fetch_market_snapshot(symbol)
            self.market_snapshot = snapshot
            self.refresh_status_bar()
            return snapshot
        except Exception as exc:  # noqa: BLE001
            self.banner_var.set(f"Market snapshot failed: {exc}")
            return None

    def apply_settings(self, settings: Dict[str, float | int]) -> None:
        cfg = self.config_service.config
        cfg.trading = cfg.trading.copy(update=settings)
        self.config_service.save()
        self.refresh_status_bar()

    def run_ai(self, user_message: str) -> Dict:
        prompt = build_prompt(
            config=self.config_service.config,
            snapshot=self.market_snapshot,
            filters=None,
            constraints={"mode": "Paper trading only"},
        )
        return self.ai_client.run_chat(prompt, user_message)

    # Utilities
    def refresh_status_bar(self) -> None:
        cfg = self.config_service.config
        binance_status = "Connected" if self.http_client.last_latency_ms else "Error" if self.banner_var.get().startswith("Binance") else "Idle"
        openai_status = "Ready" if self.ai_client.can_run_live() else "Not configured"
        active_pair = cfg.app.active_pair or "-"
        state = self.state.state
        latency = f"{self.http_client.last_latency_ms:.0f}ms" if self.http_client.last_latency_ms else "-"
        self.status_var.set(
            f"Binance: {binance_status} ({latency})  |  OpenAI: {openai_status}  |  Pair: {active_pair}  |  State: {state}"
        )

    def _rebuild_services(self) -> None:
        cfg = self.config_service.config
        self.http_client = BinanceHttpClient(logger=self.logger)
        self.binance_service = BinanceDataService(
            self.http_client,
            manual_fee_free=cfg.pairs.manual_fee_free,
            heuristic_quotes=cfg.pairs.heuristic_quote_whitelist,
            logger=self.logger,
        )
        self.ai_client = AiClient(
            self.state,
            self.logger,
            api_key=cfg.api_keys.openai_key,
            model=cfg.ai.model,
            temperature=cfg.ai.temperature,
            timeout_seconds=cfg.ai.timeout_seconds,
            max_retries=cfg.ai.max_retries,
        )


def run() -> None:
    root = tk.Tk()
    app = BBOTApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()
