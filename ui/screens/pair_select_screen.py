from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict, List

from core.formatting import format_price, format_spread, format_volume


class PairSelectScreen(ttk.Frame):
    def __init__(self, master, app) -> None:
        super().__init__(master)
        self.app = app
        self.pairs: List[Dict] = []
        self.filtered: List[Dict] = []
        self.sort_column = "symbol"
        self.sort_desc = False
        self._build()

    def _build(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill="x", padx=12, pady=6)
        ttk.Label(header, text="Pair Select", font=("Arial", 16, "bold")).pack(side="left")
        ttk.Button(header, text="Refresh", command=self.load_pairs).pack(side="right")

        filters = ttk.Frame(self)
        filters.pack(fill="x", padx=12, pady=6)
        ttk.Label(filters, text="Search").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filters())
        ttk.Entry(filters, textvariable=self.search_var, width=20).pack(side="left", padx=4)

        ttk.Label(filters, text="Quote").pack(side="left", padx=(10, 2))
        self.quote_var = tk.StringVar(value="ALL")
        self.quote_combo = ttk.Combobox(
            filters,
            textvariable=self.quote_var,
            values=["ALL", "USDT", "USDC", "FDUSD", "BTC", "ETH"],
            state="readonly",
            width=8,
        )
        self.quote_combo.bind("<<ComboboxSelected>>", lambda *_: self._apply_filters())
        self.quote_combo.pack(side="left")

        self.fee_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filters, text="Fee-Free only", variable=self.fee_only_var, command=self._apply_filters).pack(
            side="left", padx=(10, 0)
        )

        self.trading_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filters, text="TRADING only", variable=self.trading_only_var, command=self._apply_filters).pack(
            side="left", padx=(10, 0)
        )

        columns = ("symbol", "last", "spread", "volume", "status", "fee_free", "fee_method")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        headings = {
            "symbol": "Symbol",
            "last": "Last",
            "spread": "Spread",
            "volume": "24h Vol",
            "status": "Status",
            "fee_free": "FeeFree",
            "fee_method": "FeeMethod",
        }
        for col, label in headings.items():
            self.tree.heading(col, text=label, command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=12, pady=8)
        self.tree.bind("<<TreeviewSelect>>", lambda *_: self._update_action_state())
        self.tree.bind("<Double-1>", lambda *_: self._on_select())

        action = ttk.Frame(self)
        action.pack(fill="x", padx=12, pady=6)
        self.select_btn = ttk.Button(action, text="Select Pair", command=self._on_select, state="disabled")
        self.select_btn.pack(side="right")
        self.status = tk.StringVar()
        ttk.Label(action, textvariable=self.status).pack(side="left")

    def load_pairs(self) -> None:
        try:
            self.pairs = self.app.fetch_pairs()
            self.status.set(f"Loaded {len(self.pairs)} pairs")
            self._apply_filters()
        except Exception as exc:  # noqa: BLE001
            self.status.set(f"Binance error: {exc}")

    def _apply_filters(self) -> None:
        term = self.search_var.get().lower()
        quote = self.quote_var.get()
        fee_only = self.fee_only_var.get()
        trading_only = self.trading_only_var.get()
        self.filtered = []
        for pair in self.pairs:
            if term and term not in pair.get("symbol", "").lower():
                continue
            if quote != "ALL" and pair.get("quote", "") != quote:
                continue
            if fee_only and not pair.get("fee_free"):
                continue
            if trading_only and pair.get("status") != "TRADING":
                continue
            self.filtered.append(pair)
        self._render_rows()

    def _render_rows(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        sorted_pairs = sorted(
            self.filtered,
            key=lambda p: self._sort_key(p, self.sort_column),
            reverse=self.sort_desc,
        )
        for pair in sorted_pairs:
            self.tree.insert(
                "",
                "end",
                values=(
                    pair.get("symbol"),
                    format_price(pair.get("last"), pair.get("tick_size")),
                    format_spread(pair.get("spread")),
                    format_volume(pair.get("volume")),
                    pair.get("status", "-"),
                    pair.get("fee_free") or "-",
                    pair.get("fee_method", "N/A"),
                ),
            )
        self._update_action_state()

    def _sort_key(self, pair: Dict, column: str):
        value_map = {
            "symbol": pair.get("symbol", ""),
            "last": float(pair.get("last") or 0),
            "spread": float(pair.get("spread") or 0),
            "volume": float(pair.get("volume") or 0),
            "status": pair.get("status", ""),
            "fee_free": str(pair.get("fee_free")),
            "fee_method": pair.get("fee_method", ""),
        }
        return value_map.get(column)

    def _sort_by(self, column: str) -> None:
        if self.sort_column == column:
            self.sort_desc = not self.sort_desc
        else:
            self.sort_column = column
            self.sort_desc = False
        self._render_rows()

    def _update_action_state(self) -> None:
        state = "normal" if self.tree.selection() else "disabled"
        self.select_btn.config(state=state)

    def _on_select(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self.status.set("Select a pair first")
            return
        values = self.tree.item(selection[0], "values")
        symbol = values[0]
        self.app.select_pair(symbol)

