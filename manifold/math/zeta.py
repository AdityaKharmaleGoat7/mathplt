"""
Riemann Zeta function computations — GPU-accelerated with automatic CPU fallback.

Uses the fast Euler-Maclaurin implementation in ``zeta_fast`` by default.
All functions return numpy arrays for plotting.
Expensive grid computations are cached to ~/.cache/manifold/.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import numpy as np

from manifold.config import CACHE_DIR
from manifold.math.zeta_fast import (
    dirichlet_partial_sum,
    find_zeros,
    zeta_array,
    zeta_critical_line,
)


def _cache_path(key: str) -> Path:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return Path(CACHE_DIR) / f"{key}.npz"


def _cache_key(**kwargs) -> str:
    """Hash keyword arguments to a short hex string for cache file naming."""
    serialized = str(sorted(kwargs.items()))
    return hashlib.md5(serialized.encode()).hexdigest()[:16]


def zeta_grid(
    re_range: tuple[float, float] = (0.0, 1.0),
    im_range: tuple[float, float] = (0.0, 50.0),
    re_points: int = 80,
    im_points: int = 300,
    dps: int = 25,
    use_cache: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute ζ(s) on a rectangular grid in the complex s-plane.

    Parameters:
        re_range:   (min, max) for Re(s)
        im_range:   (min, max) for Im(s)
        re_points:  Number of points along real axis
        im_points:  Number of points along imaginary axis
        dps:        Kept for API compatibility (float64 precision used)
        use_cache:  Load from ~/.cache/manifold/ if available

    Returns:
        RE: (re_points, im_points) real parts of s
        IM: (re_points, im_points) imaginary parts of s
        Z:  (re_points, im_points) complex ndarray of ζ(s) values
    """
    key = _cache_key(
        fn="zeta_grid_fast",
        re_range=re_range, im_range=im_range,
        re_points=re_points, im_points=im_points,
    )
    cache_file = _cache_path(key)

    if use_cache and cache_file.exists():
        data = np.load(str(cache_file))
        return data["RE"], data["IM"], data["Z"]

    re_vals = np.linspace(re_range[0], re_range[1], re_points)
    im_vals = np.linspace(im_range[0], im_range[1], im_points)
    RE, IM = np.meshgrid(re_vals, im_vals, indexing="ij")
    S = RE + 1j * IM

    Z = zeta_array(S)

    if use_cache:
        np.savez_compressed(str(cache_file), RE=RE, IM=IM, Z=Z)

    return RE, IM, Z


def zeta_on_critical_line(
    t_values: np.ndarray,
    dps: int = 25,
    use_cache: bool = True,
) -> np.ndarray:
    """
    Evaluate ζ(1/2 + it) for a vector of t values.

    Returns complex ndarray of same shape as t_values.
    """
    key = _cache_key(
        fn="critical_line_fast",
        t_min=float(t_values[0]),
        t_max=float(t_values[-1]),
        n=len(t_values),
    )
    cache_file = _cache_path(key)

    if use_cache and cache_file.exists():
        return np.load(str(cache_file))["Z"]

    result = zeta_critical_line(t_values)

    if use_cache:
        np.savez_compressed(str(cache_file), Z=result)

    return result


def find_zeros_on_critical_line(
    n_zeros: int = 15,
    dps: int = 50,
) -> list[complex]:
    """
    Find the first n nontrivial zeros of ζ(s) on the critical line Re(s) = 1/2.

    Uses fast Euler-Maclaurin evaluation + Brent root-finding on the
    Riemann-Siegel Z function.

    Known zeros (Im part): 14.135, 21.022, 25.011, 30.425, 32.935, ...

    Returns list of complex numbers.
    """
    return find_zeros(n_zeros)


def zeta_on_contour(
    contour_points: np.ndarray,
    dps: int = 25,
) -> np.ndarray:
    """
    Evaluate ζ(s) at each point of a contour in the s-plane.

    Parameters:
        contour_points: 1D complex ndarray of s values
    Returns:
        complex ndarray of ζ(s) values
    """
    return zeta_array(np.asarray(contour_points, dtype=complex))


def winding_number_on_contour(
    contour_points: np.ndarray,
    dps: int = 25,
) -> float:
    """
    Estimate the winding number of ζ(s) around the origin for a closed contour.
    """
    w_values = zeta_on_contour(contour_points, dps=dps)
    if not np.isclose(w_values[0], w_values[-1]):
        w_values = np.append(w_values, w_values[0])
    angles = np.angle(w_values)
    total_angle = float(np.sum(np.diff(np.unwrap(angles))))
    return total_angle / (2 * np.pi)


def dirichlet_series_partial_sum(
    s_values: np.ndarray,
    n_terms: int = 100,
    dps: int = 25,
) -> np.ndarray:
    """
    Compute partial sum of Dirichlet series: sum_{n=1}^{N} n^{-s}

    Only converges for Re(s) > 1. GPU-accelerated.
    """
    return dirichlet_partial_sum(s_values, n_terms=n_terms)
