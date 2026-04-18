"""
Schwarzschild Geodesic Explorer — Tkinter UI
=============================================
Launched via:  python main.py ui
               python -m ui.app          (direct)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from core         import solver
from core.config  import OrbitalParams, SolverConfig
from render.style import STYLE
from ui.control_panel import ControlPanel
from ui.view_panel    import ViewPanel


class GeodesicApp(tk.Tk):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.title("Schwarzschild Geodesic Explorer")
        self.configure(bg=STYLE.UI_BG)
        self.minsize(900, 620)
        self.resizable(True, True)

        # Improve text rendering on high-DPI displays
        try:
            self.tk.call("tk", "scaling", 1.5)
        except Exception:
            pass

        self._build_layout()

        # Kick off the first integration once the window is fully rendered
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
        """Run the integrator and hand the solution to the view panel."""
        try:
            sol = solver.run(params, cfg)
        except Exception as exc:
            messagebox.showerror("Integration error", str(exc))
            return

        self._view.display(sol)


# ── entry point ───────────────────────────────────────────────────────────────

def launch() -> None:
    """Start the Tkinter event loop."""
    app = GeodesicApp()
    app.mainloop()


if __name__ == "__main__":
    launch()