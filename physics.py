"""
General-relativistic math for the Schwarzschild spacetime.

Conventions
-----------
- Geometric units: G = c = 1.
- Mass M = 1  →  Schwarzschild radius rs = 2M = 2.
- Coordinates: (r, phi) in the equatorial plane (theta = pi/2).
- Affine parameter: proper time tau for massive particles.
"""

from __future__ import annotations
import numpy as np

# Global constants 
M: float = 1.0
RS: float = 2.0 * M # Schwarzschild radius


# Metric helper
def lapse(r: float) -> float:
    """Metric factor f(r) = 1 - rs/r."""
    return 1.0 - RS / r


# Equations of motion
def geodesic_rhs(tau: float, Y: list[float]) -> list[float]:
    """
    Right-hand side of the Schwarzschild geodesic ODEs (equatorial plane)

    State vector Y = [r, rdot, phi, phidot]
    Returns dY/dtau = [rdot, rddot, phidot, phiddot]

    The integration is frozen (zero derivatives) once the trajectory
    enters the horizon to avoid singularity blow-up
    """
    r, rdot, phi, phidot = Y

    if r <= RS * 1.005:     # Inside/at the horizon
        return [0.0, 0.0, 0.0, 0.0]

    f = lapse(r)
    rddot   = -M / r**2 * f + r * phidot**2 * f - M / r**2 * rdot**2 / f
    phiddot = -2.0 * rdot * phidot / r
    return [rdot, rddot, phidot, phiddot]


# Circular orbit helpers
def circular_angular_velocity(r: float) -> float:
    """
    dphi/dtau for a circular orbit at radius r
    Valid only for r > 1.5 rs 
    """
    denom = 1.0 - 1.5 * RS / r
    if denom <= 0.0:
        return 0.0
    return np.sqrt(M / r**3) / np.sqrt(denom)


def circular_energy_angular_momentum(r: float) -> tuple[float, float]:
    """
    Exact conserved energy E and angular momentum L per unit rest mass
    for a circular geodesic at radius r

    Requires r > 3M (innermost stable circular orbit, ISCO, is at r = 6M = 3 rs)
    """
    E = (1.0 - 2.0 * M / r) / np.sqrt(1.0 - 3.0 * M / r)
    L = np.sqrt(M * r) / np.sqrt(1.0 - 3.0 * M / r)
    return E, L


# Initial-condition builder
def build_initial_state(r0: float, speed_frac: float = 1.0, angle_deg: float = 0.0) -> list[float]:
    """
    Construct the ODE state vector [r, rdot, phi, phidot] at tau = 0

    Parameters
    ----------
    r0 : float
        Initial radius in coordinate units (not rs units)
    speed_frac : float
        Speed relative to local circular orbit speed (1.0 = exact circular)
    angle_deg : float
        Launch angle: 0° = tangential, 90° = radial outward

    Returns
    -------
    list[float]
        [r0, rdot0, 0.0, phidot0]
    """
    alpha = np.radians(angle_deg)
    _, L_circ = circular_energy_angular_momentum(r0)

    # Scale angular momentum by the cosine component of the launch angle
    L = speed_frac * L_circ * np.cos(alpha)
    phidot = L / r0**2

    # Approximate local tangential speed → radial component
    v_circ = L_circ / r0
    rdot = speed_frac * v_circ * np.sin(alpha)

    return [r0, rdot, 0.0, phidot]