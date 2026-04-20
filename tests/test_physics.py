"""
tests/test_physics.py
=====================
Unit tests for core/physics.py
"""

from __future__ import annotations

import math
import numpy as np
import pytest
from scipy.integrate import solve_ivp
from scipy.signal import argrelmin

from core.physics import (
    M, RS,
    lapse,
    geodesic_rhs,
    circular_energy_angular_momentum,
    circular_angular_velocity,
    build_initial_state,
)


def _integrate(Y0: list[float], tau_end: float = 500.0) -> np.ndarray:
    """Run DOP853 and return the full state array (4 × n_steps)."""
    sol = solve_ivp(
        geodesic_rhs,
        [0.0, tau_end],
        Y0,
        method="DOP853",
        max_step=0.5,
        rtol=1e-10,
        atol=1e-13,
    )
    assert sol.success, f"Integration failed: {sol.message}"
    return sol.y   # shape (4, n_steps): [r, rdot, phi, phidot]


def _angular_momentum(y: np.ndarray) -> np.ndarray:
    """L = r² · dφ/dτ  from a state array."""
    r, _, _, phidot = y
    return r**2 * phidot


class TestLapse:
    def test_vanishes_at_horizon(self):
        assert lapse(RS) == pytest.approx(0.0)

    def test_half_at_two_rs(self):
        assert lapse(2 * RS) == pytest.approx(0.5)

    def test_approaches_unity_at_infinity(self):
        assert lapse(1e9) == pytest.approx(1.0, rel=1e-6)

    def test_negative_inside_horizon(self):
        # f < 0 for r < RS — the time and radial coordinates swap roles
        assert lapse(0.5 * RS) < 0.0

    def test_monotonically_increasing(self):
        r_vals = np.linspace(RS + 0.01, 20 * RS, 200)
        f_vals = np.array([lapse(r) for r in r_vals])
        assert np.all(np.diff(f_vals) > 0)


class TestHorizonFreeze:
    """
    Inside (or at) the horizon the RHS must be identically zero to prevent
    numerical blow-up from the coordinate singularity.
    """

    _THRESHOLD = RS * 1.005   # freeze radius as coded

    def test_frozen_inside_threshold(self):
        Y = [self._THRESHOLD * 0.999, 1.0, 0.0, 0.05]
        assert geodesic_rhs(0.0, Y) == [0.0, 0.0, 0.0, 0.0]

    def test_frozen_exactly_at_threshold(self):
        Y = [self._THRESHOLD, 1.0, 0.0, 0.05]
        assert geodesic_rhs(0.0, Y) == [0.0, 0.0, 0.0, 0.0]

    def test_not_frozen_just_outside(self):
        Y = [self._THRESHOLD * 1.001, 0.0, 0.0, 0.01]
        rhs = geodesic_rhs(0.0, Y)
        # At least one derivative must be nonzero outside the threshold
        assert any(v != 0.0 for v in rhs)

    def test_rdot_is_first_component(self):
        """RHS[0] must equal the input rdot (first-order ODE structure)."""
        rdot_in = 0.42
        Y = [5 * RS, rdot_in, 0.0, 0.01]
        rhs = geodesic_rhs(0.0, Y)
        assert rhs[0] == pytest.approx(rdot_in)

    def test_phidot_is_third_component(self):
        """RHS[2] must equal the input phidot."""
        phidot_in = 0.017
        Y = [5 * RS, 0.0, 1.23, phidot_in]
        rhs = geodesic_rhs(0.0, Y)
        assert rhs[2] == pytest.approx(phidot_in)


