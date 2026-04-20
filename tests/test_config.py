"""
tests/test_config.py
====================
Unit tests for core/config.py (OrbitalParams, SolverConfig) and
core/presets.py (PRESETS, get, list_presets).
"""

from __future__ import annotations

import pytest

from core.config  import OrbitalParams, SolverConfig
from core.presets import PRESETS, get, list_presets


class TestOrbitalParamsValidation:

    def test_default_values(self):
        p = OrbitalParams()
        assert p.r0_rs      == 8.0
        assert p.speed_frac == 1.0
        assert p.angle_deg  == 0.0

    def test_r0_too_small_raises(self):
        with pytest.raises(ValueError, match="r0_rs"):
            OrbitalParams(r0_rs=1.0)

    def test_r0_at_photon_sphere_raises(self):
        """r0_rs = 1.5 is the photon sphere — forbidden."""
        with pytest.raises(ValueError, match="r0_rs"):
            OrbitalParams(r0_rs=1.5)

    def test_r0_just_above_photon_sphere_ok(self):
        p = OrbitalParams(r0_rs=1.501)
        assert p.r0_rs == pytest.approx(1.501)

    def test_r0_very_large_ok(self):
        p = OrbitalParams(r0_rs=1e6)
        assert p.r0_rs == 1e6

    def test_negative_speed_raises(self):
        with pytest.raises(ValueError, match="speed_frac"):
            OrbitalParams(speed_frac=-0.1)

    def test_zero_speed_ok(self):
        """speed_frac = 0 is valid (particle starts at rest)."""
        p = OrbitalParams(speed_frac=0.0)
        assert p.speed_frac == 0.0

    def test_super_escape_speed_ok(self):
        """speed_frac > 1 is allowed (escape trajectory)."""
        p = OrbitalParams(speed_frac=2.5)
        assert p.speed_frac == 2.5

    @pytest.mark.parametrize("angle", [-180.0, -90.0, 0.0, 45.0, 90.0, 180.0])
    def test_any_angle_accepted(self, angle):
        """angle_deg has no validation constraint."""
        p = OrbitalParams(angle_deg=angle)
        assert p.angle_deg == angle


class TestSolverConfigValidation:

    def test_default_values(self):
        cfg = SolverConfig()
        assert cfg.tau_max   == 10_000.0
        assert cfg.step_size == 1.0
        assert cfg.solver    == "DOP853"

    def test_zero_tau_max_raises(self):
        with pytest.raises(ValueError, match="tau_max"):
            SolverConfig(tau_max=0.0)

    def test_negative_tau_max_raises(self):
        with pytest.raises(ValueError, match="tau_max"):
            SolverConfig(tau_max=-1.0)

    def test_zero_step_size_raises(self):
        with pytest.raises(ValueError, match="step_size"):
            SolverConfig(step_size=0.0)

    def test_negative_step_size_raises(self):
        with pytest.raises(ValueError, match="step_size"):
            SolverConfig(step_size=-0.5)

    def test_unknown_solver_raises(self):
        with pytest.raises(ValueError, match="solver"):
            SolverConfig(solver="EULER")  # type: ignore[arg-type]

    @pytest.mark.parametrize("solver", ["RK4", "RK45", "DOP853"])
    def test_valid_solvers_accepted(self, solver):
        cfg = SolverConfig(solver=solver)  # type: ignore[arg-type]
        assert cfg.solver == solver

    def test_very_small_step_size_ok(self):
        cfg = SolverConfig(step_size=1e-6)
        assert cfg.step_size == pytest.approx(1e-6)


EXPECTED_PRESETS = {"circular", "elliptical", "escape", "petal", "plunge"}


class TestPresets:

    def test_all_expected_presets_present(self):
        assert set(PRESETS.keys()) == EXPECTED_PRESETS

    def test_get_case_insensitive(self):
        for name in EXPECTED_PRESETS:
            p = get(name.upper())
            assert p is PRESETS[name]

    def test_get_unknown_raises_key_error(self):
        with pytest.raises(KeyError, match="unknown"):
            get("unknown")

    def test_list_presets_returns_all(self):
        names = {name for name, _ in list_presets()}
        assert names == EXPECTED_PRESETS

    def test_list_presets_has_descriptions(self):
        for name, desc in list_presets():
            assert isinstance(desc, str) and len(desc) > 0

    @pytest.mark.parametrize("name", list(EXPECTED_PRESETS))
    def test_preset_orbital_params_valid(self, name):
        """Each preset's OrbitalParams must pass its own __post_init__."""
        p = PRESETS[name]
        # If OrbitalParams were invalid, the module would have failed at import.
        assert p.orbital.r0_rs > 1.5
        assert p.orbital.speed_frac >= 0.0

    @pytest.mark.parametrize("name", list(EXPECTED_PRESETS))
    def test_preset_solver_config_valid(self, name):
        p = PRESETS[name]
        assert p.solver.tau_max   > 0.0
        assert p.solver.step_size > 0.0
        assert p.solver.solver in ("RK4", "RK45", "DOP853")

    def test_plunge_preset_has_low_speed(self):
        """Plunge preset is defined as low angular momentum."""
        p = PRESETS["plunge"]
        assert p.orbital.speed_frac < 0.5

    def test_escape_preset_has_high_speed(self):
        """Escape preset must have speed above circular (speed_frac > 1)."""
        p = PRESETS["escape"]
        assert p.orbital.speed_frac > 1.0

    def test_circular_preset_is_tangential(self):
        """Circular preset should have angle=0 (purely tangential launch)."""
        p = PRESETS["circular"]
        assert p.orbital.angle_deg == 0.0

    def test_petal_preset_has_large_radius(self):
        """Petal orbit is far from the BH."""
        p = PRESETS["petal"]
        assert p.orbital.r0_rs >= 20.0

    def test_preset_descriptions_are_unique(self):
        descriptions = [p.description for p in PRESETS.values()]
        assert len(descriptions) == len(set(descriptions))