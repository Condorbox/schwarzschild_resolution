"""
widgets.py
=============
Self-contained, reusable Tkinter widget primitives used across the UI.
"""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Callable

from render.style import STYLE

_BG   = STYLE.UI_PANEL_BG
_CARD = STYLE.UI_CARD_BG
_TEXT = STYLE.UI_TEXT
_MUTE = STYLE.UI_TEXT_MUTED
_ACC  = STYLE.UI_ACCENT
_BRD  = STYLE.UI_BORDER


class SectionLabel(tk.Label):
    """All-caps muted label used as a section header inside the sidebar."""

    def __init__(self, parent: tk.Widget, text: str, **kwargs):
        super().__init__(
            parent,
            text=text.upper(),
            font=STYLE.FONT_SECTION,
            bg=_BG,
            fg=_MUTE,
            **kwargs,
        )


# Horizontal rule 
class Separator(tk.Frame):
    """1 px horizontal rule that matches the panel border colour."""

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=_BRD, height=1, **kwargs)

    def pack(self, **kwargs):
        kwargs.setdefault("fill", "x")
        kwargs.setdefault("padx", 10)
        kwargs.setdefault("pady", 6)
        super().pack(**kwargs)


class LabeledSlider(tk.Frame):
    """
    A slider row with a left label and a right live-updating value readout.

    Parameters
    ----------
    parent      Parent widget.
    label       Human-readable parameter name.
    variable    tk.DoubleVar bound to the slider.
    from_, to   Slider range.
    fmt         Python format string for the value display (e.g. "{:.1f} rs").
    on_change   Optional callback(value: float) called on every slider move.
    """

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.DoubleVar,
        from_: float,
        to: float,
        fmt: str,
        on_change: Callable[[float], None] | None = None,
    ):
        super().__init__(parent, bg=_BG)
        self._var = variable
        self._fmt = fmt
        self._cb  = on_change

        header = tk.Frame(self, bg=_BG)
        header.pack(fill="x")

        tk.Label(header, text=label, font=STYLE.FONT_LABEL,
                 bg=_BG, fg=_MUTE).pack(side="left")

        self._val_lbl = tk.Label(
            header,
            text=fmt.format(variable.get()),
            font=STYLE.FONT_LABEL_BOLD,
            bg=_BG, fg=_TEXT,
        )
        self._val_lbl.pack(side="right")

        ttk.Scale(self, from_=from_, to=to, variable=variable,
                  orient="horizontal").pack(fill="x", pady=(2, 0))

        variable.trace_add("write", self._on_var_change)

    def _on_var_change(self, *_):
        val = self._var.get()
        self._val_lbl.config(text=self._fmt.format(val))
        if self._cb:
            self._cb(val)


class LogSlider(tk.Frame):
    """
    A slider whose *internal* position is linear [0, 1] but whose displayed
    value is mapped logarithmically to [min_val, max_val].

    This makes it ergonomic to choose a step-size that spans several orders
    of magnitude (e.g. 0.01 → 10.0) without cramping the small end.

    Parameters
    ----------
    parent              Parent widget.
    label               Human-readable parameter name.
    min_val, max_val    Real-world (linear) bounds — must both be > 0.
    initial             Initial real-world value.
    fmt                 Format string applied to the real value for display.
    on_change           Optional callback(real_value: float).
    """

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        min_val: float,
        max_val: float,
        initial: float,
        fmt: str = "{:.3g}",
        on_change: Callable[[float], None] | None = None,
    ):
        super().__init__(parent, bg=_BG)
        self._min_log = math.log10(min_val)
        self._max_log = math.log10(max_val)
        self._fmt     = fmt
        self._cb      = on_change

        # Internal variable is in [0, 1] — linear slider position
        self._raw = tk.DoubleVar(value=self._to_raw(initial))

        header = tk.Frame(self, bg=_BG)
        header.pack(fill="x")

        tk.Label(header, text=label, font=STYLE.FONT_LABEL,
                 bg=_BG, fg=_MUTE).pack(side="left")

        self._val_lbl = tk.Label(
            header,
            text=fmt.format(initial),
            font=STYLE.FONT_LABEL_BOLD,
            bg=_BG, fg=_TEXT,
        )
        self._val_lbl.pack(side="right")

        ttk.Scale(self, from_=0.0, to=1.0, variable=self._raw,
                  orient="horizontal").pack(fill="x", pady=(2, 0))

        self._raw.trace_add("write", self._on_raw_change)


    @property
    def real_value(self) -> float:
        """The current slider value in real (linear) units."""
        return self._to_real(self._raw.get())

    def set_real(self, value: float) -> None:
        """Programmatically set the slider to a real (linear) value."""
        self._raw.set(self._to_raw(value))


    def _to_raw(self, real: float) -> float:
        return (math.log10(real) - self._min_log) / (self._max_log - self._min_log)

    def _to_real(self, raw: float) -> float:
        return 10 ** (self._min_log + raw * (self._max_log - self._min_log))

    def _on_raw_change(self, *_):
        real = self.real_value
        self._val_lbl.config(text=self._fmt.format(real))
        if self._cb:
            self._cb(real)


