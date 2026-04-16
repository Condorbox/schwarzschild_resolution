"""
Numerical integration of Schwarzschild geodesics.

Public API
----------
    run(params, cfg) -> Solution
"""

from __future__ import annotations
import time
import numpy as np
from scipy.integrate import solve_ivp

from core.config import OrbitalParams, SolverConfig, Solution
from core.physics import RS, build_initial_state, geodesic_rhs


# Private integrators
def _rk4(Y0: list[float], t_end: float, h: float) -> tuple[np.ndarray, np.ndarray]:
    """Classic fixed-step RK4."""
    n = max(1, int(round(t_end / h)))
    h_act = t_end / n
    t_arr = np.linspace(0.0, t_end, n + 1)
    y = np.zeros((n + 1, 4))
    y[0] = Y0

    for i in range(n):
        ti, yi = t_arr[i], y[i]
        k1 = h_act * np.array(geodesic_rhs(ti, yi))
        k2 = h_act * np.array(geodesic_rhs(ti + h_act/2, yi + k1/2))
        k3 = h_act * np.array(geodesic_rhs(ti + h_act/2, yi + k2/2))
        k4 = h_act * np.array(geodesic_rhs(ti + h_act, yi + k3))
        y[i + 1] = yi + (k1 + 2*k2 + 2*k3 + k4) / 6

        if y[i + 1, 0] <= RS * 1.005:   # Horizon reached 
            return t_arr[: i + 2], y[: i + 2]

    return t_arr, y


def _scipy(Y0: list[float], t_end: float, max_step: float, method: str) -> tuple[np.ndarray, np.ndarray]:
    """Adaptive integrator via scipy.integrate.solve_ivp."""
    sol = solve_ivp(
        geodesic_rhs,
        [0.0, t_end],
        Y0,
        method=method,
        max_step=max_step,
        rtol=1e-9,
        atol=1e-12,
    )
    return sol.t, sol.y.T


def run(params: OrbitalParams, cfg: SolverConfig) -> Solution:
    """
    Integrate a geodesic and return a Solution

    Parameters
    ----------
    params : OrbitalParams
        Human-readable initial conditions.
    cfg : SolverConfig
        Numerical integration settings.
    """
    r0 = params.r0_rs * RS
    Y0 = build_initial_state(r0, params.speed_frac, params.angle_deg)

    t0 = time.perf_counter()

    if cfg.solver == "RK4":
        tau_arr, y_arr = _rk4(Y0, cfg.tau_max, cfg.step_size)
    elif cfg.solver in ("RK45", "DOP853"):
        tau_arr, y_arr = _scipy(Y0, cfg.tau_max, cfg.step_size, cfg.solver)
    else:
        raise ValueError(f"Unknown solver '{cfg.solver}'.")

    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    return Solution(
        tau = tau_arr,
        r = y_arr[:, 0] / RS,    # Store in rs units
        phi = y_arr[:, 2],
        rdot = y_arr[:, 1],
        params = params,
        elapsed_ms = elapsed_ms,
    )