"""
3-D renderer for Schwarzschild geodesics.

Projects the equatorial-plane geodesic into 3-D space.  An optional
inclination angle tilts the orbital plane so the trajectory is clearly
visible in perspective rather than appearing edge-on.
"""

from __future__ import annotations
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — registers the 3-D projection

from core.config import Solution
from render._base import STYLE, build_title, save_or_show


def plot(solution: Solution,
         inclination_deg: float = 30.0,
         save_path: str | None = None) -> str | None:
    """
    Render a geodesic on a 3-D perspective plot.

    Parameters
    ----------
    solution : Solution
        The integrated geodesic to display.
    inclination_deg : float
        Tilt of the orbital plane relative to the equatorial plane (degrees).
        0 = edge-on (hard to read), 30 = good default perspective.
    save_path : str | None
        If given, save the figure to this path instead of showing it.

    Returns
    -------
    str | None
        The path the figure was saved to, or None if shown interactively.
    """
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(10, 9))
    ax: Axes3D = fig.add_subplot(111, projection="3d")

    r_max_display = solution.r_max * 1.15

    _draw_background(ax, r_max_display, inclination_deg)
    _draw_trajectory(ax, solution, inclination_deg)
    _apply_formatting(ax, solution, inclination_deg, r_max_display)

    plt.tight_layout()
    return save_or_show(fig, save_path, "orbit3d.png")


def to_cartesian(r: np.ndarray, phi: np.ndarray,
                 inclination_deg: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert polar (r, φ) in the orbital plane to 3-D Cartesian coordinates.

    The orbital plane is rotated around the x-axis by *inclination_deg*.
    """
    x_flat = r * np.cos(phi)
    y_flat = r * np.sin(phi)
    inc = np.radians(inclination_deg)
    return x_flat, y_flat * np.cos(inc), y_flat * np.sin(inc)


def _sphere(radius: float, n: int = 40) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (X, Y, Z) mesh arrays for a sphere of the given radius."""
    u = np.linspace(0, 2 * np.pi, n)
    v = np.linspace(0, np.pi, n)
    X = radius * np.outer(np.cos(u), np.sin(v))
    Y = radius * np.outer(np.sin(u), np.sin(v))
    Z = radius * np.outer(np.ones(n), np.cos(v))
    return X, Y, Z


def _ring(radius: float, inclination_deg: float,
          n: int = 200) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return a tilted reference ring at *radius* rs."""
    phi = np.linspace(0, 2 * np.pi, n)
    return to_cartesian(np.full_like(phi, radius), phi, inclination_deg)


def _draw_background(ax: Axes3D, r_max: float, inclination_deg: float) -> None:
    # Event horizon sphere
    Xs, Ys, Zs = _sphere(radius=1.0)
    ax.plot_surface(Xs, Ys, Zs, color=STYLE.HORIZON_COLOR, zorder=5, alpha=1.0)

    # Photon sphere ring
    ax.plot(*_ring(1.5, inclination_deg),
            color=STYLE.PHOTON_SPHERE_COLOR, lw=1.0,
            ls=STYLE.PHOTON_SPHERE_LS, alpha=0.7,
            label=STYLE.PHOTON_SPHERE_LABEL)

    # ISCO ring
    ax.plot(*_ring(3.0, inclination_deg),
            color=STYLE.ISCO_COLOR, lw=1.0,
            ls=STYLE.ISCO_LS, alpha=0.7,
            label=STYLE.ISCO_LABEL)

    # Faint equatorial reference grid
    theta = np.linspace(0, 2 * np.pi, 200)
    for ring_r in np.linspace(1.5, r_max, 5):
        ax.plot(ring_r * np.cos(theta),
                ring_r * np.sin(theta),
                np.zeros_like(theta),
                color=STYLE.GRID_COLOR, lw=0.4, alpha=0.5)


def _draw_trajectory(ax: Axes3D, sol: Solution, inclination_deg: float) -> None:
    xt, yt, zt = to_cartesian(sol.r, sol.phi, inclination_deg)

    ax.plot(xt, yt, zt,
            color=STYLE.TRAJECTORY_COLOR,
            lw=STYLE.TRAJECTORY_LW,
            alpha=STYLE.TRAJECTORY_ALPHA,
            label=STYLE.TRAJECTORY_LABEL, zorder=8)

    ax.scatter([xt[0]], [yt[0]], [zt[0]],
               color=STYLE.START_COLOR, s=40, zorder=10, label="Start")

    end_color  = STYLE.PLUNGE_COLOR if sol.plunged else STYLE.END_COLOR
    end_marker = "x" if sol.plunged else "^"
    end_label  = "End (plunge)" if sol.plunged else "End"
    ax.scatter([xt[-1]], [yt[-1]], [zt[-1]],
               color=end_color, marker=end_marker, s=60, zorder=10, label=end_label)


def _apply_formatting(ax: Axes3D, sol: Solution,
                      inclination_deg: float, r_max: float) -> None:
    p = sol.params
    subtitle = build_title(p.r0_rs, p.speed_frac, p.angle_deg,
                           extra=f"inc={inclination_deg}°")
    ax.set_title(f"Schwarzschild Geodesic — 3D View\n{subtitle}", pad=14)

    ax.set_xlim(-r_max, r_max)
    ax.set_ylim(-r_max, r_max)
    ax.set_zlim(-r_max * 0.6, r_max * 0.6)

    ax.set_xlabel("x (rs)", labelpad=6)
    ax.set_ylabel("y (rs)", labelpad=6)
    ax.set_zlabel("z (rs)", labelpad=6)

    ax.legend(loc="upper left", fontsize=8)

    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor(STYLE.GRID_COLOR)