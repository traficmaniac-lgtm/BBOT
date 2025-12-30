from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict

from ai.client import TradeSettingsSchema
from core.state import AppState


class TradeScreen(ttk.Frame):
    def __init__(self, master, app, symbol: str) -> None:
        super().__init__(master)
        self.app = app
        self.symbol = symbol
        self.settings_vars: Dict[str, tk.StringVar] = {}
        self.last_ai_payload: Dict | None = None
        self._build()

    def _build(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=6)
        ttk.Label(header, text=f"Trade: {self.symbol}", font=("Arial", 16, "bold")).pack(side="left")
        ttk.Button(header, text="Refresh snapshot", command=self.refresh_market).pack(side="right")

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True, padx=8, pady=4)
        right = ttk.Frame(body)
        right.pack(side="right", fill="both", expand=True, padx=8, pady=4)

        # Market snapshot
        market_box = ttk.Labelframe(left, text="Market snapshot (Binance)")
        market_box.pack(fill="x", pady=6)
        self.market_labels = {
            "last": tk.StringVar(value="-"),
            "bid": tk.StringVar(value="-"),
            "ask": tk.StringVar(value="-"),
            "spread": tk.StringVar(value="-"),
            "volume": tk.StringVar(value="-"),
        }
        for idx, (label, key) in enumerate(self.market_labels.items()):
            ttk.Label(market_box, text=label.upper()).grid(row=idx, column=0, sticky="w", padx=6, pady=3)
            ttk.Label(market_box, textvariable=key).grid(row=idx, column=1, sticky="w", padx=6, pady=3)

        filters_box = ttk.Labelframe(left, text="Filters")
        filters_box.pack(fill="x", pady=6)
        self.filters_vars = {
            "tick": tk.StringVar(value="-"),
            "step": tk.StringVar(value="-"),
            "min_notional": tk.StringVar(value="-"),
        }
        labels = [
            ("tickSize", "tick"),
            ("stepSize", "step"),
            ("minNotional", "min_notional"),
        ]
        for idx, (label, key) in enumerate(labels):
            ttk.Label(filters_box, text=label).grid(row=idx, column=0, sticky="w", padx=6, pady=3)
            ttk.Label(filters_box, textvariable=self.filters_vars[key]).grid(row=idx, column=1, sticky="w", padx=6, pady=3)

        conn_box = ttk.Labelframe(left, text="Connection")
        conn_box.pack(fill="x", pady=6)
        self.conn_status = tk.StringVar(value="REST pending")
        ttk.Label(conn_box, textvariable=self.conn_status).pack(anchor="w", padx=6, pady=3)

        # Settings + AI column
        settings_box = ttk.Labelframe(right, text="Bot settings (paper mode)")
        settings_box.pack(fill="x", pady=6)
        fields = [
            ("budget_usdt", "Budget USDT"),
            ("max_orders", "Max orders"),
            ("grid_step_pct", "Grid step %"),
            ("take_profit_pct", "Take profit %"),
            ("stop_loss_pct", "Stop loss %"),
            ("cooldown_seconds", "Cooldown (s)"),
            ("update_interval_ms", "Update interval (ms)"),
        ]
        for idx, (key, label) in enumerate(fields):
            self.settings_vars[key] = tk.StringVar(value=str(getattr(self.app.config_service.config.trading, key)))
            ttk.Label(settings_box, text=label).grid(row=idx, column=0, sticky="w", padx=6, pady=4)
            ttk.Entry(settings_box, textvariable=self.settings_vars[key]).grid(row=idx, column=1, sticky="we", padx=6, pady=4)
        settings_box.grid_columnconfigure(1, weight=1)

        control_box = ttk.Frame(settings_box)
        control_box.grid(row=len(fields), column=0, columnspan=2, sticky="we", pady=6)
        ttk.Button(control_box, text="Start (paper)", command=self._on_start).pack(side="left")
        ttk.Button(control_box, text="Stop", command=self._on_stop).pack(side="left", padx=4)

        self.preview = tk.Text(settings_box, height=6, state="disabled")
        self.preview.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="we", padx=6, pady=4)
        self._render_preview()

        # AI chat
        ai_box = ttk.Labelframe(right, text="AI copilot")
        ai_box.pack(fill="both", expand=True, pady=6)
        self.chat_log = tk.Text(ai_box, height=10, state="disabled")
        self.chat_log.pack(fill="both", expand=True, padx=6, pady=4)
        self.chat_input = tk.Entry(ai_box)
        self.chat_input.pack(fill="x", padx=6)
        send_frame = ttk.Frame(ai_box)
        send_frame.pack(fill="x", padx=6, pady=4)
        ttk.Button(send_frame, text="Send to AI", command=self._on_send).pack(side="left")
        ttk.Button(send_frame, text="Apply JSON", command=self._apply_ai_json).pack(side="left", padx=4)
        ttk.Button(send_frame, text="Copy JSON", command=self._copy_json).pack(side="left")

        # Logs
        self.log_box = tk.Text(self, height=6, state="disabled")
        self.log_box.pack(fill="x", padx=10, pady=6)

    def refresh_market(self) -> None:
        snapshot = self.app.fetch_market_snapshot(self.symbol)
        if snapshot:
            self.market_labels["last"].set(snapshot.last_price)
            self.market_labels["bid"].set(snapshot.bid)
            self.market_labels["ask"].set(snapshot.ask)
            self.market_labels["spread"].set(snapshot.spread)
            self.market_labels["volume"].set(snapshot.volume_24h)
            pair_meta = next((p for p in self.app.pairs if p.get("symbol") == self.symbol), {})
            self.filters_vars["tick"].set(pair_meta.get("tick_size", "-"))
            self.filters_vars["step"].set(pair_meta.get("step_size", "-"))
            self.filters_vars["min_notional"].set(pair_meta.get("min_notional", "-"))
            self.conn_status.set("REST OK")
        else:
            self.conn_status.set("REST error")
        self._render_preview()

    def _render_preview(self) -> None:
        data = {k: self._parse_value(v.get()) for k, v in self.settings_vars.items()}
        text = json.dumps(data, indent=2)
        self._set_text(self.preview, text)

    def _on_start(self) -> None:
        self.app.state.set_state(AppState.RUNNING)
        self._log("Bot started in paper mode")
        self.app.refresh_status_bar()

    def _on_stop(self) -> None:
        self.app.state.set_state(AppState.STOPPED)
        self._log("Bot stopped")
        self.app.refresh_status_bar()

    def _on_send(self) -> None:
        message = self.chat_input.get().strip()
        if not message:
            return
        self._log(f"User -> AI: {message}")
        try:
            response = self.app.run_ai(message)
            self.last_ai_payload = response
            self._log("🧠 AI EXPLANATION:\n" + response.get("explanation", ""))
            settings_json = json.dumps(response.get("settings", {}), indent=2)
            self._log("⚙️ SETTINGS_JSON:\n" + settings_json)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("AI", str(exc))
        self._render_preview()

    def _apply_ai_json(self) -> None:
        if not self.last_ai_payload:
            messagebox.showinfo("AI", "No AI settings to apply")
            return
        try:
            validated = TradeSettingsSchema(**self.last_ai_payload.get("settings", {}))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("AI", f"Invalid JSON: {exc}")
            return
        for key, value in validated.model_dump().items():
            self.settings_vars[key].set(str(value))
        self.app.apply_settings(validated.model_dump())
        self._render_preview()
        self._log("Applied AI JSON to fields")

    def _copy_json(self) -> None:
        if not self.last_ai_payload:
            return
        payload = json.dumps(self.last_ai_payload.get("settings", {}), indent=2)
        self.clipboard_clear()
        self.clipboard_append(payload)
        self._log("Copied AI JSON to clipboard")

    def _parse_value(self, value: str):
        try:
            if value is None:
                return None
            if "." in str(value):
                return float(value)
            return int(value)
        except ValueError:
            return value

    def _log(self, text: str) -> None:
        self.log_box.config(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _set_text(self, widget: tk.Text, content: str) -> None:
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.config(state="disabled")