class StatCard(tk.Frame):
    """
    A small metric card displaying a label and a large numeric value.

    Call .set(text, colour) to update at runtime.
    """

    def __init__(self, parent: tk.Widget, label: str):
        super().__init__(parent, bg=_CARD, padx=10, pady=8)

        tk.Label(self, text=label.upper(), font=STYLE.FONT_STAT_LABEL,
                 bg=_CARD, fg=_MUTE).pack(anchor="w")

        self._val = tk.Label(self, text="—", font=STYLE.FONT_STAT_VAL,
                             bg=_CARD, fg=_TEXT)
        self._val.pack(anchor="w")

    def set(self, text: str, colour: str = STYLE.UI_TEXT) -> None:
        self._val.config(text=text, fg=colour)


class ToggleStrip(tk.Frame):
    """
    A row of mutually-exclusive text buttons (radio-button semantics).

    Parameters
    ----------
    parent      Parent widget.
    options     List of (value, label) pairs.
    on_select   Callback(value) invoked when the active selection changes.
    initial     Value that starts selected (defaults to options[0]).
    """

    def __init__(
        self,
        parent: tk.Widget,
        options: list[tuple[str, str]],
        on_select: Callable[[str], None],
        initial: str | None = None,
    ):
        super().__init__(parent, bg=_BG)
        self._on_select = on_select
        self._buttons: dict[str, tk.Button] = {}
        self._active: str = initial if initial is not None else options[0][0]

        for value, label in options:
            btn = tk.Button(
                self,
                text=label,
                font=STYLE.FONT_SMALL,
                bg=_BRD, fg=_MUTE,
                activebackground=_ACC,
                activeforeground=STYLE.UI_BG,
                relief="flat",
                cursor="hand2",
                padx=10, pady=4,
                command=lambda v=value: self._select(v),
            )
            btn.pack(side="left", padx=(0, 2))
            self._buttons[value] = btn

        self._refresh()

    def _select(self, value: str) -> None:
        if value == self._active:
            return
        self._active = value
        self._refresh()
        self._on_select(value)

    def _refresh(self) -> None:
        for value, btn in self._buttons.items():
            active = value == self._active
            btn.config(
                bg=_ACC if active else _BRD,
                fg=STYLE.UI_BG if active else _MUTE,
            )

    @property
    def value(self) -> str:
        return self._active

    def select(self, value: str) -> None:
        """Programmatically activate a button (does NOT fire on_select)."""
        self._active = value
        self._refresh()


# Icon/text button 
class ActionButton(tk.Button):
    """
    Primary CTA button.  Pass ``accent=False`` for a secondary (dim) style.
    Exposes ``set_state(enabled)`` to disable during a background computation.
    """

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable,
        accent: bool = True,
        **kwargs,
    ):
        self._normal_bg = _ACC if accent else _BRD
        self._normal_fg = STYLE.UI_BG if accent else _TEXT
        self._hover_bg  = "#00b8d9" if accent else "#36364a"

        super().__init__(
            parent,
            text=text,
            font=STYLE.FONT_BTN,
            bg=self._normal_bg,
            fg=self._normal_fg,
            activebackground=self._hover_bg,
            activeforeground=self._normal_fg,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=8,
            command=command,
            **kwargs,
        )

    def set_state(self, enabled: bool) -> None:
        """Enable or disable, updating visual appearance to match."""
        if enabled:
            self.config(
                state="normal",
                bg=self._normal_bg,
                fg=self._normal_fg,
                cursor="hand2",
            )
        else:
            self.config(
                state="disabled",
                bg=_BRD,
                fg=_MUTE,
                cursor="",
            )


