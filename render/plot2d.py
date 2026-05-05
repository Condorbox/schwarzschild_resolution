"""
2-D polar renderer for Schwarzschild geodesics.
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt

from core.config import Solution
from render._base import build_title, save_or_show
from  render.style import STYLE


def plot(solution: Solution, save_path: str | None = None) -> str | None:
    """
    Render a geodesic on a polar plot.

    Parameters
    ----------
    solution : Solution
        The integrated geodesic to display.
    save_path : str | None
        If given, save the figure to this path instead of showing it.

    Returns
    -------
    str | None
        The path the figure was saved to, or None if shown interactively.
    """
    plt.style.use("dark_background")
    fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(8, 8))

    _draw_background(ax)
    _draw_trajectory(ax, solution)
    _apply_formatting(ax, solution)

    plt.tight_layout()
    return save_or_show(fig, save_path, "orbit.png")


def _unit_circle(n: int = 400) -> np.ndarray:
    return np.linspace(0.0, 2.0 * np.pi, n)


def _draw_background(ax: plt.Axes) -> None:
    th = _unit_circle()

    # Event horizon
    ax.fill(th, np.ones_like(th), color=STYLE.HORIZON_COLOR, zorder=6)
    ax.plot(th, np.ones_like(th), color=STYLE.HORIZON_EDGE, lw=1.2, zorder=7)

    # Photon sphere
    ax.plot(th, 1.5 * np.ones_like(th),
            color=STYLE.PHOTON_SPHERE_COLOR, lw=1.0,
            ls=STYLE.PHOTON_SPHERE_LS, alpha=0.7,
            label=STYLE.PHOTON_SPHERE_LABEL, zorder=5)

    # ISCO
    ax.plot(th, 3.0 * np.ones_like(th),
            color=STYLE.ISCO_COLOR, lw=1.0,
            ls=STYLE.ISCO_LS, alpha=0.7,
            label=STYLE.ISCO_LABEL, zorder=5)


def _draw_trajectory(ax: plt.Axes, sol: Solution) -> None:
    ax.plot(sol.phi, sol.r,
            color=STYLE.TRAJECTORY_COLOR,
            lw=STYLE.TRAJECTORY_LW,
            alpha=STYLE.TRAJECTORY_ALPHA,
            label=STYLE.TRAJECTORY_LABEL, zorder=8)

    ax.plot(sol.phi[0], sol.r[0],
            "o", color=STYLE.START_COLOR, ms=6, zorder=10, label="Start")

    end_color  = STYLE.PLUNGE_COLOR if sol.plunged else STYLE.END_COLOR
    end_marker = "x"  if sol.plunged else "^"
    end_label  = "End (plunge)" if sol.plunged else "End"
    ax.plot(sol.phi[-1], sol.r[-1],
            end_marker, color=end_color, ms=8, zorder=10, label=end_label)


def _apply_formatting(ax: plt.Axes, sol: Solution) -> None:
    p = sol.params
    subtitle = build_title(p.r0_rs, p.speed_frac, p.angle_deg)
    ax.set_title(f"Schwarzschild Geodesic — Equatorial Plane\n{subtitle}", pad=20)
    ax.set_rmax(p.r0_rs * 1.2)
    ax.grid(color=STYLE.GRID_COLOR, linestyle="-", linewidth=0.5)
    ax.legend(loc="upper right", fontsize=9)