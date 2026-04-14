from dataclasses import dataclass, field
from typing import Literal
 
SolverName = Literal["RK4", "RK45", "DOP853"]

@dataclass
class OrbitalParams:
    """Initial conditions for a geodesic, expressed in human-friendly units."""
 
    # Initial radius in units of the Schwarzschild radius (rs).
    r0_rs: float = 8.0
 
    # Speed as a fraction of the local circular orbit speed.
    speed_frac: float = 1.0
 
    # Launch angle in degrees: 0 = pure tangential, 90 = pure radial.
    angle_deg: float = 0.0
 
    def __post_init__(self) -> None:
        if self.r0_rs <= 1.5:
            raise ValueError(
                f"r0_rs={self.r0_rs} must be > 1.5 rs (photon sphere)."
            )
        if self.speed_frac < 0:
            raise ValueError("speed_frac must be non-negative.")
        

@dataclass
class SolverConfig:
    """Numerical integration settings."""
 
    tau_max: float = 10000.0   # Proper time to integrate.
    step_size: float = 1.0      # Fixed step (RK4) or max_step hint (RK45/DOP853).
    solver: SolverName = "DOP853"
 
    def __post_init__(self) -> None:
        if self.tau_max <= 0:
            raise ValueError("tau_max must be positive.")
        if self.step_size <= 0:
            raise ValueError("step_size must be positive.")
        if self.solver not in ("RK4", "RK45", "DOP853"):
            raise ValueError(f"Unknown solver '{self.solver}'. Use RK4, RK45, or DOP853.")
        

@dataclass
class Solution:
    """Output of a geodesic integration — a pure data container."""
 
    tau: "np.ndarray"           # Proper-time array.
    r: "np.ndarray"             # Radial coordinate (in rs units).
    phi: "np.ndarray"           # Azimuthal angle (radians).
    rdot: "np.ndarray"          # dr/dtau
    params: OrbitalParams       # The inputs that produced this solution.
    elapsed_ms: float = 0.0     # Wall-clock time for the integration.
 
    @property
    def plunged(self) -> bool:
        """True if the geodesic terminated inside the event horizon."""
        return float(self.r[-1]) <= 1.02
 
    @property
    def r_min(self) -> float:
        return float(self.r.min())
 
    @property
    def r_max(self) -> float:
        return float(self.r.max())
 
    @property
    def n_steps(self) -> int:
        return len(self.tau)