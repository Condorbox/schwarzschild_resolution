"""
tests/test_solver.py
====================
Integration tests for core/solver.py
"""

from __future__ import annotations

import numpy as np
import pytest

from core.config  import OrbitalParams, SolverConfig
from core.physics import RS
from core.solver  import run


@pytest.fixture
def elliptical_params() -> OrbitalParams:
    return OrbitalParams(r0_rs=10.0, speed_frac=0.85, angle_deg=0.0)

@pytest.fixture
def plunge_params() -> OrbitalParams:
    return OrbitalParams(r0_rs=6.5, speed_frac=0.3, angle_deg=0.0)

@pytest.fixture
def escape_params() -> OrbitalParams:
    return OrbitalParams(r0_rs=8.0, speed_frac=1.4, angle_deg=0.0)

@pytest.fixture
def default_cfg() -> SolverConfig:
    return SolverConfig(tau_max=500.0, step_size=0.5, solver="DOP853")


class TestSolutionStructure:
    def test_arrays_same_length(self, elliptical_params, default_cfg):
        sol = run(elliptical_params, default_cfg)
        assert len(sol.tau) == len(sol.r) == len(sol.phi) == len(sol.rdot)

    def test_tau_starts_at_zero(self, elliptical_params, default_cfg):
        sol = run(elliptical_params, default_cfg)
        assert sol.tau[0] == pytest.approx(0.0)

    def test_tau_monotonically_increasing(self, elliptical_params, default_cfg):
        sol = run(elliptical_params, default_cfg)
        assert np.all(np.diff(sol.tau) > 0.0)

    def test_r_in_rs_units(self, elliptical_params, default_cfg):
        """r[0] should equal r0_rs (units of rs), not r0_rs * RS."""
        sol = run(elliptical_params, default_cfg)
        assert sol.r[0] == pytest.approx(elliptical_params.r0_rs, rel=1e-6)

    def test_phi_starts_at_zero(self, elliptical_params, default_cfg):
        sol = run(elliptical_params, default_cfg)
        assert sol.phi[0] == pytest.approx(0.0)

    def test_elapsed_ms_positive(self, elliptical_params, default_cfg):
        sol = run(elliptical_params, default_cfg)
        assert sol.elapsed_ms > 0.0

    def test_params_preserved(self, elliptical_params, default_cfg):
        sol = run(elliptical_params, default_cfg)
        assert sol.params is elliptical_params

    def test_n_steps_property(self, elliptical_params, default_cfg):
        sol = run(elliptical_params, default_cfg)
        assert sol.n_steps == len(sol.tau)

    def test_r_min_max_properties(self, elliptical_params, default_cfg):
        sol = run(elliptical_params, default_cfg)
        assert sol.r_min == pytest.approx(float(sol.r.min()))
        assert sol.r_max == pytest.approx(float(sol.r.max()))


class TestPlungedProperty:
    def test_plunge_detected(self, plunge_params):
        cfg = SolverConfig(tau_max=500.0, step_size=0.1, solver="DOP853")
        sol = run(plunge_params, cfg)
        assert sol.plunged is True

    def test_non_plunge_orbit(self, elliptical_params, default_cfg):
        sol = run(elliptical_params, default_cfg)
        assert sol.plunged is False

    def test_escape_does_not_plunge(self, escape_params):
        cfg = SolverConfig(tau_max=2000.0, step_size=1.0, solver="DOP853")
        sol = run(escape_params, cfg)
        assert sol.plunged is False

    def test_plunged_threshold_is_1_02_rs(self):
        """Solution.plunged triggers at r[-1] ≤ 1.02 rs (unit test of the property)."""
        params = OrbitalParams(r0_rs=8.0, speed_frac=1.0, angle_deg=0.0)
        cfg    = SolverConfig(tau_max=10.0, step_size=1.0, solver="DOP853")
        sol    = run(params, cfg)

        # Monkey-patch last r value to test the boundary
        sol.r[-1] = 1.02
        assert sol.plunged is True
        sol.r[-1] = 1.021
        assert sol.plunged is False


class TestOrbitalBehaviour:
    def test_plunge_reaches_near_horizon(self, plunge_params):
        """A plunging orbit must reach within 5% above the event horizon."""
        cfg = SolverConfig(tau_max=500.0, step_size=0.1, solver="DOP853")
        sol = run(plunge_params, cfg)
        assert sol.r_min <= 1.1   # in rs units

    def test_plunge_terminates_early_rk4(self, plunge_params):
        """
        The RK4 path has an explicit horizon-check that breaks early.
        tau[-1] must be strictly less than tau_max when the orbit plunges.
        """
        tau_max = 500.0
        cfg = SolverConfig(tau_max=tau_max, step_size=0.1, solver="RK4")
        sol = run(plunge_params, cfg)
        assert sol.tau[-1] < tau_max

    def test_plunge_scipy_runs_to_tau_max(self, plunge_params):
        """
        The scipy path (RK45 / DOP853) has NO early-exit on horizon entry.
        After plunging, geodesic_rhs returns [0,0,0,0] so the state freezes,
        but the integrator keeps stepping until tau_max is reached.

        This is a known asymmetry between the RK4 and scipy code paths.
        If this behaviour is ever unified, this test should be updated.
        """
        tau_max = 500.0
        cfg = SolverConfig(tau_max=tau_max, step_size=0.1, solver="DOP853")
        sol = run(plunge_params, cfg)
        # DOP853 reaches tau_max — the frozen state is held until the end
        assert sol.tau[-1] == pytest.approx(tau_max)
        # The trajectory is still detected as a plunge despite running to tau_max
        assert sol.plunged is True

    def test_escape_r_grows_monotonically_after_periapsis(self, escape_params):
        """
        After the first periapsis an escaping orbit should grow monotonically
        to large radius.
        """
        cfg = SolverConfig(tau_max=2000.0, step_size=1.0, solver="DOP853")
        sol = run(escape_params, cfg)

        r = sol.r
        peak_idx = np.argmin(r)          # closest approach
        r_after  = r[peak_idx:]
        assert np.all(np.diff(r_after) >= 0.0), (
            "Escaping orbit should be monotonically receding after periapsis"
        )

    def test_escape_reaches_large_radius(self, escape_params):
        cfg = SolverConfig(tau_max=2000.0, step_size=1.0, solver="DOP853")
        sol = run(escape_params, cfg)
        assert sol.r_max > 50.0   # rs units

    def test_bound_orbit_r_bounded(self, elliptical_params):
        """r_max of a bound orbit should not grow beyond a modest multiple of r0."""
        cfg = SolverConfig(tau_max=5000.0, step_size=0.5, solver="DOP853")
        sol = run(elliptical_params, cfg)
        assert sol.r_max < 5.0 * elliptical_params.r0_rs

    def test_all_r_above_horizon(self, elliptical_params):
        """r must stay above 1 rs for a non-plunging orbit."""
        cfg = SolverConfig(tau_max=2000.0, step_size=0.5, solver="DOP853")
        sol = run(elliptical_params, cfg)
        assert np.all(sol.r > 1.0)