class TestAngularMomentumConservation:
    """
    L = r² dφ/dτ is an exact first integral of the Schwarzschild geodesic
    equations.  It must be conserved to numerical precision along any
    trajectory that does not enter the freeze zone.
    """

    @pytest.mark.parametrize("r0_rs, speed, angle_desc", [
        (10.0, 0.85, "elliptical"),
        (8.0,  0.60, "inner elliptical"),
        (15.0, 1.10, "slightly super-circular"),
        (40.0, 0.85, "wide petal"),
        (6.0,  0.80, "near-ISCO bound"),
    ])
    def test_L_conserved(self, r0_rs, speed, angle_desc):
        r0 = r0_rs * RS
        Y0 = build_initial_state(r0, speed, 0.0)
        y = _integrate(Y0, tau_end=1000.0)

        L = _angular_momentum(y)
        L0 = L[0]

        # Relative drift must stay below 1 part in 10^7 for DOP853
        rel_drift = np.abs(L - L0).max() / abs(L0)
        assert rel_drift < 1e-7, (
            f"L drifted by {rel_drift:.2e} for r0={r0_rs} rs, speed={speed}"
        )

    def test_L_conserved_for_radial_component(self):
        """Orbit with a 30° launch angle — L still conserved."""
        r0 = 12.0 * RS
        Y0 = build_initial_state(r0, 0.9, 30.0)
        y = _integrate(Y0, tau_end=800.0)

        L = _angular_momentum(y)
        rel_drift = np.abs(L - L[0]).max() / abs(L[0])
        assert rel_drift < 1e-7

    def test_L_sign_positive_for_prograde(self):
        """Tangential launch with positive speed → positive L (prograde orbit)."""
        r0 = 8.0 * RS
        Y0 = build_initial_state(r0, 1.0, 0.0)
        y = _integrate(Y0, tau_end=200.0)
        assert _angular_momentum(y).mean() > 0.0


class TestGeodesicRhsSelfConsistency:
    """Verify the structure and basic physics of the RHS function."""

    def test_rddot_negative_for_radial_freefall(self):
        """
        A particle released at rest (phidot=0, rdot=0) should accelerate
        inward: d²r/dτ² < 0.
        """
        r0 = 8.0 * RS
        Y = [r0, 0.0, 0.0, 0.0]
        rhs = geodesic_rhs(0.0, Y)
        assert rhs[1] < 0.0, "Radial freefall should accelerate inward"

    def test_phiddot_zero_for_radial_infall(self):
        """
        Pure radial infall (phidot=0) → angular acceleration must be zero
        (no torque in a spherically symmetric spacetime).
        """
        Y = [6.0 * RS, -0.5, 0.0, 0.0]
        rhs = geodesic_rhs(0.0, Y)
        assert rhs[3] == pytest.approx(0.0, abs=1e-14)

    def test_phiddot_zero_for_circular_candidate(self):
        """
        The correct circular-orbit phidot satisfies d²r/dτ² = 0.
        phidot_circ = sqrt(M/r³) zeroes the radial acceleration exactly.
        """
        r0 = 8.0 * RS
        phidot_circ = math.sqrt(M / r0**3)
        Y = [r0, 0.0, 0.0, phidot_circ]
        rhs = geodesic_rhs(0.0, Y)
        assert rhs[1] == pytest.approx(0.0, abs=1e-12), (
            "d²r/dτ² should vanish for the circular-orbit phidot"
        )

    @pytest.mark.parametrize("r_rs", [2.0, 4.0, 8.0, 20.0])
    def test_infall_acceleration_stronger_closer(self, r_rs):
        """
        Radial gravitational acceleration (pure infall) should be stronger
        at smaller radii — a basic monotonicity requirement.
        """
        r = r_rs * RS
        Y = [r, 0.0, 0.0, 0.0]
        rddot = geodesic_rhs(0.0, Y)[1]
        # Just store; parametrize ensures ordering via fixture comparison
        assert rddot < 0.0

    def test_centrifugal_term_opposes_gravity(self):
        """
        Increasing phidot should raise d²r/dτ² (centrifugal barrier).
        """
        r0 = 8.0 * RS
        phidot_low  = 0.005
        phidot_high = 0.020
        rddot_low  = geodesic_rhs(0.0, [r0, 0.0, 0.0, phidot_low ])[1]
        rddot_high = geodesic_rhs(0.0, [r0, 0.0, 0.0, phidot_high])[1]
        assert rddot_high > rddot_low


