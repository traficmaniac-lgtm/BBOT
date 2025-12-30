import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from ai.client import AiClient
from ai.prompt_builder import build_prompt
from core.config_service import ConfigService
from core.logger import setup_logger
from core.state import AppState, StateMachine
from exchanges.binance_client import BinanceClient
from exchanges.pairs_loader import PairLoader
from risk.rules import validate_risk


class BBOTApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("BBOT Desktop Copilot")
        self.state = StateMachine()
        self.config_service = ConfigService()
        self.logger = setup_logger(level=self.config_service.config.app.log_level)
        self.binance_client = BinanceClient(
            api_key=self.config_service.config.api_keys.exchange_key,
            api_secret=self.config_service.config.api_keys.exchange_secret,
            testnet=self.config_service.config.app.testnet,
            logger=self.logger,
        )
        self.ai_client = AiClient(self.state, self.logger, mock=True)
        self.pairs = []
        self.filtered_pairs = []

        self._build_layout()
        self._refresh_status()

    # Layout
    def _build_layout(self) -> None:
        self.status_var = tk.StringVar()
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side="left", padx=5, pady=5)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.dashboard_frame = ttk.Frame(self.notebook)
        self.pairs_frame = ttk.Frame(self.notebook)
        self.ai_frame = ttk.Frame(self.notebook)
        self.trading_frame = ttk.Frame(self.notebook)
        self.risk_frame = ttk.Frame(self.notebook)
        self.logs_frame = ttk.Frame(self.notebook)
        self.settings_frame = ttk.Frame(self.notebook)

        for name, frame in [
            ("Dashboard", self.dashboard_frame),
            ("Pairs", self.pairs_frame),
            ("AI", self.ai_frame),
            ("Trading", self.trading_frame),
            ("Risk", self.risk_frame),
            ("Logs", self.logs_frame),
            ("Settings", self.settings_frame),
        ]:
            self.notebook.add(frame, text=name)

        self._build_dashboard_tab()
        self._build_pairs_tab()
        self._build_ai_tab()
        self._build_trading_tab()
        self._build_risk_tab()
        self._build_logs_tab()
        self._build_settings_tab()

    def _build_dashboard_tab(self) -> None:
        self.dashboard_status = tk.StringVar()
        ttk.Label(self.dashboard_frame, text="System overview", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        ttk.Label(self.dashboard_frame, textvariable=self.dashboard_status, wraplength=500).pack(anchor="w", padx=10)
        ttk.Button(self.dashboard_frame, text="Refresh", command=self._refresh_dashboard).pack(anchor="w", padx=10, pady=5)

    def _build_pairs_tab(self) -> None:
        control_frame = ttk.Frame(self.pairs_frame)
        control_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(control_frame, text="Load pairs from Binance", command=self._load_pairs).pack(side="left")

        ttk.Label(control_frame, text="Search:").pack(side="left", padx=(10, 2))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self._filter_pairs())
        ttk.Entry(control_frame, textvariable=self.filter_var, width=18).pack(side="left")

        ttk.Label(control_frame, text="Quote:").pack(side="left", padx=(10, 2))
        self.quote_filter_var = tk.StringVar(value="ALL")
        self.quote_filter = ttk.Combobox(
            control_frame,
            textvariable=self.quote_filter_var,
            values=["ALL", "USDT", "USDC", "FDUSD"],
            width=8,
            state="readonly",
        )
        self.quote_filter.bind("<<ComboboxSelected>>", lambda *_: self._filter_pairs())
        self.quote_filter.pack(side="left")

        self.fee_free_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            control_frame,
            text="Fee-Free only",
            variable=self.fee_free_only_var,
            command=self._filter_pairs,
        ).pack(side="left", padx=(10, 0))

        self.pairs_tree = ttk.Treeview(
            self.pairs_frame,
            columns=("symbol", "base", "quote", "fee_free", "fee_method"),
            show="headings",
        )
        headings = {
            "symbol": "Symbol",
            "base": "Base",
            "quote": "Quote",
            "fee_free": "FeeFree",
            "fee_method": "FeeMethod",
        }
        for col, label in headings.items():
            self.pairs_tree.heading(col, text=label)
            self.pairs_tree.column(col, stretch=True, width=100)
        self.pairs_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.pairs_tree.bind("<<TreeviewSelect>>", self._on_pair_select)

    def _build_ai_tab(self) -> None:
        ttk.Label(self.ai_frame, text="Prompt preview:").pack(anchor="w", padx=10, pady=(10, 2))
        self.prompt_text = tk.Text(self.ai_frame, height=5, state="disabled")
        self.prompt_text.pack(fill="x", padx=10)

        ttk.Button(self.ai_frame, text="Run AI analysis", command=self._run_ai).pack(anchor="w", padx=10, pady=5)

        ttk.Label(self.ai_frame, text="AI JSON response:").pack(anchor="w", padx=10, pady=(10, 2))
        self.ai_response_text = tk.Text(self.ai_frame, height=10, state="disabled")
        self.ai_response_text.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        ttk.Button(self.ai_frame, text="Apply settings", command=self._apply_ai_settings).pack(anchor="e", padx=10, pady=5)

    def _build_trading_tab(self) -> None:
        self.trading_vars = {
            "budget_usdt": tk.StringVar(value=str(self.config_service.config.trading.budget_usdt)),
            "leverage": tk.StringVar(value=str(self.config_service.config.trading.leverage)),
            "timeframe": tk.StringVar(value=self.config_service.config.trading.timeframe),
            "take_profit_pct": tk.StringVar(value=str(self.config_service.config.trading.take_profit_pct)),
            "stop_loss_pct": tk.StringVar(value=str(self.config_service.config.trading.stop_loss_pct)),
        }
        row = 0
        for label, key in [
            ("Budget (USDT)", "budget_usdt"),
            ("Leverage", "leverage"),
            ("Timeframe", "timeframe"),
            ("Take profit %", "take_profit_pct"),
            ("Stop loss %", "stop_loss_pct"),
        ]:
            ttk.Label(self.trading_frame, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=2)
            ttk.Entry(self.trading_frame, textvariable=self.trading_vars[key]).grid(row=row, column=1, sticky="we", padx=10, pady=2)
            row += 1
        self.trading_frame.grid_columnconfigure(1, weight=1)

        self.run_status_var = tk.StringVar(value="STOPPED")
        ttk.Label(self.trading_frame, text="Status:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        ttk.Label(self.trading_frame, textvariable=self.run_status_var, foreground="green").grid(row=row, column=1, sticky="w", padx=10)
        row += 1

        button_frame = ttk.Frame(self.trading_frame)
        button_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        ttk.Button(button_frame, text="Start", command=self._start_trading).pack(side="left")
        ttk.Button(button_frame, text="Stop", command=self._stop_trading).pack(side="left", padx=5)

    def _build_risk_tab(self) -> None:
        self.risk_vars = {
            "max_drawdown_pct": tk.StringVar(value=str(self.config_service.config.risk.max_drawdown_pct)),
            "per_trade_risk_pct": tk.StringVar(value=str(self.config_service.config.risk.per_trade_risk_pct)),
            "max_concurrent_trades": tk.StringVar(value=str(self.config_service.config.risk.max_concurrent_trades)),
        }
        row = 0
        for label, key in [
            ("Max drawdown %", "max_drawdown_pct"),
            ("Per trade risk %", "per_trade_risk_pct"),
            ("Max concurrent trades", "max_concurrent_trades"),
        ]:
            ttk.Label(self.risk_frame, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=2)
            ttk.Entry(self.risk_frame, textvariable=self.risk_vars[key]).grid(row=row, column=1, sticky="we", padx=10, pady=2)
            row += 1
        self.risk_frame.grid_columnconfigure(1, weight=1)
        ttk.Button(self.risk_frame, text="Validate", command=self._validate_risk).grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="w")

    def _build_logs_tab(self) -> None:
        self.log_text = tk.Text(self.logs_frame, state="disabled")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)
        ttk.Button(self.logs_frame, text="Export", command=self._export_logs).pack(anchor="e", padx=10, pady=5)

    def _build_settings_tab(self) -> None:
        cfg = self.config_service.config
        self.settings_vars = {
            "exchange_key": tk.StringVar(value=cfg.api_keys.exchange_key),
            "exchange_secret": tk.StringVar(value=cfg.api_keys.exchange_secret),
            "openai_key": tk.StringVar(value=cfg.api_keys.openai_key),
            "exchange": tk.StringVar(value=cfg.app.exchange),
            "testnet": tk.BooleanVar(value=cfg.app.testnet),
            "mode": tk.StringVar(value=cfg.app.mode),
        }

        row = 0
        for label, key in [
            ("Exchange key", "exchange_key"),
            ("Exchange secret", "exchange_secret"),
            ("OpenAI key", "openai_key"),
        ]:
            ttk.Label(self.settings_frame, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=2)
            mask_field = "*" if "key" in key or "secret" in key else None
            ttk.Entry(self.settings_frame, textvariable=self.settings_vars[key], show=mask_field).grid(
                row=row, column=1, sticky="we", padx=10, pady=2
            )
            row += 1

        ttk.Label(self.settings_frame, text="Exchange").grid(row=row, column=0, sticky="w", padx=10, pady=2)
        ttk.Combobox(self.settings_frame, textvariable=self.settings_vars["exchange"], values=["binance", "okx", "bybit"], state="readonly").grid(row=row, column=1, sticky="we", padx=10, pady=2)
        row += 1

        ttk.Label(self.settings_frame, text="Mode (mock/live)").grid(row=row, column=0, sticky="w", padx=10, pady=2)
        ttk.Combobox(self.settings_frame, textvariable=self.settings_vars["mode"], values=["mock", "live"], state="readonly").grid(row=row, column=1, sticky="we", padx=10, pady=2)
        row += 1

        ttk.Checkbutton(self.settings_frame, text="Use testnet", variable=self.settings_vars["testnet"]).grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        row += 1

        ttk.Label(self.settings_frame, text="Active config:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.active_config_label = ttk.Label(self.settings_frame, text=self.config_service.active_config_name())
        self.active_config_label.grid(row=row, column=1, sticky="w", padx=10, pady=5)
        row += 1

        btn_frame = ttk.Frame(self.settings_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        ttk.Button(btn_frame, text="Save", command=self._save_config).pack(side="left")
        ttk.Button(btn_frame, text="Load", command=self._load_config).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Test Exchange", command=self._test_exchange).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Test OpenAI", command=self._test_openai).pack(side="left", padx=5)

        self.settings_frame.grid_columnconfigure(1, weight=1)

    # Actions
    def _refresh_status(self) -> None:
        exchange_status = "Connected" if self.pairs else "Not loaded"
        ai_status = (
            "Ready" if self.config_service.config.api_keys.openai_key else "Mock (no key)"
        )
        self.status_var.set(
            " | ".join(
                [
                    f"State: {self.state.state}",
                    f"Pair: {self.config_service.config.app.active_pair}",
                    f"Exchange: {exchange_status}",
                    f"AI: {ai_status}",
                    f"Active config: {self.config_service.active_config_name()}",
                ]
            )
        )
        prompt = build_prompt(self.config_service.config)
        self._set_text(self.prompt_text, prompt)
        self._refresh_dashboard()

    def _refresh_dashboard(self) -> None:
        cfg = self.config_service.config
        summary = (
            f"Exchange: {cfg.app.exchange} ({'testnet' if cfg.app.testnet else 'live'}), mode={cfg.app.mode}\n"
            f"AI client: {self.ai_client.describe()}\n"
            f"Active pair: {cfg.app.active_pair} | Loaded pairs: {len(self.pairs)}\n"
            f"Trading: budget {cfg.trading.budget_usdt} USDT, TP {cfg.trading.take_profit_pct}% / SL {cfg.trading.stop_loss_pct}%\n"
            f"State: {self.state.state}"
        )
        self.dashboard_status.set(summary)

    def _load_pairs(self) -> None:
        cfg = self.config_service.config
        loader = PairLoader(
            self.binance_client,
            manual_fee_free=cfg.pairs.manual_fee_free,
            heuristic_quote_whitelist=cfg.pairs.heuristic_quote_whitelist,
            logger=self.logger,
        )
        self.pairs = loader.load()
        self._filter_pairs()
        self.state.set_state(AppState.PAIRS_LOADED)
        self._log("Loaded pairs from Binance (with fallback if needed)")

    def _filter_pairs(self) -> None:
        term = self.filter_var.get().lower()
        quote = self.quote_filter_var.get()
        fee_only = self.fee_free_only_var.get()
        self.filtered_pairs = []
        for pair in self.pairs:
            if term and term not in pair.get("symbol", "").lower():
                continue
            if quote != "ALL" and pair.get("quote", "").upper() != quote:
                continue
            if fee_only and not pair.get("fee_free"):
                continue
            self.filtered_pairs.append(pair)
        for item in self.pairs_tree.get_children():
            self.pairs_tree.delete(item)
        for pair in self.filtered_pairs:
            self.pairs_tree.insert(
                "",
                "end",
                values=(
                    pair.get("symbol"),
                    pair.get("base"),
                    pair.get("quote"),
                    pair.get("fee_free"),
                    pair.get("fee_method"),
                ),
            )

    def _on_pair_select(self, _event) -> None:
        selection = self.pairs_tree.selection()
        if not selection:
            return
        values = self.pairs_tree.item(selection[0], "values")
        if values:
            symbol = values[0]
            self.config_service.config.app.active_pair = symbol
            self.state.set_state(AppState.PAIRS_LOADED)
            self._refresh_status()
            self._log(f"Selected pair: {symbol}")
            self.notebook.select(self.trading_frame)

    def _run_ai(self) -> None:
        prompt = build_prompt(self.config_service.config)
        try:
            response = self.ai_client.run_analysis(prompt, retries=self.config_service.config.ai.max_retries)
            formatted = json.dumps(response, indent=2)
            self._set_text(self.ai_response_text, formatted)
            self._fill_trading_from_ai(response)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("AI error", str(exc))
        self._refresh_status()

    def _apply_ai_settings(self) -> None:
        try:
            data = json.loads(self.ai_response_text.get("1.0", "end"))
            self._fill_trading_from_ai(data)
            self._log("Applied AI settings to trading form")
        except json.JSONDecodeError:
            messagebox.showwarning("AI", "No valid AI JSON to apply")

    def _fill_trading_from_ai(self, payload: dict) -> None:
        for key in ["budget_usdt", "leverage", "timeframe", "take_profit_pct", "stop_loss_pct"]:
            if key in payload:
                self.trading_vars[key].set(str(payload[key]))
        self.state.set_state(AppState.AI_READY)
        self._refresh_dashboard()

    def _start_trading(self) -> None:
        self.state.set_state(AppState.RUNNING)
        self.run_status_var.set("RUNNING")
        self._log("Trading started (mock)")
        self._refresh_status()

    def _stop_trading(self) -> None:
        self.state.set_state(AppState.STOPPED)
        self.run_status_var.set("STOPPED")
        self._log("Trading stopped")
        self._refresh_status()

    def _validate_risk(self) -> None:
        settings = {k: float(v.get() or 0) for k, v in self.risk_vars.items()}
        result = validate_risk(settings)
        self._log(f"Risk validation: {result['status']} - {result['notes']}")

    def _export_logs(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".log", filetypes=[("Log files", "*.log")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.log_text.get("1.0", "end"))
        self._log(f"Logs exported to {path}")

    def _save_config(self) -> None:
        cfg = self.config_service.config
        cfg.api_keys.exchange_key = self.settings_vars["exchange_key"].get()
        cfg.api_keys.exchange_secret = self.settings_vars["exchange_secret"].get()
        cfg.api_keys.openai_key = self.settings_vars["openai_key"].get()
        cfg.app.exchange = self.settings_vars["exchange"].get()
        cfg.app.testnet = bool(self.settings_vars["testnet"].get())
        cfg.app.mode = self.settings_vars["mode"].get()
        cfg.app.active_pair = self.config_service.config.app.active_pair
        cfg.trading.budget_usdt = float(self.trading_vars["budget_usdt"].get() or 0)
        cfg.trading.leverage = int(float(self.trading_vars["leverage"].get() or 0))
        cfg.trading.timeframe = self.trading_vars["timeframe"].get()
        cfg.trading.take_profit_pct = float(self.trading_vars["take_profit_pct"].get() or 0)
        cfg.trading.stop_loss_pct = float(self.trading_vars["stop_loss_pct"].get() or 0)
        cfg.risk.max_drawdown_pct = float(self.risk_vars["max_drawdown_pct"].get() or 0)
        cfg.risk.per_trade_risk_pct = float(self.risk_vars["per_trade_risk_pct"].get() or 0)
        cfg.risk.max_concurrent_trades = int(float(self.risk_vars["max_concurrent_trades"].get() or 0))
        self.binance_client = BinanceClient(
            api_key=cfg.api_keys.exchange_key,
            api_secret=cfg.api_keys.exchange_secret,
            testnet=cfg.app.testnet,
            logger=self.logger,
        )
        try:
            self.config_service.save()
            self.state.set_state(AppState.CONFIGURED)
            self.active_config_label.config(text=self.config_service.active_config_name())
            self._log(f"Config saved to {self.config_service.active_config_name()}")
            messagebox.showinfo("Config", "Saved")
        except Exception as exc:  # noqa: BLE001
            self.state.set_state(AppState.ERROR, str(exc))
            messagebox.showerror("Config", str(exc))
        self._refresh_status()

    def _load_config(self) -> None:
        path_str = filedialog.askopenfilename(filetypes=[("YAML", "*.yaml"), ("YML", "*.yml")])
        if not path_str:
            return
        try:
            cfg = self.config_service.load(Path(path_str))
            # Update UI values
            self.settings_vars["exchange_key"].set(cfg.api_keys.exchange_key)
            self.settings_vars["exchange_secret"].set(cfg.api_keys.exchange_secret)
            self.settings_vars["openai_key"].set(cfg.api_keys.openai_key)
            self.settings_vars["exchange"].set(cfg.app.exchange)
            self.settings_vars["testnet"].set(cfg.app.testnet)
            self.settings_vars["mode"].set(cfg.app.mode)
            for key, var in self.trading_vars.items():
                var.set(str(getattr(cfg.trading, key)))
            for key, var in self.risk_vars.items():
                var.set(str(getattr(cfg.risk, key)))
            self.active_config_label.config(text=self.config_service.active_config_name())
            self.state.set_state(AppState.CONFIGURED)
            self._log(f"Loaded config {path_str}")
        except Exception as exc:  # noqa: BLE001
            self.state.set_state(AppState.ERROR, str(exc))
            messagebox.showerror("Load config", str(exc))
        self._refresh_status()

    def _test_exchange(self) -> None:
        self._log("Exchange connectivity test (mock): OK")
        messagebox.showinfo("Exchange", "Mock exchange test passed")

    def _test_openai(self) -> None:
        client_desc = self.ai_client.describe()
        self._log(f"OpenAI test using {client_desc}")
        messagebox.showinfo("OpenAI", f"Using {client_desc}")

    def _log(self, text: str) -> None:
        self.logger.info(text)
        self.log_text.config(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _set_text(self, widget: tk.Text, content: str) -> None:
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.config(state="disabled")


def run() -> None:
    root = tk.Tk()
    app = BBOTApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()