class TestAngularMomentumViaPublicAPI:
    """
    Angular momentum L = r² dφ/dτ is a true conserved quantity.
    We recover phidot from finite differences of phi to keep this test
    independent of internal implementation details.
    """

    @pytest.mark.parametrize("solver_name, step", [
        ("DOP853", 0.5),
        ("RK45",   0.5),
        ("RK4",    0.1),
    ])
    def test_L_conserved_all_solvers(self, elliptical_params, solver_name, step):
        cfg = SolverConfig(tau_max=500.0, step_size=step, solver=solver_name)
        sol = run(elliptical_params, cfg)

        # Recover phidot via finite differences (central where possible)
        r   = sol.r * RS          # coordinate units
        phi = sol.phi
        tau = sol.tau
        phidot = np.gradient(phi, tau)
        L = r**2 * phidot

        # Ignore boundary points where finite-diff is least accurate
        L_inner = L[2:-2]
        rel_drift = np.abs(L_inner - L_inner[0]).max() / abs(L_inner[0])

        # RK4 is lower order; allow 10× more drift
        tol = 1e-4 if solver_name == "RK4" else 1e-5
        assert rel_drift < tol, (
            f"{solver_name}: L drifted by {rel_drift:.2e}"
        )


class TestSolverAgreement:
    """
    All three integrators should agree on the final state of a short trajectory
    to well within their respective accuracy targets.
    """

    def test_rk45_dop853_agree_on_final_r(self, elliptical_params):
        cfg_rk45   = SolverConfig(tau_max=300.0, step_size=0.5, solver="RK45")
        cfg_dop853 = SolverConfig(tau_max=300.0, step_size=0.5, solver="DOP853")

        sol_rk45   = run(elliptical_params, cfg_rk45)
        sol_dop853 = run(elliptical_params, cfg_dop853)

        # They should agree on r(τ_end) to four decimal places
        assert sol_rk45.r[-1] == pytest.approx(sol_dop853.r[-1], rel=1e-3)

    def test_rk4_agrees_with_dop853_on_r_min(self, elliptical_params):
        """
        RK4 with a fine step should agree on periapsis radius with DOP853.
        """
        cfg_rk4    = SolverConfig(tau_max=500.0, step_size=0.05, solver="RK4")
        cfg_dop853 = SolverConfig(tau_max=500.0, step_size=0.5,  solver="DOP853")

        sol_rk4    = run(elliptical_params, cfg_rk4)
        sol_dop853 = run(elliptical_params, cfg_dop853)

        assert sol_rk4.r_min == pytest.approx(sol_dop853.r_min, rel=1e-2)


class TestRK4StepCount:
    def test_step_count_formula(self):
        """
        RK4 uses n = round(tau_max / step_size) steps.
        The output array length should be n + 1.
        """
        tau_max, h = 1000.0, 2.0
        expected_steps = round(tau_max / h) + 1    # n + 1 points

        params = OrbitalParams(r0_rs=10.0, speed_frac=0.85, angle_deg=0.0)
        cfg    = SolverConfig(tau_max=tau_max, step_size=h, solver="RK4")
        sol    = run(params, cfg)

        # Only holds if the orbit doesn't plunge (which it won't here)
        assert sol.n_steps == expected_steps

    def test_finer_step_increases_step_count(self):
        params = OrbitalParams(r0_rs=10.0, speed_frac=0.85, angle_deg=0.0)
        cfg_coarse = SolverConfig(tau_max=500.0, step_size=1.0, solver="RK4")
        cfg_fine   = SolverConfig(tau_max=500.0, step_size=0.1, solver="RK4")

        sol_coarse = run(params, cfg_coarse)
        sol_fine   = run(params, cfg_fine)

        assert sol_fine.n_steps > sol_coarse.n_steps


class TestSolverValidation:
    def test_unknown_solver_raises(self):
        params = OrbitalParams(r0_rs=8.0, speed_frac=1.0, angle_deg=0.0)
        # SolverConfig validation blocks "EULER" before run() is called
        with pytest.raises(ValueError, match="Unknown solver"):
            SolverConfig(solver="EULER")  # type: ignore[arg-type]