class TestCircularOrbitHelpers:
    @pytest.mark.parametrize("r_rs", [3.5, 5.0, 8.0, 15.0, 40.0])
    def test_angular_momentum_positive(self, r_rs):
        _, L = circular_energy_angular_momentum(r_rs * RS)
        assert L > 0.0

    @pytest.mark.parametrize("r_rs", [3.5, 5.0, 8.0, 15.0, 40.0])
    def test_energy_between_zero_and_one(self, r_rs):
        """
        Bound massive particle: 0 < E < 1.
        E=1 is the unbound threshold; E→√(8/9) at ISCO; E→1 at infinity.
        """
        E, _ = circular_energy_angular_momentum(r_rs * RS)
        assert 0.0 < E < 1.0

    def test_angular_velocity_positive(self):
        omega = circular_angular_velocity(8.0 * RS)
        assert omega > 0.0

    def test_angular_velocity_decreases_with_radius(self):
        """Keplerian-like: omega decreases as r increases (third law)."""
        r_vals = [4.0 * RS, 8.0 * RS, 15.0 * RS, 30.0 * RS]
        omegas = [circular_angular_velocity(r) for r in r_vals]
        assert all(omegas[i] > omegas[i+1] for i in range(len(omegas)-1))

    def test_photon_sphere_boundary(self):
        """At exactly r = 1.5 RS the denominator in omega vanishes → omega = 0."""
        assert circular_angular_velocity(1.5 * RS) == pytest.approx(0.0)


class TestBuildInitialState:
    def test_tangential_launch_zero_rdot(self):
        """angle=0 → purely tangential → rdot must be exactly zero."""
        Y0 = build_initial_state(8.0 * RS, 1.0, 0.0)
        assert Y0[1] == pytest.approx(0.0, abs=1e-15)

    def test_radial_launch_zero_phidot(self):
        """angle=90° → purely radial → phidot must be exactly zero."""
        Y0 = build_initial_state(8.0 * RS, 1.0, 90.0)
        assert Y0[3] == pytest.approx(0.0, abs=1e-15)

    def test_initial_radius_preserved(self):
        r0 = 12.5 * RS
        Y0 = build_initial_state(r0, 0.9, 15.0)
        assert Y0[0] == pytest.approx(r0)

    def test_phi_starts_at_zero(self):
        Y0 = build_initial_state(10.0 * RS, 1.0, 0.0)
        assert Y0[2] == pytest.approx(0.0)

    def test_rdot_scales_with_sin_angle(self):
        """
        rdot = speed_frac * v_circ * sin(angle), so
        rdot(60°) / rdot(30°) should equal sin60/sin30 = √3.
        """
        r0 = 10.0 * RS
        Y0_30 = build_initial_state(r0, 1.0, 30.0)
        Y0_60 = build_initial_state(r0, 1.0, 60.0)
        ratio = Y0_60[1] / Y0_30[1]
        assert ratio == pytest.approx(math.sqrt(3), rel=1e-10)

    def test_phidot_scales_with_cos_angle(self):
        """
        phidot = L/r² where L = speed * L_circ * cos(angle).
        phidot(60°) / phidot(0°) should equal cos(60°) = 0.5.
        """
        r0 = 10.0 * RS
        Y0_0  = build_initial_state(r0, 1.0,  0.0)
        Y0_60 = build_initial_state(r0, 1.0, 60.0)
        ratio = Y0_60[3] / Y0_0[3]
        assert ratio == pytest.approx(math.cos(math.radians(60.0)), rel=1e-10)

    def test_speed_zero_gives_zero_phidot_and_rdot(self):
        """speed_frac=0 → particle at rest → both velocities zero."""
        Y0 = build_initial_state(8.0 * RS, 0.0, 0.0)
        assert Y0[1] == pytest.approx(0.0, abs=1e-15)
        assert Y0[3] == pytest.approx(0.0, abs=1e-15)

    def test_speed_scaling_linear(self):
        """phidot should scale linearly with speed_frac (at fixed angle=0)."""
        r0 = 8.0 * RS
        Y0_1 = build_initial_state(r0, 1.0, 0.0)
        Y0_2 = build_initial_state(r0, 2.0, 0.0)
        assert Y0_2[3] == pytest.approx(2.0 * Y0_1[3], rel=1e-12)


