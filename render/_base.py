"""
Shared rendering utilities for all Schwarzschild geodesic plotters.

Provides
--------
STYLE        — colour/line-style constants used by every renderer.
build_title  — consistent parameter subtitle string.
save_or_show — unified figure save / interactive-show / auto-save fallback.
auto_save_path — non-clobbering filename helper.
"""

from __future__ import annotations
from pathlib import Path

from render import avoid_matplotlib_warning
avoid_matplotlib_warning()

import matplotlib
import matplotlib.pyplot as plt


def build_title(r0_rs: float, speed_frac: float, angle_deg: float,
                extra: str = "") -> str:
    """Return the parameter subtitle line shown on every plot."""
    base = f"r₀={r0_rs} rs  |  v={speed_frac} v_circ  |  α={angle_deg}°"
    return f"{base}  |  {extra}" if extra else base


def _backend_supports_show() -> bool:
    """True when the active Matplotlib backend can open an interactive window."""
    from matplotlib import rcsetup
    backend = str(matplotlib.get_backend())
    if backend.lower().startswith("module://"):
        return True
    interactive = {b.lower() for b in rcsetup.interactive_bk}
    return backend.lower() in interactive


def auto_save_path(filename: str) -> Path:
    """Return *filename*, incrementing a suffix (-1, -2, …) to avoid clobbering."""
    base = Path(filename)
    if not base.exists():
        return base
    stem, suffix = base.stem, base.suffix
    for i in range(1, 1000):
        candidate = base.with_name(f"{stem}-{i}{suffix}")
        if not candidate.exists():
            return candidate
    return base          # last resort: overwrite


def save_or_show(fig: plt.Figure,
                 save_path: str | None,
                 default_filename: str) -> str | None:
    """
    Unified figure output logic shared by every renderer.
    """
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return save_path

    if _backend_supports_show():
        plt.show()
        return None

    out = auto_save_path(default_filename)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return str(out)
