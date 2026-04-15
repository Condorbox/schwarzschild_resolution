"""
3D Matplotlib renderer for Schwarzschild geodesics.

Projects the equatorial-plane geodesic into 3D space.  An optional
inclination angle tilts the orbital plane away from the z=0 plane so
the trajectory is not just a flat disc when viewed from an angle.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 registers the 3d projection

from config import Solution


def _to_cartesian(r: np.ndarray, phi: np.ndarray, inclination_deg: float = 30.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert polar (r, phi) in the orbital plane to 3-D Cartesian coordinates

    The orbital plane is tilted by `inclination_deg` around the x-axis so
    the path is clearly visible in perspective rather than edge-on
    """
    # Flat equatorial coordinates
    x_flat = r * np.cos(phi)
    y_flat = r * np.sin(phi)

    # Rotate around the x-axis by the inclination angle
    inc = np.radians(inclination_deg)
    x = x_flat
    y = y_flat * np.cos(inc)
    z = y_flat * np.sin(inc)
    return x, y, z


def _sphere(radius: float, n: int = 40) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (X, Y, Z) mesh arrays for a sphere of the given radius"""
    u = np.linspace(0, 2 * np.pi, n)
    v = np.linspace(0, np.pi, n)
    X = radius * np.outer(np.cos(u), np.sin(v))
    Y = radius * np.outer(np.sin(u), np.sin(v))
    Z = radius * np.outer(np.ones(n), np.cos(v))
    return X, Y, Z


def _reference_ring(radius: float, inclination_deg: float, n: int = 200) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return a tilted reference ring (photon sphere or ISCO)"""
    phi = np.linspace(0, 2 * np.pi, n)
    r = np.full_like(phi, radius)
    return _to_cartesian(r, phi, inclination_deg)


def plot3d(solution: Solution, inclination_deg: float = 30.0, save_path: str | None = None) -> str | None:
    """
    Render a geodesic on a 3-D plot

    Parameters
    ----------
    solution : Solution
        The integrated geodesic to display
    inclination_deg : float
        Tilt of the orbital plane relative to the equatorial plane (degrees)
        0 = flat (hard to see), 30 = good default perspective
    save_path : str | None
        If given, save the figure to this path instead of showing it

    Returns
    -------
    str | None
        The path the figure was saved to, or None if shown interactively
    """
    p = solution.params
    title_info = (
        f"r₀={p.r0_rs} rs  |  v={p.speed_frac} v_circ  |  α={p.angle_deg}°  "
        f"|  inc={inclination_deg}°"
    )

    plt.style.use("dark_background")
    fig = plt.figure(figsize=(10, 9))
    ax: Axes3D = fig.add_subplot(111, projection="3d")

    r_max_display = solution.r_max * 1.15

    # Black hole (event horizon sphere) 
    Xs, Ys, Zs = _sphere(radius=1.0)
    ax.plot_surface(Xs, Ys, Zs, color="black", zorder=5, alpha=1.0)

    # Photon sphere ring 
    xph, yph, zph = _reference_ring(1.5, inclination_deg)
    ax.plot(xph, yph, zph, color="#fbbf24", lw=1.0, ls="--", alpha=0.7,
            label="Photon sphere (1.5 rs)")

    # ISCO ring 
    xis, yis, zis = _reference_ring(3.0, inclination_deg)
    ax.plot(xis, yis, zis, color="#a78bfa", lw=1.0, ls=":", alpha=0.7,
            label="ISCO (3.0 rs)")

    # Geodesic trajectory 
    xt, yt, zt = _to_cartesian(solution.r, solution.phi, inclination_deg)
    ax.plot(xt, yt, zt, color="#00d4ff", lw=1.5, alpha=0.9,
            label="Geodesic path", zorder=8)

    # Start marker
    ax.scatter([xt[0]], [yt[0]], [zt[0]],
               color="#39d353", s=40, zorder=10, label="Start")

    # End marker
    end_color  = "#ff6b35" if solution.plunged else "#f472b6"
    end_marker = "x"       if solution.plunged else "^"
    end_label  = "End (plunge)" if solution.plunged else "End"
    ax.scatter([xt[-1]], [yt[-1]], [zt[-1]],
               color=end_color, marker=end_marker, s=60, zorder=10, label=end_label)

    # Faint equatorial grid disc 
    theta = np.linspace(0, 2 * np.pi, 200)
    for ring_r in np.linspace(1.5, r_max_display, 5):
        rx = ring_r * np.cos(theta)
        ry = ring_r * np.sin(theta)
        rz = np.zeros_like(theta)
        ax.plot(rx, ry, rz, color="#333344", lw=0.4, alpha=0.5)

    # Axis cosmetics 
    ax.set_xlim(-r_max_display, r_max_display)
    ax.set_ylim(-r_max_display, r_max_display)
    ax.set_zlim(-r_max_display * 0.6, r_max_display * 0.6)

    ax.set_xlabel("x (rs)", labelpad=6)
    ax.set_ylabel("y (rs)", labelpad=6)
    ax.set_zlabel("z (rs)", labelpad=6)

    ax.set_title(f"Schwarzschild Geodesic — 3D View\n{title_info}", pad=14)
    ax.legend(loc="upper left", fontsize=8)

    # Tick label colour to match dark background
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor("#333344")

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return save_path
    else:
        if _backend_supports_show():
            plt.show()
            return None

        auto_path = _auto_save_path("orbit3d.png")
        fig.savefig(auto_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return str(auto_path)


def _backend_supports_show() -> bool:
    import matplotlib
    from matplotlib import rcsetup
    backend = str(matplotlib.get_backend())
    if backend.lower().startswith("module://"):
        return True
    interactive = {b.lower() for b in rcsetup.interactive_bk}
    return backend.lower() in interactive


def _auto_save_path(filename: str) -> Path:
    base = Path(filename)
    if not base.exists():
        return base
    stem, suffix = base.stem, base.suffix
    for i in range(1, 1000):
        candidate = base.with_name(f"{stem}-{i}{suffix}")
        if not candidate.exists():
            return candidate
    return base