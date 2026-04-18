"""
Schwarzschild Geodesic Explorer — Tkinter UI
=============================================
Launched via:  python main.py ui
               python -m ui.app          (direct)
"""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk, messagebox

from core import solver
from core.config import OrbitalParams, SolverConfig
from core.presets import PRESETS, list_presets
from render.style import STYLE

# ── pull UI tokens into local names so the rest of the file stays readable ───
BG         = STYLE.UI_BG
PANEL_BG   = STYLE.UI_PANEL_BG
BORDER     = STYLE.UI_BORDER
TEXT       = STYLE.UI_TEXT
TEXT_MUTED = STYLE.UI_TEXT_MUTED
ACCENT     = STYLE.UI_ACCENT
GREEN      = STYLE.UI_GREEN
PINK       = STYLE.UI_PINK
ORANGE     = STYLE.UI_ORANGE
AMBER      = STYLE.UI_AMBER
PURPLE     = STYLE.UI_PURPLE
CANVAS_BG  = STYLE.UI_CANVAS_BG
GRID       = STYLE.UI_GRID


# ── drawing helpers ───────────────────────────────────────────────────────────
def _polar_to_xy(r, phi, cx, cy, scale):
    return cx + r * math.cos(phi) * scale, cy - r * math.sin(phi) * scale


def _draw_circle(canvas, cx, cy, r_rs, scale, **kwargs):
    n   = 300
    pts = []
    for i in range(n + 1):
        a    = 2 * math.pi * i / n
        x, y = _polar_to_xy(r_rs, a, cx, cy, scale)
        pts += [x, y]
    canvas.create_line(*pts, **kwargs)


# ── preset helpers ────────────────────────────────────────────────────────────
def _preset_display_names() -> dict[str, str]:
    """Map title-cased display name → lower-case registry key."""
    return {name.capitalize(): name for name, _ in list_presets()}


def _get_preset_params(key: str) -> dict:
    """Return a flat dict of UI-friendly values for the given preset key."""
    p = PRESETS[key]
    return dict(
        r0    = p.orbital.r0_rs,
        speed = p.orbital.speed_frac,
        angle = p.orbital.angle_deg,
        tau   = p.solver.tau_max,
    )


