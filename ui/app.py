"""
Schwarzschild Geodesic Explorer — Tkinter UI
=============================================
Launched via:  python main.py ui
               python -m ui.app          (direct)
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox
from typing import Optional

from core         import solver
from core.config  import OrbitalParams, SolverConfig, Solution
from render.style import STYLE
from ui.control_panel import ControlPanel
from ui.view_panel    import ViewPanel


class GeodesicApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("Schwarzschild Geodesic Explorer")
        self.configure(bg=STYLE.UI_BG)
        self.minsize(920, 640)
        self.resizable(True, True)

        # Improve text rendering on high-DPI displays
        try:
            self.tk.call("tk", "scaling", 1.5)
        except Exception:
            pass

        self._closing = False
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Shared slot for thread → main-thread communication
        self._pending_result: Optional[Solution]   = None
        self._pending_error:  Optional[Exception]  = None

        self._build_layout()

        # Fire the first preset once the window has fully rendered
        self.after(100, self._control.activate_first_preset)

    # ── layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._control = ControlPanel(self, on_run=self._on_run)
        self._control.grid(row=0, column=0, sticky="ns",
                           padx=(10, 0), pady=10)

        self._view = ViewPanel(self)
        self._view.grid(row=0, column=1, sticky="nsew",
                        padx=10, pady=10)

    # ── callback ──────────────────────────────────────────────────────────────

    def _on_run(self, params: OrbitalParams, cfg: SolverConfig) -> None:
        """
        Show the loading state immediately, then dispatch solver to a thread.
        """
        self._view.set_loading(True)
        self._control.set_running(True)

        # Clear any stale results
        self._pending_result = None
        self._pending_error  = None

        thread = threading.Thread(
            target=self._worker,
            args=(params, cfg),
            daemon=True,   # won't block app exit
        )
        thread.start()

    # ── background worker ─────────────────────────────────────────────────────

    def _worker(self, params: OrbitalParams, cfg: SolverConfig) -> None:
        """
        Runs on the worker thread.
        Deposits its outcome then schedules _on_result_ready on the main thread.
        """
        try:
            self._pending_result = solver.run(params, cfg)
        except Exception as exc:
            self._pending_error = exc
        finally:
            # after(0, …) is the only thread-safe Tkinter call
            self.after(0, self._on_result_ready)

    # ── result handler ─────────────────────────────────────────────────────

    def _on_result_ready(self) -> None:
        """
        Called on the main thread once the worker finishes.
        Hides the overlay, re-enables the Run button, and shows the result.
        """
        if self._closing:
            return

        self._view.set_loading(False)
        self._control.set_running(False)

        if self._pending_error is not None:
            messagebox.showerror("Integration error", str(self._pending_error))
            return

        if self._pending_result is not None:
            self._view.display(self._pending_result)

    # ── close handler ─────────────────────────────────────────────────────
    def _on_close(self) -> None:
        """Cleanly destroy the window and let the process exit."""
        self._closing = True
        self.destroy()


# ── entry point ───────────────────────────────────────────────────────────────

def launch() -> None:
    """Start the Tkinter event loop."""
    app = GeodesicApp()
    app.mainloop()


if __name__ == "__main__":
    launch()