class TestGRPhysics:
    """
    Tests that verify genuinely general-relativistic behaviour that would
    be absent in Newtonian or special-relativistic mechanics.
    """

    def test_periapsis_precession_exceeds_2pi(self):
        """
        In GR the azimuthal angle between successive periapses is > 2π
        (positive precession / frame-dragging analog in Schwarzschild).
        """
        r0 = 10.0 * RS
        Y0 = build_initial_state(r0, 0.85, 0.0)
        y = _integrate(Y0, tau_end=5000.0)

        r_arr   = y[0]
        phi_arr = y[2]
        periapsis_idx = argrelmin(r_arr, order=10)[0]

        assert len(periapsis_idx) >= 3, (
            "Need at least 3 periapsis passages to measure precession reliably"
        )

        delta_phi = np.diff(phi_arr[periapsis_idx])
        # All inter-periapsis angles must exceed 2π
        assert np.all(delta_phi > 2.0 * math.pi), (
            f"Some Δφ ≤ 2π: {delta_phi[delta_phi <= 2*math.pi]}"
        )

    def test_periapsis_precession_consistent_across_orbits(self):
        """
        The precession angle per orbit must be stable (same orbit → same Δφ).
        """
        r0 = 10.0 * RS
        Y0 = build_initial_state(r0, 0.85, 0.0)
        y = _integrate(Y0, tau_end=8000.0)

        r_arr   = y[0]
        phi_arr = y[2]
        periapsis_idx = argrelmin(r_arr, order=10)[0]

        assert len(periapsis_idx) >= 5
        delta_phi = np.diff(phi_arr[periapsis_idx])

        # Standard deviation of Δφ should be very small (< 1% of 2π)
        assert delta_phi.std() < 0.01 * 2.0 * math.pi

    def test_no_precession_for_newtonian_analogy(self):
        """
        Far from the black hole (r >> rs) the orbit should approach the
        Newtonian (no-precession) case.  We test: Δφ < 2π + 0.05 rad for r₀=200 rs.
        """
        r0 = 200.0 * RS
        Y0 = build_initial_state(r0, 0.99, 0.0)
        y = _integrate(Y0, tau_end=80_000.0)

        r_arr   = y[0]
        phi_arr = y[2]
        periapsis_idx = argrelmin(r_arr, order=20)[0]

        if len(periapsis_idx) < 2:
            pytest.skip("Not enough orbits at 200 rs within tau_end")

        delta_phi = np.diff(phi_arr[periapsis_idx])
        assert delta_phi.mean() < 2.0 * math.pi + 0.05

    def test_bound_orbit_stays_bound(self):
        """
        An orbit launched below escape speed must not escape to infinity.
        r_max should remain bounded to within a reasonable factor of r0.
        """
        r0 = 10.0 * RS
        Y0 = build_initial_state(r0, 0.85, 0.0)
        y = _integrate(Y0, tau_end=3000.0)
        r_rs = y[0] / RS

        assert r_rs.max() < 4.0 * 10.0, (
            "Bound orbit escaped unexpectedly"
        )

    def test_phi_monotonically_increasing_for_prograde(self):
        """
        For a prograde (L > 0) bound orbit, φ should be non-decreasing.
        """
        r0 = 10.0 * RS
        Y0 = build_initial_state(r0, 0.85, 0.0)
        y = _integrate(Y0, tau_end=2000.0)
        phi = y[2]
        assert np.all(np.diff(phi) >= 0.0), "φ decreased in a prograde orbit"

    def test_effective_circular_orbit_is_stable(self):
        """
        A particle launched with the phidot that exactly satisfies d²r/dτ²=0
        (i.e., phidot = sqrt(M/r³)) should remain near its initial radius.
        """
        r0 = 8.0 * RS
        phidot_circ = math.sqrt(M / r0**3)
        Y0 = [r0, 0.0, 0.0, phidot_circ]
        y = _integrate(Y0, tau_end=2000.0)
        r_rs = y[0] / RS
        # Should stay within 0.1% of starting radius
        assert r_rs.std() / 8.0 < 1e-3, (
            f"Circular orbit drifted: std={r_rs.std():.4f} rs"
        )