# ── main application window ───────────────────────────────────────────────────
class GeodesicApp(tk.Tk):

    CANVAS_SIZE = 560

    def __init__(self):
        super().__init__()
        self.title("Schwarzschild Geodesic Explorer")
        self.configure(bg=BG)
        self.resizable(True, True)
        # Enable crisp text rendering on high-DPI displays (Windows / some Linux)
        try:
            self.tk.call("tk", "scaling", 1.5)
        except Exception:
            pass
        self._result = None
        self._display_names = _preset_display_names()
        self._build_ui()
        first = next(iter(self._display_names))
        self._apply_preset(first)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # ---- left panel ----
        left = tk.Frame(self, bg=PANEL_BG, bd=0, highlightthickness=1,
                        highlightbackground=BORDER)
        left.grid(row=0, column=0, sticky="ns", padx=(10, 0), pady=10)

        tk.Label(left, text="Schwarzschild",
                 font=STYLE.FONT_TITLE,
                 bg=PANEL_BG, fg=TEXT).pack(anchor="w", padx=14, pady=(14, 0))
        tk.Label(left, text="Geodesic Explorer",
                 font=STYLE.FONT_SUBTITLE,
                 bg=PANEL_BG, fg=TEXT_MUTED).pack(anchor="w", padx=14, pady=(0, 10))

        self._sep(left)

        # presets
        tk.Label(left, text="PRESETS",
                 font=STYLE.FONT_SMALL_BOLD,
                 bg=PANEL_BG, fg=TEXT_MUTED).pack(anchor="w", padx=14, pady=(8, 4))
        btn_row = tk.Frame(left, bg=PANEL_BG)
        btn_row.pack(fill="x", padx=14, pady=(0, 4))
        self._preset_btns: dict[str, tk.Button] = {}
        for i, display_name in enumerate(self._display_names):
            b = tk.Button(btn_row, text=display_name,
                          font=STYLE.FONT_SMALL,
                          bg=BORDER, fg=TEXT_MUTED,
                          activebackground=ACCENT, activeforeground=BG,
                          relief="flat", cursor="hand2",
                          padx=6, pady=3,
                          command=lambda n=display_name: self._apply_preset(n))
            b.grid(row=i // 2, column=i % 2, padx=2, pady=2, sticky="ew")
            btn_row.columnconfigure(i % 2, weight=1)
            self._preset_btns[display_name] = b

        self._sep(left)

        # sliders
        tk.Label(left, text="PARAMETERS",
                 font=STYLE.FONT_SMALL_BOLD,
                 bg=PANEL_BG, fg=TEXT_MUTED).pack(anchor="w", padx=14, pady=(8, 4))

        self._r0_var    = tk.DoubleVar(value=8.0)
        self._speed_var = tk.DoubleVar(value=1.0)
        self._angle_var = tk.DoubleVar(value=0.0)
        self._tau_var   = tk.DoubleVar(value=10000.0)

        self._mk_slider(left, "Initial radius (rs)", self._r0_var,    2.0, 50.0, "{:.1f} rs")
        self._mk_slider(left, "Speed (v / v_circ)",  self._speed_var, 0.0,  2.0, "{:.2f}")
        self._mk_slider(left, "Launch angle (°)",    self._angle_var, -90,  90,  "{:.0f}°")
        self._mk_slider(left, "Proper time τ",       self._tau_var,   100, 30000, "{:.0f}")

        self._sep(left)

        # integrator
        tk.Label(left, text="INTEGRATOR",
                 font=STYLE.FONT_SMALL_BOLD,
                 bg=PANEL_BG, fg=TEXT_MUTED).pack(anchor="w", padx=14, pady=(8, 4))
        self._solver_var = tk.StringVar(value="DOP853")
        solver_row = tk.Frame(left, bg=PANEL_BG)
        solver_row.pack(fill="x", padx=14, pady=(0, 8))
        for s in ("RK4", "RK45", "DOP853"):
            rb = tk.Radiobutton(solver_row, text=s,
                                variable=self._solver_var, value=s,
                                font=STYLE.FONT_RADIOLABEL,
                                bg=PANEL_BG, fg=TEXT,
                                selectcolor=PANEL_BG,
                                activebackground=PANEL_BG,
                                activeforeground=ACCENT,
                                indicatoron=True)
            rb.pack(side="left", padx=(0, 10))

        self._sep(left)

        # run button
        run_btn = tk.Button(left, text="▶  Integrate geodesic",
                            font=STYLE.FONT_BTN,
                            bg=ACCENT, fg=BG,
                            activebackground="#00b8d9", activeforeground=BG,
                            relief="flat", cursor="hand2",
                            padx=10, pady=8,
                            command=self._run)
        run_btn.pack(fill="x", padx=14, pady=(4, 14))

        # ---- right panel ----
        right = tk.Frame(self, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # stats row
        stats_frame = tk.Frame(right, bg=BG)
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._stat_steps  = self._mk_stat(stats_frame, "Steps")
        self._stat_rmin   = self._mk_stat(stats_frame, "r min")
        self._stat_rmax   = self._mk_stat(stats_frame, "r max")
        self._stat_status = self._mk_stat(stats_frame, "Status")
        self._stat_time   = self._mk_stat(stats_frame, "Time")
        for i in range(5):
            stats_frame.columnconfigure(i, weight=1)

        # canvas
        cs = self.CANVAS_SIZE
        self._canvas = tk.Canvas(right, width=cs, height=cs,
                                 bg=CANVAS_BG,
                                 highlightthickness=1,
                                 highlightbackground=BORDER)
        self._canvas.grid(row=1, column=0, sticky="nsew")

        # legend (below canvas)
        leg = tk.Frame(right, bg=BG)
        leg.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        for color, label in [
            (AMBER,  "Photon sphere 1.5 rs"),
            (PURPLE, "ISCO 3.0 rs"),
            (GREEN,  "Start"),
            (PINK,   "End"),
            (ORANGE, "Plunge"),
        ]:
            dot = tk.Frame(leg, bg=color, width=10, height=10)
            dot.pack(side="left", padx=(6, 2))
            tk.Label(leg, text=label,
                     font=STYLE.FONT_LEGEND,
                     bg=BG, fg=TEXT_MUTED).pack(side="left", padx=(0, 10))

    # ── widget helpers ────────────────────────────────────────────────────────

    def _sep(self, parent):
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=10, pady=4)

    def _mk_slider(self, parent, label, var, from_, to, fmt):
        row = tk.Frame(parent, bg=PANEL_BG)
        row.pack(fill="x", padx=14, pady=3)
        header = tk.Frame(row, bg=PANEL_BG)
        header.pack(fill="x")
        tk.Label(header, text=label,
                 font=STYLE.FONT_LABEL,
                 bg=PANEL_BG, fg=TEXT_MUTED).pack(side="left")
        val_lbl = tk.Label(header, text=fmt.format(var.get()),
                           font=STYLE.FONT_LABEL_BOLD,
                           bg=PANEL_BG, fg=TEXT)
        val_lbl.pack(side="right")

        def on_change(*_):
            val_lbl.config(text=fmt.format(var.get()))

        var.trace_add("write", on_change)
        sl = ttk.Scale(row, from_=from_, to=to, variable=var,
                       orient="horizontal", length=200)
        sl.pack(fill="x", pady=(2, 0))

    def _mk_stat(self, parent, label: str) -> tk.Label:
        f = tk.Frame(parent, bg=PANEL_BG, padx=10, pady=6)
        f.pack(side="left", fill="x", expand=True, padx=3)
        tk.Label(f, text=label,
                 font=STYLE.FONT_SMALL,
                 bg=PANEL_BG, fg=TEXT_MUTED).pack(anchor="w")
        val = tk.Label(f, text="—",
                       font=STYLE.FONT_STAT,
                       bg=PANEL_BG, fg=TEXT)
        val.pack(anchor="w")
        return val

    # ── preset / run logic ────────────────────────────────────────────────────

    def _apply_preset(self, display_name: str):
        for n, b in self._preset_btns.items():
            b.config(
                bg=ACCENT if n == display_name else BORDER,
                fg=BG     if n == display_name else TEXT_MUTED,
            )
        key = self._display_names[display_name]
        p   = _get_preset_params(key)
        self._r0_var.set(p["r0"])
        self._speed_var.set(p["speed"])
        self._angle_var.set(p["angle"])
        self._tau_var.set(p["tau"])
        self._run()

    def _run(self):
        r0    = self._r0_var.get()
        speed = self._speed_var.get()
        angle = self._angle_var.get()
        tau   = self._tau_var.get()
        slvr  = self._solver_var.get()

        try:
            params = OrbitalParams(r0_rs=r0, speed_frac=speed, angle_deg=angle)
            cfg    = SolverConfig(tau_max=tau, solver=slvr)
        except ValueError as exc:
            messagebox.showerror("Invalid input", str(exc))
            return

        try:
            result = solver.run(params, cfg)
        except Exception as exc:
            messagebox.showerror("Integration error", str(exc))
            return

        self._result = result
        self._update_stats(result)
        self._redraw(result)

    def _update_stats(self, sol):
        self._stat_steps.config(text=f"{sol.n_steps:,}")
        self._stat_rmin.config(text=f"{sol.r_min:.2f} rs")
        self._stat_rmax.config(text=f"{sol.r_max:.2f} rs")
        self._stat_time.config(text=f"{sol.elapsed_ms:.1f} ms")
        if sol.plunged:
            self._stat_status.config(text="Plunged",  fg=ORANGE)
        else:
            self._stat_status.config(text="Orbiting", fg=GREEN)

    # ── drawing ───────────────────────────────────────────────────────────────

    def _redraw(self, sol):
        cv = self._canvas
        cv.delete("all")
        W  = cv.winfo_width()  or self.CANVAS_SIZE
        H  = cv.winfo_height() or self.CANVAS_SIZE
        cx, cy = W / 2, H / 2

        r_max = sol.r_max * 1.15
        scale = (min(W, H) * 0.46) / r_max

        # faint grid rings
        step = max(1, int(r_max / 5))
        for gr in range(step, int(r_max) + step, step):
            _draw_circle(cv, cx, cy, gr, scale,
                         fill=GRID, width=1, smooth=True)

        # reference orbits
        _draw_circle(cv, cx, cy, 1.5, scale,
                     fill=AMBER, width=1, dash=(4, 4), smooth=True)
        _draw_circle(cv, cx, cy, 3.0, scale,
                     fill=PURPLE, width=1, dash=(2, 3), smooth=True)

        # event horizon
        eh = 1.0 * scale
        cv.create_oval(cx - eh, cy - eh, cx + eh, cy + eh,
                       fill="#000000", outline="white", width=1.5)

        # trajectory
        pts = []
        for r, phi in zip(sol.r, sol.phi):
            x, y = _polar_to_xy(r, phi, cx, cy, scale)
            pts += [x, y]
        if len(pts) >= 4:
            cv.create_line(*pts, fill=ACCENT, width=2, smooth=True)

        # start marker
        sx, sy = _polar_to_xy(sol.r[0], sol.phi[0], cx, cy, scale)
        cv.create_oval(sx - 5, sy - 5, sx + 5, sy + 5,
                       fill=GREEN, outline="")

        # end marker
        ex, ey = _polar_to_xy(sol.r[-1], sol.phi[-1], cx, cy, scale)
        color  = ORANGE if sol.plunged else PINK
        if sol.plunged:
            d = 5
            cv.create_line(ex - d, ey - d, ex + d, ey + d, fill=color, width=2)
            cv.create_line(ex + d, ey - d, ex - d, ey + d, fill=color, width=2)
        else:
            cv.create_oval(ex - 5, ey - 5, ex + 5, ey + 5,
                           fill=color, outline="")

        # radius labels
        for gr in range(step, int(r_max) + step, step):
            lx, ly = _polar_to_xy(gr, math.pi * 0.25, cx, cy, scale)
            cv.create_text(lx, ly, text=f"{gr} rs",
                           fill=TEXT_MUTED,
                           font=STYLE.FONT_CANVAS)


# ── entry point ───────────────────────────────────────────────────────────────
def launch():
    """Start the Tkinter event loop."""
    app = GeodesicApp()
    app.mainloop()


if __name__ == "__main__":
    launch()