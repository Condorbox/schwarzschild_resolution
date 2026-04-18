"""
widgets.py
=============
Self-contained, reusable Tkinter widget primitives used across the UI.
"""

from __future__ import annotations

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

    def pack(self, **kwargs):  # sensible defaults so callers can just call .pack()
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
        self._var     = variable
        self._fmt     = fmt
        self._cb      = on_change

        header = tk.Frame(self, bg=_BG)
        header.pack(fill="x")

        tk.Label(header, text=label, font=STYLE.FONT_LABEL,
                 bg=_BG, fg=_MUTE).pack(side="left")

        self._val_lbl = tk.Label(header, text=fmt.format(variable.get()),
                                 font=STYLE.FONT_LABEL_BOLD, bg=_BG, fg=_TEXT)
        self._val_lbl.pack(side="right")

        ttk.Scale(self, from_=from_, to=to, variable=variable,
                  orient="horizontal").pack(fill="x", pady=(2, 0))

        variable.trace_add("write", self._on_var_change)

    def _on_var_change(self, *_):
        val = self._var.get()
        self._val_lbl.config(text=self._fmt.format(val))
        if self._cb:
            self._cb(val)


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
    """

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable,
        accent: bool = True,
        **kwargs,
    ):
        bg = _ACC if accent else _BRD
        fg = STYLE.UI_BG if accent else _TEXT
        hover_bg = "#00b8d9" if accent else "#36364a"

        super().__init__(
            parent,
            text=text,
            font=STYLE.FONT_BTN,
            bg=bg,
            fg=fg,
            activebackground=hover_bg,
            activeforeground=fg,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=8,
            command=command,
            **kwargs,
        )


class TabBar(tk.Frame):
    """
    Underline-style tab strip.  Calls on_change(tab_id) when the user switches.
    """

    def __init__(
        self,
        parent: tk.Widget,
        tabs: list[tuple[str, str]],   # [(id, label), …]
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

        # underline indicator
        self._indicator = tk.Frame(self, bg=_ACC, height=2)
        self._indicator.place(x=0, y=0, width=0)   # positioned in _refresh
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
        # Move underline beneath the active tab
        active_lbl = self._btns[self._active]
        self._indicator.place(
            x=active_lbl.winfo_x(),
            y=self.winfo_height() - 2,
            width=active_lbl.winfo_width(),
        )

    @property
    def active(self) -> str:
        return self._active