class TabBar(tk.Frame):
    """
    Underline-style tab strip.  Calls on_change(tab_id) when the user switches.
    """

    def __init__(
        self,
        parent: tk.Widget,
        tabs: list[tuple[str, str]],
        on_change: Callable[[str], None],
        initial: str | None = None,
    ):
        super().__init__(parent, bg=STYLE.UI_BG)
        self._on_change = on_change
        self._active: str = initial if initial is not None else tabs[0][0]
        self._btns: dict[str, tk.Label] = {}

        for tab_id, label in tabs:
            lbl = tk.Label(
                self,
                text=label,
                font=STYLE.FONT_LABEL_BOLD,
                bg=STYLE.UI_BG,
                fg=_TEXT if tab_id == self._active else _MUTE,
                cursor="hand2",
                padx=14,
                pady=8,
            )
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda _e, tid=tab_id: self._switch(tid))
            self._btns[tab_id] = lbl

        self._indicator = tk.Frame(self, bg=_ACC, height=2)
        self._indicator.place(x=0, y=0, width=0)
        self.bind("<Configure>", lambda _e: self._refresh())
        self._refresh()

    def _switch(self, tab_id: str) -> None:
        if tab_id == self._active:
            return
        self._active = tab_id
        self._refresh()
        self._on_change(tab_id)

    def _refresh(self) -> None:
        for tid, lbl in self._btns.items():
            lbl.config(fg=_TEXT if tid == self._active else _MUTE)
        active_lbl = self._btns[self._active]
        self._indicator.place(
            x=active_lbl.winfo_x(),
            y=self.winfo_height() - 2,
            width=active_lbl.winfo_width(),
        )

    @property
    def active(self) -> str:
        return self._active


class ComputingOverlay(tk.Canvas):
    """
    A full-area overlay rendered on top of the view panel while the solver
    runs on a background thread.
    """

    _MESSAGES = [
        "Integrating geodesic…",
        "Solving equations of motion…",
        "Tracing spacetime curvature…",
        "Computing proper time…",
        "Following the geodesic…",
    ]
    _TICK_MS = 40       # ~25 fps
    _DOT_R   = 5        # base dot radius (px)
    _DOT_GAP = 20       # centre-to-centre spacing
    _N_DOTS  = 3

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg=STYLE.UI_CANVAS_BG, highlightthickness=0)
        self._tick: int         = 0
        self._msg_idx: int      = 0
        self._after_id: str | None = None


    def start(self) -> None:
        """Show and begin animating."""
        self._tick    = 0
        self._msg_idx = 0
        self._animate()

    def stop(self) -> None:
        """Stop animating and hide."""
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        self.place_forget()


    def _animate(self) -> None:
        self._draw()
        self._tick += 1
        # Rotate message every ~2.5 s
        cycle = max(1, 2500 // self._TICK_MS)
        if self._tick % cycle == 0:
            self._msg_idx = (self._msg_idx + 1) % len(self._MESSAGES)
        self._after_id = self.after(self._TICK_MS, self._animate)

    def _draw(self) -> None:
        self.delete("all")
        W = self.winfo_width()  or 500
        H = self.winfo_height() or 500
        cx, cy = W / 2, H / 2

        # background
        for _ in range(2):
            self.create_rectangle(0, 0, W, H,
                                  fill=STYLE.UI_CANVAS_BG,
                                  stipple="gray50", outline="")

        # card
        cw, ch = 270, 108
        self._rounded_rect(
            cx - cw/2, cy - ch/2, cx + cw/2, cy + ch/2,
            r=12,
            fill=STYLE.UI_CARD_BG,
            outline=STYLE.UI_BORDER,
            width=1,
        )

        # message
        self.create_text(
            cx, cy - 18,
            text=self._MESSAGES[self._msg_idx],
            fill=STYLE.UI_TEXT,
            font=STYLE.FONT_LABEL_BOLD,
            anchor="center",
        )

        # pulsing dots
        t      = self._tick * self._TICK_MS / 1000.0
        dot_cy = cy + 24
        total  = (self._N_DOTS - 1) * self._DOT_GAP
        dot_x0 = cx - total / 2

        for i in range(self._N_DOTS):
            phase = t * 2.8 - i * 0.6
            alpha = (math.sin(phase) + 1) / 2      # 0 → 1

            # Lerp from muted grey to accent cyan
            r = int(0x2a + (0x00 - 0x2a) * alpha)
            g = int(0x2a + (0xd4 - 0x2a) * alpha)
            b = int(0x35 + (0xff - 0x35) * alpha)
            colour = f"#{r:02x}{g:02x}{b:02x}"

            dr     = self._DOT_R * (0.65 + 0.35 * alpha)   # size pulse
            dot_cx = dot_x0 + i * self._DOT_GAP
            self.create_oval(
                dot_cx - dr, dot_cy - dr,
                dot_cx + dr, dot_cy + dr,
                fill=colour, outline="",
            )

    def _rounded_rect(self, x0, y0, x1, y1, r: int, **kw) -> None:
        """Polygon approximation of a rounded rectangle."""
        pts = [
            x0+r, y0,    x1-r, y0,
            x1,   y0,    x1,   y0+r,
            x1,   y1-r,  x1,   y1,
            x1-r, y1,    x0+r, y1,
            x0,   y1,    x0,   y1-r,
            x0,   y0+r,  x0,   y0,
            x0+r, y0,
        ]
        self.create_polygon(pts, smooth=True, **kw)