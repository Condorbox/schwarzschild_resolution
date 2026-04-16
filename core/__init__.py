"""
core — physics, data types, integration, and presets.
"""

from core.config  import OrbitalParams, SolverConfig, Solution
from core.physics import RS, M, lapse, geodesic_rhs, build_initial_state
from core.presets import PRESETS, Preset, get as get_preset, list_presets
from core         import solver

__all__ = [
    "OrbitalParams", "SolverConfig", "Solution",
    "RS", "M", "lapse", "geodesic_rhs", "build_initial_state",
    "PRESETS", "Preset", "get_preset", "list_presets",
    "solver",
]