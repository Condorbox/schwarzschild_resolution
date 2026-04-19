"""
view_panel.py
================
The right-hand display panel of the Geodesic Explorer.

Tabs
----
  2D Orbit       — polar canvas rendered natively in Tkinter (no Matplotlib).
  3D View        — Matplotlib 3-D figure embedded via FigureCanvasTkAgg.
  Phase Space    — r vs ṙ (dr/dτ) phase-space portrait, also via Matplotlib.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import TYPE_CHECKING

import tkinter as tk

from render.style import STYLE
from ui.widgets   import ComputingOverlay, StatCard, TabBar

if TYPE_CHECKING:
    from core.config import Solution

# Suppress noisy Matplotlib config warnings in sandboxed environments
if "MPLCONFIGDIR" not in os.environ:
    _mpl_tmp = Path("/tmp/matplotlib_ui")
    _mpl_tmp.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(_mpl_tmp)


_BG   = STYLE.UI_BG
_BRD  = STYLE.UI_BORDER
_TEXT = STYLE.UI_TEXT
_MUTE = STYLE.UI_TEXT_MUTED
_ACC  = STYLE.UI_ACCENT
_CARD = STYLE.UI_CARD_BG


# 2-D polar orbit canvas
class _OrbitCanvas(tk.Frame):
    """Native Tkinter polar-orbit renderer."""

    _SIZE = 560

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=_BG)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(
            self,
            width=self._SIZE, height=self._SIZE,
            bg=STYLE.UI_CANVAS_BG,
            highlightthickness=1,
            highlightbackground=_BRD,
        )
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._canvas.bind("<Configure>", self._on_resize)
        self._solution: Solution | None = None
        self._draw_placeholder()


    def render(self, sol: Solution) -> None:
        self._solution = sol
        self._redraw()


    def _on_resize(self, _event) -> None:
        if self._solution:
            self._redraw()

    def _geometry(self):
        W = self._canvas.winfo_width()  or self._SIZE
        H = self._canvas.winfo_height() or self._SIZE
        return W, H, W / 2, H / 2

    @staticmethod
    def _polar_to_xy(r, phi, cx, cy, scale):
        return cx + r * math.cos(phi) * scale, cy - r * math.sin(phi) * scale

    def _draw_circle(self, cx, cy, r_rs, scale, **kw):
        n = 300
        pts = []
        for i in range(n + 1):
            a = 2 * math.pi * i / n
            x, y = self._polar_to_xy(r_rs, a, cx, cy, scale)
            pts += [x, y]
        self._canvas.create_line(*pts, **kw)

    def _draw_placeholder(self) -> None:
        cv = self._canvas
        cv.delete("all")
        _, _, cx, cy = self._geometry()
        cv.create_text(
            cx, cy,
            text="Select a preset or adjust parameters\nand press  ▶  Run",
            fill=_MUTE,
            font=STYLE.FONT_LABEL,
            justify="center",
        )

    def _redraw(self) -> None:
        sol = self._solution
        if sol is None:
            return

        cv = self._canvas
        cv.delete("all")
        W, H, cx, cy = self._geometry()

        r_max = sol.r_max * 1.15
        scale = (min(W, H) * 0.46) / r_max

        # faint grid rings
        step = max(1, int(r_max / 5))
        for gr in range(step, int(r_max) + step, step):
            self._draw_circle(cx, cy, gr, scale,
                              fill=STYLE.UI_GRID, width=1, smooth=True)

        # reference circles
        self._draw_circle(cx, cy, 1.5, scale,
                          fill=STYLE.UI_AMBER, width=1, dash=(4, 4), smooth=True)
        self._draw_circle(cx, cy, 3.0, scale,
                          fill=STYLE.UI_PURPLE, width=1, dash=(2, 3), smooth=True)

        # event horizon
        eh = 1.0 * scale
        cv.create_oval(cx - eh, cy - eh, cx + eh, cy + eh,
                       fill="#000000", outline="white", width=1.5)

        # trajectory
        pts = []
        for r, phi in zip(sol.r, sol.phi):
            x, y = self._polar_to_xy(r, phi, cx, cy, scale)
            pts += [x, y]
        if len(pts) >= 4:
            cv.create_line(*pts, fill=_ACC, width=2, smooth=True)

        # markers 
        sx, sy = self._polar_to_xy(sol.r[0],  sol.phi[0],  cx, cy, scale)
        ex, ey = self._polar_to_xy(sol.r[-1], sol.phi[-1], cx, cy, scale)

        cv.create_oval(sx - 5, sy - 5, sx + 5, sy + 5,
                       fill=STYLE.UI_GREEN, outline="")

        end_color = STYLE.UI_ORANGE if sol.plunged else STYLE.UI_PINK
        if sol.plunged:
            d = 5
            cv.create_line(ex-d, ey-d, ex+d, ey+d, fill=end_color, width=2)
            cv.create_line(ex+d, ey-d, ex-d, ey+d, fill=end_color, width=2)
        else:
            cv.create_oval(ex - 5, ey - 5, ex + 5, ey + 5,
                           fill=end_color, outline="")

        # ── r labels ──
        for gr in range(step, int(r_max) + step, step):
            lx, ly = self._polar_to_xy(gr, math.pi * 0.25, cx, cy, scale)
            cv.create_text(lx, ly, text=f"{gr} rs",
                           fill=_MUTE, font=STYLE.FONT_CANVAS_TICK)

        # in-canvas legend
        legend = [
            (STYLE.UI_AMBER,  "Photon sphere 1.5 rs"),
            (STYLE.UI_PURPLE, "ISCO 3.0 rs"),
            (STYLE.UI_GREEN,  "Start"),
            (STYLE.UI_ORANGE if sol.plunged else STYLE.UI_PINK,
             "End (plunge)" if sol.plunged else "End"),
        ]
        ly0 = H - 10 - len(legend) * 16
        for colour, label in legend:
            cv.create_rectangle(10, ly0, 18, ly0+8, fill=colour, outline="")
            cv.create_text(24, ly0+4, text=label, anchor="w",
                           fill=_MUTE, font=STYLE.FONT_CANVAS_TICK)
            ly0 += 16


# 3-D view
class _View3D(tk.Frame):
    """Matplotlib 3-D geodesic plot embedded in a Tkinter frame."""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=_BG)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # inclination slider 
        ctrl = tk.Frame(self, bg=_BG)
        ctrl.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 0))

        tk.Label(ctrl, text="Inclination",
                 font=STYLE.FONT_LABEL, bg=_BG, fg=_MUTE).pack(side="left")

        self._inc_var = tk.DoubleVar(value=30.0)
        self._inc_lbl = tk.Label(ctrl, text="30°",
                                 font=STYLE.FONT_LABEL_BOLD, bg=_BG, fg=_TEXT)
        self._inc_lbl.pack(side="right")

        import tkinter.ttk as ttk
        ttk.Scale(ctrl, from_=0, to=90, variable=self._inc_var,
                  orient="horizontal",
                  command=self._on_inc_change).pack(
            side="left", fill="x", expand=True, padx=8)

        self._inc_var.trace_add("write", lambda *_: self._inc_lbl.config(
            text=f"{self._inc_var.get():.0f}°"))

        # placeholder label
        self._placeholder = tk.Label(
            self, text="Run an integration to see the 3D view.",
            font=STYLE.FONT_LABEL, bg=_BG, fg=_MUTE,
        )
        self._placeholder.grid(row=1, column=0)

        self._mpl_canvas = None
        self._fig        = None
        self._ax         = None
        self._solution: Solution | None = None


    def render(self, sol: Solution) -> None:
        self._solution = sol
        self._redraw()


    def _on_inc_change(self, _val=None) -> None:
        if self._solution is not None:
            self._redraw()

    def _ensure_figure(self) -> None:
        if self._fig is not None:
            return

        import matplotlib
        matplotlib.use("TkAgg")
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

        self._placeholder.grid_forget()
        self._fig = plt.figure(figsize=(7, 6), facecolor=STYLE.UI_CANVAS_BG)
        self._ax  = self._fig.add_subplot(111, projection="3d",
                                           facecolor=STYLE.UI_CANVAS_BG)
        canvas = FigureCanvasTkAgg(self._fig, master=self)
        canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")
        self._mpl_canvas = canvas

    def _redraw(self) -> None:
        import numpy as np
        from render.plot3d import to_cartesian

        sol = self._solution
        inc = self._inc_var.get()
        self._ensure_figure()

        ax  = self._ax
        ax.cla()
        ax.set_facecolor(STYLE.UI_CANVAS_BG)
        self._fig.patch.set_facecolor(STYLE.UI_CANVAS_BG)
        ax.tick_params(colors=_MUTE, labelsize=7)
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.pane.fill = False
            axis.pane.set_edgecolor(STYLE.GRID_COLOR)
            axis.label.set_color(_MUTE)

        r_max = sol.r_max * 1.15

        # event horizon sphere
        u = np.linspace(0, 2 * np.pi, 40)
        v = np.linspace(0, np.pi, 40)
        ax.plot_surface(
            np.outer(np.cos(u), np.sin(v)),
            np.outer(np.sin(u), np.sin(v)),
            np.outer(np.ones(40), np.cos(v)),
            color="#000000", alpha=1.0, zorder=5,
        )

        phi_ring = np.linspace(0, 2 * np.pi, 200)
        ax.plot(*to_cartesian(np.full_like(phi_ring, 1.5), phi_ring, inc),
                color=STYLE.PHOTON_SPHERE_COLOR, lw=1, ls="--", alpha=0.7)
        ax.plot(*to_cartesian(np.full_like(phi_ring, 3.0), phi_ring, inc),
                color=STYLE.ISCO_COLOR, lw=1, ls=":", alpha=0.7)

        xt, yt, zt = to_cartesian(sol.r, sol.phi, inc)
        ax.plot(xt, yt, zt,
                color=STYLE.TRAJECTORY_COLOR,
                lw=STYLE.TRAJECTORY_LW,
                alpha=STYLE.TRAJECTORY_ALPHA)

        ax.scatter([xt[0]],  [yt[0]],  [zt[0]],
                   color=STYLE.START_COLOR, s=40, zorder=10)
        end_c = STYLE.PLUNGE_COLOR if sol.plunged else STYLE.END_COLOR
        ax.scatter([xt[-1]], [yt[-1]], [zt[-1]],
                   color=end_c, marker="x" if sol.plunged else "^",
                   s=60, zorder=10)

        ax.set_xlim(-r_max, r_max)
        ax.set_ylim(-r_max, r_max)
        ax.set_zlim(-r_max * 0.6, r_max * 0.6)
        ax.set_xlabel("x (rs)", labelpad=4, fontsize=8)
        ax.set_ylabel("y (rs)", labelpad=4, fontsize=8)
        ax.set_zlabel("z (rs)", labelpad=4, fontsize=8)

        p = sol.params
        ax.set_title(
            f"3D View  —  r₀={p.r0_rs} rs  v={p.speed_frac} v_circ  "
            f"α={p.angle_deg}°  inc={inc:.0f}°",
            color=_TEXT, fontsize=8, pad=8,
        )
        self._mpl_canvas.draw()


# Phase-space portrait  r vs ṙ
class _PhaseSpace(tk.Frame):
    """r(τ) vs ṙ(τ) phase portrait."""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=_BG)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._placeholder = tk.Label(
            self, text="Run an integration to see the phase-space portrait.",
            font=STYLE.FONT_LABEL, bg=_BG, fg=_MUTE,
        )
        self._placeholder.grid(row=0, column=0)

        self._mpl_canvas = None
        self._fig        = None
        self._ax         = None


    def render(self, sol: Solution) -> None:
        self._ensure_figure()
        self._redraw(sol)


    def _ensure_figure(self) -> None:
        if self._fig is not None:
            return

        import matplotlib
        matplotlib.use("TkAgg")
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self._placeholder.grid_forget()
        self._fig, self._ax = plt.subplots(
            figsize=(7, 6), facecolor=STYLE.UI_CANVAS_BG)
        self._ax.set_facecolor(STYLE.UI_CANVAS_BG)
        canvas = FigureCanvasTkAgg(self._fig, master=self)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self._mpl_canvas = canvas

    def _redraw(self, sol: Solution) -> None:
        ax  = self._ax
        fig = self._fig
        ax.cla()
        ax.set_facecolor(STYLE.UI_CANVAS_BG)
        fig.patch.set_facecolor(STYLE.UI_CANVAS_BG)
        for spine in ax.spines.values():
            spine.set_edgecolor(STYLE.GRID_COLOR)
        ax.tick_params(colors=_MUTE, labelsize=8)

        n = len(sol.tau)
        for i in range(n - 1):
            alpha = i / n
            g = int(0xd4 * alpha)
            b = int(0xff - 0x64 * alpha)
            ax.plot(sol.r[i:i+2], sol.rdot[i:i+2],
                    color=f"#00{g:02x}{b:02x}", lw=1.2, alpha=0.85)

        ax.scatter([sol.r[0]],  [sol.rdot[0]],
                   color=STYLE.START_COLOR, s=50, zorder=5, label="Start")
        end_c = STYLE.PLUNGE_COLOR if sol.plunged else STYLE.END_COLOR
        ax.scatter([sol.r[-1]], [sol.rdot[-1]], color=end_c, s=50, zorder=5,
                   label="End (plunge)" if sol.plunged else "End")

        ax.axvline(3.0, color=STYLE.ISCO_COLOR,
                   lw=0.8, ls=":", alpha=0.6, label="ISCO (3 rs)")
        ax.axvline(1.5, color=STYLE.PHOTON_SPHERE_COLOR,
                   lw=0.8, ls="--", alpha=0.6, label="Photon sphere (1.5 rs)")
        ax.axhline(0, color=STYLE.GRID_COLOR, lw=0.6)

        ax.set_xlabel("r  (rs)",    color=_MUTE, fontsize=9)
        ax.set_ylabel("ṙ = dr/dτ", color=_MUTE, fontsize=9)
        ax.set_title("Phase Space  —  r vs ṙ", color=_TEXT, fontsize=9, pad=8)
        leg = ax.legend(fontsize=7, facecolor=_CARD,
                        edgecolor=_BRD, labelcolor=_TEXT)
        leg.get_frame().set_alpha(0.8)
        fig.tight_layout()
        self._mpl_canvas.draw()


# Stats bar
class _StatsBar(tk.Frame):

    _CARDS = [
        ("steps",  "Steps"),
        ("r_min",  "r min"),
        ("r_max",  "r max"),
        ("status", "Status"),
        ("time",   "Time"),
    ]

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=_BG)
        self._cards: dict[str, StatCard] = {}
        for key, label in self._CARDS:
            card = StatCard(self, label)
            card.pack(side="left", fill="x", expand=True, padx=(0, 3))
            self._cards[key] = card

    def update(self, sol: Solution) -> None:
        self._cards["steps"].set(f"{sol.n_steps:,}")
        self._cards["r_min"].set(f"{sol.r_min:.2f} rs")
        self._cards["r_max"].set(f"{sol.r_max:.2f} rs")
        self._cards["time"].set(f"{sol.elapsed_ms:.1f} ms")
        if sol.plunged:
            self._cards["status"].set("Plunged",  STYLE.UI_ORANGE)
        else:
            self._cards["status"].set("Orbiting", STYLE.UI_GREEN)


class ViewPanel(tk.Frame):
    """
    The right-hand display area.

    Layout
    ------
    ┌─────────────────────────────────────┐
    │  Stats bar  (5 cards)               │
    ├─────────────────────────────────────┤
    │  Tab bar  [ 2D Orbit | 3D | Phase ] │
    ├─────────────────────────────────────┤
    │  Active tab content (fills rest)    │
    └─────────────────────────────────────┘

    Public API
    ----------
    display(solution)       — render result into all tabs + update stats.
    set_loading(bool)       — show/hide the ComputingOverlay.
    """

    _TABS = [
        ("2d",    "2D Orbit"),
        ("3d",    "3D View"),
        ("phase", "Phase Space"),
    ]

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=_BG)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # stats bar
        self._stats = _StatsBar(self)
        self._stats.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        # tab bar
        self._tab_bar = TabBar(self, self._TABS,
                               on_change=self._switch_tab,
                               initial="2d")
        self._tab_bar.grid(row=1, column=0, sticky="ew")
        tk.Frame(self, bg=_BRD, height=1).grid(row=1, column=0, sticky="sew")

        # content frame
        self._content = tk.Frame(self, bg=_BG)
        self._content.grid(row=2, column=0, sticky="nsew")
        self._content.columnconfigure(0, weight=1)
        self._content.rowconfigure(0, weight=1)

        self._views: dict[str, tk.Frame] = {
            "2d":    _OrbitCanvas(self._content),
            "3d":    _View3D(self._content),
            "phase": _PhaseSpace(self._content),
        }
        for view in self._views.values():
            view.grid(row=0, column=0, sticky="nsew")

        self._active_tab = "2d"
        self._raise_tab("2d")

        # computing overlay — sits above everything in _content
        self._overlay = ComputingOverlay(self._content)
        # (not placed yet; start() / stop() handle placement)

        self._solution: Solution | None = None


    def display(self, sol: Solution) -> None:
        """Render the solution and update the stats bar."""
        self._solution = sol
        self._stats.update(sol)
        self._render_tab(self._active_tab, sol)

    def set_loading(self, loading: bool) -> None:
        """
        Show or hide the computing overlay.

        Called from the main thread:
          - Before spawning the solver thread  → set_loading(True)
          - After the result arrives via after() → set_loading(False)
        """
        if loading:
            self._overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            # self._overlay.lift()   # ensure it sits above the tab views
            self._overlay.start()
        else:
            self._overlay.stop()   # hides itself via place_forget()


    def _switch_tab(self, tab_id: str) -> None:
        self._active_tab = tab_id
        self._raise_tab(tab_id)
        if self._solution is not None:
            self._render_tab(tab_id, self._solution)

    def _raise_tab(self, tab_id: str) -> None:
        self._views[tab_id].tkraise()

    def _render_tab(self, tab_id: str, sol: Solution) -> None:
        self._views[tab_id].render(sol)