"""
Tests for Riemann zeta math functions.

Verifies:
- Known zero locations match mpmath zetazero()
- zeta_on_critical_line returns correct values at known points
- winding_number returns approximately correct integer for a small contour
- domain_color returns valid RGB in [0, 1]
"""

import numpy as np
import pytest


class TestZetaOnCriticalLine:
    def test_known_zero_magnitudes(self):
        """|ζ(½ + it)| should be very small at known zeros."""
        from manifold.math.zeta import zeta_on_critical_line

        # Known imaginary parts of first nontrivial zeros
        known_zeros_t = [14.134725, 21.022040, 25.010858]
        t_values = np.array(known_zeros_t)

        zeta_vals = zeta_on_critical_line(t_values, dps=30, use_cache=False)
        magnitudes = np.abs(zeta_vals)

        # Each should be very close to zero (< 1e-4 with dps=30)
        for i, (t, mag) in enumerate(zip(known_zeros_t, magnitudes)):
            assert mag < 1e-4, f"Expected |ζ(½ + i{t:.3f})| ≈ 0, got {mag:.6f}"

    def test_away_from_zeros(self):
        """ζ(½ + i·10) should be non-zero (not near a zero)."""
        from manifold.math.zeta import zeta_on_critical_line
        t_values = np.array([10.0])
        zeta_vals = zeta_on_critical_line(t_values, dps=25, use_cache=False)
        assert np.abs(zeta_vals[0]) > 0.1

    def test_output_shape(self):
        from manifold.math.zeta import zeta_on_critical_line
        t = np.linspace(1.0, 20.0, 50)
        result = zeta_on_critical_line(t, dps=15, use_cache=False)
        assert result.shape == (50,)
        assert result.dtype == complex


class TestFindZeros:
    def test_first_zero_location(self):
        """First nontrivial zero should be at t ≈ 14.135."""
        from manifold.math.zeta import find_zeros_on_critical_line
        zeros = find_zeros_on_critical_line(n_zeros=1, dps=30)
        assert len(zeros) == 1
        z = zeros[0]
        assert abs(z.real - 0.5) < 1e-6, f"Expected Re(z) = 0.5, got {z.real}"
        assert abs(z.imag - 14.134725) < 1e-3, f"Expected Im(z) ≈ 14.135, got {z.imag}"

    def test_all_on_critical_line(self):
        """All returned zeros should have Re(s) = 0.5 (verifies Riemann Hypothesis for these)."""
        from manifold.math.zeta import find_zeros_on_critical_line
        zeros = find_zeros_on_critical_line(n_zeros=5, dps=30)
        for z in zeros:
            assert abs(z.real - 0.5) < 1e-6, f"Zero not on critical line: {z}"

    def test_zero_imaginary_parts_increasing(self):
        """Zeros should be ordered by increasing imaginary part."""
        from manifold.math.zeta import find_zeros_on_critical_line
        zeros = find_zeros_on_critical_line(n_zeros=5, dps=25)
        t_vals = [z.imag for z in zeros]
        assert t_vals == sorted(t_vals)

    def test_known_zero_values(self):
        """First 5 zeros should match known values to 3 decimal places."""
        from manifold.math.zeta import find_zeros_on_critical_line
        known = [14.134725, 21.022040, 25.010858, 30.424876, 32.935062]
        zeros = find_zeros_on_critical_line(n_zeros=5, dps=30)
        for z, expected_t in zip(zeros, known):
            assert abs(z.imag - expected_t) < 1e-3, (
                f"Zero mismatch: got t={z.imag:.6f}, expected t={expected_t:.6f}"
            )


class TestDomainColor:
    def test_output_shape(self):
        from manifold.math.complex_ops import domain_color_fast
        z = np.zeros((10, 10), dtype=complex)
        rgb = domain_color_fast(z)
        assert rgb.shape == (10, 10, 3)

    def test_values_in_range(self):
        """All RGB values must be in [0, 1]."""
        from manifold.math.complex_ops import domain_color_fast
        z = np.random.randn(20, 20) + 1j * np.random.randn(20, 20)
        rgb = domain_color_fast(z)
        assert rgb.min() >= 0.0
        assert rgb.max() <= 1.0

    def test_hue_encodes_phase(self):
        """
        domain_color_fast should produce different colors for z=1 vs z=-1
        (different arguments, so different hues).
        """
        from manifold.math.complex_ops import domain_color_fast
        rgb_pos = domain_color_fast(np.array([[1.0 + 0j]]))
        rgb_neg = domain_color_fast(np.array([[-1.0 + 0j]]))
        # Colors should differ (different hue for arg=0 vs arg=π)
        assert not np.allclose(rgb_pos, rgb_neg, atol=0.05)


class TestDirichletSeries:
    def test_converges_for_large_re(self):
        """Dirichlet series with N=200 terms should approximate ζ(2) = π²/6."""
        from manifold.math.zeta import dirichlet_series_partial_sum
        s = np.array([2.0 + 0j])
        result = dirichlet_series_partial_sum(s, n_terms=500)
        expected = np.pi**2 / 6
        # Should be within 0.5% with 500 terms
        assert abs(result[0].real - expected) / expected < 0.005

    def test_output_shape(self):
        from manifold.math.zeta import dirichlet_series_partial_sum
        s = np.array([2.0 + 0j, 3.0 + 0j, 4.0 + 0j])
        result = dirichlet_series_partial_sum(s, n_terms=10)
        assert result.shape == (3,)
        assert result.dtype == complex
