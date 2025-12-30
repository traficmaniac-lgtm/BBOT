from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict, List


class PairSelectScreen(ttk.Frame):
    def __init__(self, master, app) -> None:
        super().__init__(master)
        self.app = app
        self.pairs: List[Dict] = []
        self.filtered: List[Dict] = []
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
        self.quote_combo = ttk.Combobox(filters, textvariable=self.quote_var, values=["ALL", "USDT", "FDUSD", "BUSD", "USDC"], state="readonly", width=8)
        self.quote_combo.bind("<<ComboboxSelected>>", lambda *_: self._apply_filters())
        self.quote_combo.pack(side="left")

        self.fee_only_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(filters, text="Fee-Free only", variable=self.fee_only_var, command=self._apply_filters).pack(
            side="left", padx=(10, 0)
        )

        columns = ("symbol", "last", "spread", "volume", "status", "fee_free")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        headings = {
            "symbol": "Symbol",
            "last": "Last",
            "spread": "Spread",
            "volume": "24h Vol",
            "status": "Status",
            "fee_free": "FeeFree",
        }
        for col, label in headings.items():
            self.tree.heading(col, text=label)
            self.tree.column(col, width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=12, pady=8)

        action = ttk.Frame(self)
        action.pack(fill="x", padx=12, pady=6)
        ttk.Button(action, text="Select Pair", command=self._on_select).pack(side="right")
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
        self.filtered = []
        for pair in self.pairs:
            if term and term not in pair.get("symbol", "").lower():
                continue
            if quote != "ALL" and pair.get("quote", "") != quote:
                continue
            if fee_only and not pair.get("fee_free"):
                continue
            self.filtered.append(pair)
        for item in self.tree.get_children():
            self.tree.delete(item)
        for pair in self.filtered:
            self.tree.insert(
                "",
                "end",
                values=(
                    pair.get("symbol"),
                    pair.get("last"),
                    pair.get("spread"),
                    pair.get("volume"),
                    pair.get("status"),
                    pair.get("fee_free"),
                ),
            )

    def _on_select(self) -> None:
        selection = self.tree.selection()
        if not selection:
            self.status.set("Select a pair first")
            return
        values = self.tree.item(selection[0], "values")
        symbol = values[0]
        self.app.select_pair(symbol)

