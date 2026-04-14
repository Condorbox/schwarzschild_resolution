"""
Named orbital parameter presets
"""

from __future__ import annotations
from config import OrbitalParams, SolverConfig
from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    description: str
    orbital: OrbitalParams
    solver: SolverConfig


PRESETS: dict[str, Preset] = {
    "circular": Preset(
        description="Stable circular orbit at 8 rs",
        orbital=OrbitalParams(r0_rs=8.0,  speed_frac=1.0,  angle_deg=0.0),
        solver =SolverConfig (tau_max=10_000, step_size=1.0, solver="DOP853"),
    ),
    "elliptical": Preset(
        description="Elliptical orbit (periapsis ~5 rs)",
        orbital=OrbitalParams(r0_rs=10.0, speed_frac=0.85, angle_deg=0.0),
        solver =SolverConfig (tau_max=5_000,  step_size=1.0, solver="DOP853"),
    ),
    "escape": Preset(
        description="Escape trajectory (v > v_circ)",
        orbital=OrbitalParams(r0_rs=8.0,  speed_frac=1.4,  angle_deg=0.0),
        solver =SolverConfig (tau_max=2_000,  step_size=1.0, solver="DOP853"),
    ),
    "petal": Preset(
        description="Precessing petal orbit far from the BH",
        orbital=OrbitalParams(r0_rs=40.0, speed_frac=0.85, angle_deg=65.0),
        solver =SolverConfig (tau_max=20_000, step_size=1.0, solver="DOP853"),
    ),
    "plunge": Preset(
        description="Low-angular-momentum plunge into the black hole",
        orbital=OrbitalParams(r0_rs=6.5,  speed_frac=0.3,  angle_deg=0.0),
        solver =SolverConfig (tau_max=500,   step_size=0.1, solver="DOP853"),
    ),
}


def get(name: str) -> Preset:
    """Retrieve a preset by name (case-insensitive)"""
    key = name.lower()
    if key not in PRESETS:
        available = ", ".join(PRESETS)
        raise KeyError(f"Unknown preset '{name}'. Available: {available}")
    return PRESETS[key]


def list_presets() -> list[tuple[str, str]]:
    """Return [(name, description), …] for display"""
    return [(k, v.description) for k, v in PRESETS.items()]