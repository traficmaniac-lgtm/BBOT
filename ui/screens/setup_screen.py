from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class SetupScreen(ttk.Frame):
    def __init__(self, master, app) -> None:
        super().__init__(master)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(self, text="Setup keys", font=("Arial", 16, "bold")).pack(anchor="w", padx=12, pady=8)
        form = ttk.Frame(self)
        form.pack(fill="x", padx=14, pady=8)

        self.exchange_key = tk.StringVar(value=self.app.config_service.config.api_keys.exchange_key)
        self.exchange_secret = tk.StringVar(value=self.app.config_service.config.api_keys.exchange_secret)
        self.openai_key = tk.StringVar(value=self.app.config_service.config.api_keys.openai_key)
        self.testnet_var = tk.BooleanVar(value=self.app.config_service.config.app.testnet)

        for idx, (label, var, show) in enumerate(
            [
                ("Binance key", self.exchange_key, None),
                ("Binance secret", self.exchange_secret, "*"),
                ("OpenAI key", self.openai_key, "*"),
            ]
        ):
            ttk.Label(form, text=label).grid(row=idx, column=0, sticky="w", padx=6, pady=6)
            ttk.Entry(form, textvariable=var, show=show, width=60).grid(row=idx, column=1, sticky="we", padx=6, pady=6)
        form.grid_columnconfigure(1, weight=1)

        ttk.Checkbutton(form, text="Use Binance testnet", variable=self.testnet_var).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=6, pady=6
        )

        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=14, pady=8)
        ttk.Button(btns, text="Test Binance", command=self._on_test_binance).pack(side="left")
        ttk.Button(btns, text="Test OpenAI", command=self._on_test_openai).pack(side="left", padx=6)
        ttk.Button(btns, text="Save & Continue", command=self._on_save).pack(side="right")

        self.status = tk.StringVar()
        ttk.Label(self, textvariable=self.status, foreground="#4caf50").pack(anchor="w", padx=14)

    def _on_save(self) -> None:
        self.app.save_keys(
            self.exchange_key.get().strip(),
            self.exchange_secret.get().strip(),
            self.openai_key.get().strip(),
            bool(self.testnet_var.get()),
        )
        self.status.set("Saved.")

    def _on_test_binance(self) -> None:
        ok = self.app.test_binance()
        self.status.set("Binance OK" if ok else "Binance failed")

    def _on_test_openai(self) -> None:
        ok = self.app.test_openai()
        self.status.set("OpenAI OK" if ok else "OpenAI not ready")

