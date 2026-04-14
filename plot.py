"""
2D Matplotlib renderer for Schwarzschild geodesics.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from config import Solution


def plot(solution: Solution, save_path: str | None = None) -> str | None:
    """
    Render a geodesic on a polar plot

    Parameters
    ----------
    solution : Solution
        The integrated geodesic to display
    save_path : str | None
        If given, save the figure to this path instead of showing it

    Returns
    -------
    str | None
        The path the figure was saved to, or None if it was shown interactively.
    """
    p = solution.params
    title_info = (
        f"r₀={p.r0_rs} rs  |  v={p.speed_frac} v_circ  |  α={p.angle_deg}°"
    )

    plt.style.use("dark_background")
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 8))

    _draw_background(ax)
    _draw_trajectory(ax, solution)
    _apply_formatting(ax, title_info, p.r0_rs)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return save_path
    else:
        if _backend_supports_show():
            plt.show()
            return None

        auto_path = _auto_save_path()
        fig.savefig(auto_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return str(auto_path)


def _backend_supports_show() -> bool:
    """
    Return True if the current Matplotlib backend is expected to support
    interactive window display via plt.show().
    """
    import matplotlib
    from matplotlib import rcsetup

    backend = str(matplotlib.get_backend())
    if backend.lower().startswith("module://"):
        return True
    interactive = {b.lower() for b in rcsetup.interactive_bk}
    return backend.lower() in interactive


def _auto_save_path(filename: str = "orbit.png") -> Path:
    base = Path(filename)
    if not base.exists():
        return base

    stem = base.stem
    suffix = base.suffix
    for i in range(1, 1000):
        candidate = base.with_name(f"{stem}-{i}{suffix}")
        if not candidate.exists():
            return candidate
    return base


def _unit_circle(n: int = 400) -> np.ndarray:
    return np.linspace(0.0, 2.0 * np.pi, n)


def _draw_background(ax: plt.Axes) -> None:
    th = _unit_circle()

    # Event horizon (filled)
    ax.fill(th, np.ones_like(th), color="#000000", zorder=6)
    ax.plot(th, np.ones_like(th), color="#ffffff", lw=1.2, zorder=7)

    # Reference circles
    ax.plot(th, 1.5 * np.ones_like(th),
            color="#fbbf24", lw=1.0, ls="--", alpha=0.7,
            label="Photon sphere (1.5 rs)", zorder=5)
    ax.plot(th, 3.0 * np.ones_like(th),
            color="#a78bfa", lw=1.0, ls=":",  alpha=0.7,
            label="ISCO (3.0 rs)", zorder=5)


def _draw_trajectory(ax: plt.Axes, sol: Solution) -> None:
    ax.plot(sol.phi, sol.r,
            color="#00d4ff", lw=1.5, alpha=0.9,
            label="Geodesic path", zorder=8)

    # Start marker
    ax.plot(sol.phi[0], sol.r[0],
            "o", color="#39d353", ms=6, zorder=10, label="Start")

    # End marker
    end_color = "#ff6b35" if sol.plunged else "#f472b6"
    end_marker = "x" if sol.plunged else "^"
    end_label = "End (plunge)" if sol.plunged else "End"
    ax.plot(sol.phi[-1], sol.r[-1],
            end_marker, color=end_color, ms=8, zorder=10, label=end_label)


def _apply_formatting(ax: plt.Axes, title: str, r0_rs: float) -> None:
    ax.set_title(f"Schwarzschild Geodesic — Equatorial Plane\n{title}", pad=20)
    ax.set_rmax(r0_rs * 1.2)
    ax.grid(color="#333344", linestyle="-", linewidth=0.5)
    ax.legend(loc="upper right", fontsize=9)
