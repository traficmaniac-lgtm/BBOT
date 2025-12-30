from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict

from ai.client import TradeSettingsSchema
from core.formatting import format_price, format_spread, format_volume
from core.state import AppState


class TradeScreen(ttk.Frame):
    def __init__(self, master, app, symbol: str) -> None:
        super().__init__(master)
        self.app = app
        self.symbol = symbol
        self.settings_vars: Dict[str, tk.StringVar] = {}
        self.last_ai_payload: Dict | None = None
        self.auto_refresh_job: str | None = None
        self.validation_labels: Dict[str, tk.Label] = {}
        self.ai_buttons: list[ttk.Button] = []
        self._build()

    def _build(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill="x", padx=10, pady=6)
        ttk.Label(header, text=f"Trade: {self.symbol}", font=("Arial", 16, "bold")).pack(side="left")
        controls = ttk.Frame(header)
        controls.pack(side="right")
        ttk.Button(controls, text="Refresh snapshot", command=self.refresh_market).pack(side="left", padx=4)
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.auto_refresh_interval = tk.StringVar(value="2000")
        ttk.Checkbutton(controls, text="Auto-refresh", variable=self.auto_refresh_var, command=self._toggle_auto_refresh).pack(
            side="left", padx=(10, 4)
        )
        ttk.Combobox(controls, width=5, state="readonly", textvariable=self.auto_refresh_interval, values=["1000", "2000", "5000"]).pack(
            side="left"
        )

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
            "spread_points": tk.StringVar(value="-"),
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
            ttk.Label(filters_box, text=label, font=("Arial", 10, "bold")).grid(row=idx, column=0, sticky="w", padx=6, pady=3)
            lbl = ttk.Label(filters_box, textvariable=self.filters_vars[key])
            lbl.grid(row=idx, column=1, sticky="w", padx=6, pady=3)
            if key == "min_notional":
                self._attach_tooltip(lbl, "Shown as 'N/A' when Binance does not provide minNotional filter")

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
            entry = ttk.Entry(settings_box, textvariable=self.settings_vars[key])
            entry.grid(row=idx, column=1, sticky="we", padx=6, pady=4)
            entry.bind("<FocusOut>", lambda *_: self._validate_settings())
            err = tk.Label(settings_box, text="", foreground="red", font=("Arial", 8))
            err.grid(row=idx, column=2, sticky="w")
            self.validation_labels[key] = err
        settings_box.grid_columnconfigure(1, weight=1)

        control_box = ttk.Frame(settings_box)
        control_box.grid(row=len(fields), column=0, columnspan=2, sticky="we", pady=6)
        ttk.Button(control_box, text="Conservative", command=lambda: self._apply_preset("conservative")).pack(side="left", padx=(0, 4))
        ttk.Button(control_box, text="Normal", command=lambda: self._apply_preset("normal")).pack(side="left", padx=4)
        ttk.Button(control_box, text="Aggressive", command=lambda: self._apply_preset("aggressive")).pack(side="left", padx=4)
        ttk.Button(control_box, text="Start (paper)", command=self._on_start).pack(side="right")
        ttk.Button(control_box, text="Stop", command=self._on_stop).pack(side="right", padx=4)

        preview_row = len(fields) + 1
        ttk.Label(settings_box, text="Effective Settings (JSON)").grid(row=preview_row, column=0, sticky="w", padx=6)
        copy_btn = ttk.Button(settings_box, text="Copy", command=self._copy_effective_settings)
        copy_btn.grid(row=preview_row, column=1, sticky="e", padx=6)
        self.preview = tk.Text(settings_box, height=8, state="disabled")
        self.preview.grid(row=preview_row + 1, column=0, columnspan=3, sticky="we", padx=6, pady=4)
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
        self.ai_status_label = ttk.Label(ai_box, foreground="red")
        self.ai_status_label.pack(anchor="w", padx=6)
        self.setup_ai_btn = ttk.Button(ai_box, text="Open Setup", command=self.app.show_setup)
        self.ai_buttons = [
            ttk.Button(send_frame, text="Send to AI", command=self._on_send),
            ttk.Button(send_frame, text="Apply JSON", command=self._apply_ai_json),
            ttk.Button(send_frame, text="Copy JSON", command=self._copy_json),
        ]
        for idx, btn in enumerate(self.ai_buttons):
            pad = 0 if idx == 0 else 4
            btn.pack(side="left", padx=pad)
        self._toggle_ai_ui()

        # Logs
        self.log_box = tk.Text(self, height=6, state="disabled")
        self.log_box.pack(fill="x", padx=10, pady=6)

    def refresh_market(self) -> None:
        snapshot = self.app.fetch_market_snapshot(self.symbol)
        if snapshot:
            pair_meta = next((p for p in self.app.pairs if p.get("symbol") == self.symbol), {})
            tick_size = pair_meta.get("tick_size")
            self.market_labels["last"].set(format_price(snapshot.last_price, tick_size))
            self.market_labels["bid"].set(format_price(snapshot.bid, tick_size))
            self.market_labels["ask"].set(format_price(snapshot.ask, tick_size))
            self.market_labels["spread"].set(format_spread(snapshot.spread))
            spread_points = snapshot.ask - snapshot.bid if snapshot.ask is not None and snapshot.bid is not None else None
            self.market_labels["spread_points"].set(format_price(spread_points, tick_size))
            self.market_labels["volume"].set(format_volume(snapshot.volume_24h))
            self.filters_vars["tick"].set(pair_meta.get("tick_size", "-"))
            self.filters_vars["step"].set(pair_meta.get("step_size", "-"))
            min_notional = pair_meta.get("min_notional")
            self.filters_vars["min_notional"].set(min_notional if min_notional is not None else "N/A")
            self.conn_status.set("REST OK")
        else:
            self.conn_status.set("REST error")
        self._render_preview()
        self._schedule_auto_refresh()

    def _render_preview(self) -> None:
        data = {k: self._parse_value(v.get()) for k, v in self.settings_vars.items()}
        text = json.dumps(data, indent=2)
        self._set_text(self.preview, text)
        self._validate_settings()

    def _on_start(self) -> None:
        self.app.state.set_state(AppState.RUNNING)
        self._log("Bot started in paper mode")
        self.app.refresh_status_bar()

    def _on_stop(self) -> None:
        self.app.state.set_state(AppState.STOPPED)
        self._log("Bot stopped")
        self.app.refresh_status_bar()

    def _on_send(self) -> None:
        if not self.app.ai_client.can_run_live():
            messagebox.showinfo("AI", "OpenAI key not configured")
            return
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

    def _copy_effective_settings(self) -> None:
        payload = self.preview.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(payload)
        self._log("Copied effective settings")

    def _parse_value(self, value: str):
        try:
            if value is None:
                return None
            if "." in str(value):
                return float(value)
            return int(value)
        except ValueError:
            return value

    def _apply_preset(self, preset: str) -> None:
        presets = {
            "conservative": {
                "budget_usdt": 50,
                "max_orders": 3,
                "grid_step_pct": 0.2,
                "take_profit_pct": 0.6,
                "stop_loss_pct": 1.5,
                "cooldown_seconds": 45,
                "update_interval_ms": 3000,
            },
            "normal": {
                "budget_usdt": 100,
                "max_orders": 5,
                "grid_step_pct": 0.35,
                "take_profit_pct": 0.9,
                "stop_loss_pct": 2.0,
                "cooldown_seconds": 30,
                "update_interval_ms": 2000,
            },
            "aggressive": {
                "budget_usdt": 200,
                "max_orders": 8,
                "grid_step_pct": 0.5,
                "take_profit_pct": 1.2,
                "stop_loss_pct": 3.0,
                "cooldown_seconds": 15,
                "update_interval_ms": 1000,
            },
        }
        values = presets.get(preset, {})
        for key, val in values.items():
            if key in self.settings_vars:
                self.settings_vars[key].set(str(val))
        self._render_preview()
        self._log(f"Applied {preset} preset")

    def _validate_settings(self) -> None:
        errors = {}
        for key, var in self.settings_vars.items():
            value = var.get().strip()
            try:
                parsed = float(value) if "." in value else int(value)
                if parsed < 0:
                    errors[key] = "Must be >= 0"
            except ValueError:
                errors[key] = "Invalid number"
        for key, label in self.validation_labels.items():
            label.config(text=errors.get(key, ""))

    def _toggle_auto_refresh(self) -> None:
        if self.auto_refresh_var.get():
            self._schedule_auto_refresh()
        else:
            if self.auto_refresh_job:
                self.after_cancel(self.auto_refresh_job)
                self.auto_refresh_job = None

    def _schedule_auto_refresh(self) -> None:
        if not self.auto_refresh_var.get():
            return
        if self.auto_refresh_job:
            self.after_cancel(self.auto_refresh_job)
        try:
            delay = int(self.auto_refresh_interval.get())
        except ValueError:
            delay = 2000
        self.auto_refresh_job = self.after(delay, self.refresh_market)

    def _attach_tooltip(self, widget: ttk.Label, text: str) -> None:
        tooltip = tk.Toplevel(widget)
        tooltip.withdraw()
        tooltip.overrideredirect(True)
        tooltip_label = tk.Label(tooltip, text=text, background="#2d2f36", foreground="white", padx=6, pady=4, relief="solid")
        tooltip_label.pack()

        def show(_event):
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20
            tooltip.geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def hide(_event):
            tooltip.withdraw()

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def _toggle_ai_ui(self) -> None:
        configured = self.app.config_service.config.api_keys.openai_key is not None and self.app.config_service.config.api_keys.openai_key != ""
        state = "normal" if configured else "disabled"
        self.chat_input.config(state=state)
        if configured:
            self.ai_status_label.config(text="AI ready")
            self.setup_ai_btn.pack_forget()
        else:
            self.ai_status_label.config(text="AI not configured")
            self.setup_ai_btn.pack(anchor="w", padx=6)
            self.chat_input.delete(0, "end")
        for btn in self.ai_buttons:
            btn.config(state=state)

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

