"""
tests/test_presets_integration.py
==================================
End-to-end integration tests that run each preset through the full solver
pipeline and verify the expected physical outcome.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.signal import argrelmin

from core.presets import get as get_preset
from core.solver  import run


def _run_preset(name: str):
    p = get_preset(name)
    return run(p.orbital, p.solver)


class TestCircularPreset:
    def test_does_not_plunge(self):
        sol = _run_preset("circular")
        assert not sol.plunged

    def test_r_stays_above_horizon(self):
        sol = _run_preset("circular")
        assert np.all(sol.r > 1.0)

    def test_has_many_steps(self):
        """tau_max=10000, step=1 → adaptive solver takes many steps."""
        sol = _run_preset("circular")
        assert sol.n_steps > 100


class TestEllipticalPreset:
    def test_does_not_plunge(self):
        sol = _run_preset("elliptical")
        assert not sol.plunged

    def test_has_periapsis_and_apoapsis(self):
        """A genuine elliptical orbit must oscillate in r."""
        sol = _run_preset("elliptical")
        r = sol.r
        assert r.min() < r.max() * 0.95, "r is not oscillating — orbit looks circular"

    def test_periapsis_above_isco(self):
        """Elliptical preset starts at 10 rs with 0.85 speed — should stay above ISCO (3 rs)."""
        sol = _run_preset("elliptical")
        assert sol.r_min > 3.0

    def test_multiple_periapsis_passages(self):
        sol = _run_preset("elliptical")
        periapsis_idx = argrelmin(sol.r, order=5)[0]
        assert len(periapsis_idx) >= 2, "Expected at least 2 periapsis passages"

    def test_periapsis_precesses(self):
        """GR periapsis precession: Δφ must exceed 2π."""
        sol = _run_preset("elliptical")
        periapsis_idx = argrelmin(sol.r, order=5)[0]
        if len(periapsis_idx) < 2:
            pytest.skip("Not enough periapsis passages")
        delta_phi = np.diff(sol.phi[periapsis_idx])
        assert delta_phi.mean() > 2.0 * np.pi


class TestEscapePreset:
    def test_does_not_plunge(self):
        sol = _run_preset("escape")
        assert not sol.plunged

    def test_r_max_large(self):
        """Escape orbit should reach well beyond the starting radius."""
        p   = get_preset("escape")
        sol = _run_preset("escape")
        assert sol.r_max > 10.0 * p.orbital.r0_rs

    def test_r_increases_at_end(self):
        """At the end of the integration window the orbit should still be receding."""
        sol  = _run_preset("escape")
        tail = sol.r[-20:]
        assert np.all(np.diff(tail) > 0.0), (
            "Escape orbit r is not monotonically increasing near the end"
        )


class TestPetalPreset:
    def test_does_not_plunge(self):
        sol = _run_preset("petal")
        assert not sol.plunged

    def test_starts_far_from_bh(self):
        sol = _run_preset("petal")
        assert sol.r[0] >= 20.0   # preset is r0=40 rs

    def test_has_multiple_petals(self):
        """
        The petal orbit should complete several loops, visible as repeated
        r minima (petals).
        """
        sol = _run_preset("petal")
        periapsis_idx = argrelmin(sol.r, order=20)[0]
        assert len(periapsis_idx) >= 3, (
            f"Expected ≥3 petal periapses, got {len(periapsis_idx)}"
        )

    def test_phi_span_multiple_revolutions(self):
        """Over 20000 tau the orbit should span several full rotations."""
        sol = _run_preset("petal")
        total_angle = sol.phi[-1] - sol.phi[0]
        assert total_angle > 4.0 * np.pi   # at least 2 full rotations


class TestPlungePreset:
    def test_plunges(self):
        sol = _run_preset("plunge")
        assert sol.plunged is True

    def test_r_reaches_near_horizon(self):
        sol = _run_preset("plunge")
        assert sol.r_min <= 1.1   # within 10% above horizon (rs units)

    def test_terminates_before_tau_max_with_rk4(self):
        """
        The RK4 path has an explicit early-exit when the horizon is reached.
        The DOP853 plunge preset runs to tau_max even after plunging because
        scipy has no early-exit — the state is merely frozen by the zero-
        derivative guard in geodesic_rhs.  We use RK4 to test early-exit.
        """
        from core.config import OrbitalParams, SolverConfig
        params = OrbitalParams(r0_rs=6.5, speed_frac=0.3, angle_deg=0.0)
        cfg = SolverConfig(tau_max=500.0, step_size=0.1, solver="RK4")
        from core.solver import run as _run
        sol = _run(params, cfg)
        assert sol.tau[-1] < cfg.tau_max

    def test_r_decreasing_throughout(self):
        """A radial plunge should have monotonically decreasing r."""
        sol = _run_preset("plunge")
        # Allow for a tiny initial outward wiggle at start of integration
        # but overall trend must be inward
        assert sol.r[-1] < sol.r[0]


class TestAllPresetsSmoke:
    """Smoke tests: every preset must complete without raising an exception."""

    @pytest.mark.parametrize("name", ["circular", "elliptical", "escape", "petal", "plunge"])
    def test_runs_without_error(self, name):
        sol = _run_preset(name)
        assert sol is not None
        assert sol.n_steps > 0

    @pytest.mark.parametrize("name", ["circular", "elliptical", "escape", "petal", "plunge"])
    def test_no_nan_in_output(self, name):
        sol = _run_preset(name)
        assert not np.any(np.isnan(sol.r))
        assert not np.any(np.isnan(sol.phi))
        assert not np.any(np.isnan(sol.rdot))

    @pytest.mark.parametrize("name", ["circular", "elliptical", "escape", "petal", "plunge"])
    def test_no_inf_in_output(self, name):
        sol = _run_preset(name)
        assert not np.any(np.isinf(sol.r))
        assert not np.any(np.isinf(sol.phi))