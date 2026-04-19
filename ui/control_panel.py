"""
ui/control_panel.py
===================
The left sidebar of the Geodesic Explorer.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Callable

from core.config  import OrbitalParams, SolverConfig
from core.presets import PRESETS, list_presets
from render.style import STYLE
from ui.widgets   import (
    ActionButton,
    LabeledSlider,
    LogSlider,
    SectionLabel,
    Separator,
    ToggleStrip,
)

_BG   = STYLE.UI_PANEL_BG
_TEXT = STYLE.UI_TEXT
_MUTE = STYLE.UI_TEXT_MUTED
_ACC  = STYLE.UI_ACCENT
_BRD  = STYLE.UI_BORDER
_BG_W = STYLE.UI_BG


def _preset_display_names() -> dict[str, str]:
    """Map capitalised display name → lower-case registry key."""
    return {name.capitalize(): name for name, _ in list_presets()}


def _preset_params(key: str) -> dict:
    p = PRESETS[key]
    return dict(
        r0        = p.orbital.r0_rs,
        speed     = p.orbital.speed_frac,
        angle     = p.orbital.angle_deg,
        tau       = p.solver.tau_max,
        step_size = p.solver.step_size,
        solver    = p.solver.solver,
    )


class ControlPanel(tk.Frame):
    """
    Self-contained left sidebar.

    Parameters
    ----------
    parent      The parent tk widget.
    on_run      Callback(OrbitalParams, SolverConfig) fired on every run.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_run: Callable[[OrbitalParams, SolverConfig], None],
    ):
        super().__init__(parent, bg=_BG, bd=0,
                         highlightthickness=1,
                         highlightbackground=_BRD)
        self._on_run        = on_run
        self._display_names = _preset_display_names()
        self._preset_btns: dict[str, tk.Button] = {}
        self._run_btn: ActionButton | None = None

        self._build()

    def set_running(self, running: bool) -> None:
        """
        Lock / unlock the Run button while the solver is on a background thread.
        Prevents double-submission and gives clear visual feedback.
        """
        if self._run_btn is not None:
            self._run_btn.set_state(not running)
            label = "⏳  Integrating…" if running else "▶  Integrate geodesic"
            self._run_btn.config(text=label)

    def activate_first_preset(self) -> None:
        """Programmatically trigger the first preset (called at startup)."""
        first = next(iter(self._display_names))
        self._apply_preset(first)

    # construction

    def _build(self) -> None:
        self._build_header()
        Separator(self).pack()
        self._build_presets()
        Separator(self).pack()
        self._build_parameters()
        Separator(self).pack()
        self._build_solver()
        Separator(self).pack()
        self._build_run_btn()

    def _build_header(self) -> None:
        tk.Label(self, text="Schwarzschild",
                 font=STYLE.FONT_TITLE, bg=_BG, fg=_TEXT,
                 ).pack(anchor="w", padx=16, pady=(16, 0))
        tk.Label(self, text="Geodesic Explorer",
                 font=STYLE.FONT_SUBTITLE, bg=_BG, fg=_MUTE,
                 ).pack(anchor="w", padx=16, pady=(0, 10))

    def _build_presets(self) -> None:
        SectionLabel(self, "Presets").pack(anchor="w", padx=16, pady=(8, 4))

        grid = tk.Frame(self, bg=_BG)
        grid.pack(fill="x", padx=16, pady=(0, 4))

        for i, display_name in enumerate(self._display_names):
            btn = tk.Button(
                grid,
                text=display_name,
                font=STYLE.FONT_SMALL,
                bg=_BRD, fg=_MUTE,
                activebackground=_ACC,
                activeforeground=_BG_W,
                relief="flat", cursor="hand2",
                padx=6, pady=4,
                command=lambda n=display_name: self._apply_preset(n),
            )
            btn.grid(row=i // 2, column=i % 2, padx=2, pady=2, sticky="ew")
            grid.columnconfigure(i % 2, weight=1)
            self._preset_btns[display_name] = btn

    def _build_parameters(self) -> None:
        SectionLabel(self, "Parameters").pack(anchor="w", padx=16, pady=(8, 4))

        self._r0_var    = tk.DoubleVar(value=8.0)
        self._speed_var = tk.DoubleVar(value=1.0)
        self._angle_var = tk.DoubleVar(value=0.0)
        self._tau_var   = tk.DoubleVar(value=10_000.0)

        sliders: list[tuple] = [
            ("Initial radius",   self._r0_var,    2.0,    50.0,  "{:.1f} rs"),
            ("Speed (v/v_circ)", self._speed_var,  0.0,    2.0,   "{:.2f}×"),
            ("Launch angle",     self._angle_var, -90.0,  90.0,  "{:.0f}°"),
            ("Proper time τ",    self._tau_var,   100.0, 30_000.0, "{:.0f}"),
        ]
        for label, var, lo, hi, fmt in sliders:
            LabeledSlider(self, label, var, lo, hi, fmt).pack(
                fill="x", padx=16, pady=3)

    def _build_solver(self) -> None:
        SectionLabel(self, "Integrator").pack(anchor="w", padx=16, pady=(8, 4))

        # algorithm toggle
        self._solver_strip = ToggleStrip(
            self,
            options=[("RK4", "RK4"), ("RK45", "RK45"), ("DOP853", "DOP853")],
            on_select=lambda _v: None,   # value read lazily at run-time
            initial="DOP853",
        )
        self._solver_strip.pack(anchor="w", padx=16, pady=(0, 6))

        # step-size log slider
        # Range 0.01 → 10.0 spans three orders of magnitude; log scale makes
        # both fine (0.01–0.1) and coarse (1–10) ends equally accessible.
        self._step_slider = LogSlider(
            self,
            label="Step size / max step",
            min_val=0.01,
            max_val=10.0,
            initial=1.0,
            fmt="{:.3g}",
        )
        self._step_slider.pack(fill="x", padx=16, pady=(0, 10))

        # inline hint
        tk.Label(
            self,
            text="Smaller step → higher accuracy, slower run",
            font=STYLE.FONT_SMALL,
            bg=_BG, fg=_MUTE,
            wraplength=200,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(0, 6))

    def _build_run_btn(self) -> None:
        self._run_btn = ActionButton(
            self, "▶  Integrate geodesic",
            command=self._do_run, accent=True,
        )
        self._run_btn.pack(fill="x", padx=16, pady=(4, 16))

    def _apply_preset(self, display_name: str) -> None:
        for name, btn in self._preset_btns.items():
            active = name == display_name
            btn.config(
                bg=_ACC  if active else _BRD,
                fg=_BG_W if active else _MUTE,
            )

        key = self._display_names[display_name]
        p   = _preset_params(key)

        self._r0_var.set(p["r0"])
        self._speed_var.set(p["speed"])
        self._angle_var.set(p["angle"])
        self._tau_var.set(p["tau"])
        self._step_slider.set_real(p["step_size"])
        self._solver_strip.select(p["solver"])

        self._do_run()

    def _do_run(self) -> None:
        try:
            params = OrbitalParams(
                r0_rs      = self._r0_var.get(),
                speed_frac = self._speed_var.get(),
                angle_deg  = self._angle_var.get(),
            )
            cfg = SolverConfig(
                tau_max   = self._tau_var.get(),
                step_size = self._step_slider.real_value,
                solver    = self._solver_strip.value,
            )
        except ValueError as exc:
            messagebox.showerror("Invalid parameters", str(exc))
            return

        self._on_run(params, cfg)