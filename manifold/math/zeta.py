"""
Riemann Zeta function computations backed by mpmath.

All functions return numpy arrays for plotting.
Expensive grid computations are cached to ~/.cache/manifold/ using numpy save/load.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Sequence

import numpy as np

from manifold.config import CACHE_DIR, DEFAULT_DPS, HIGH_DPS


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
    dps: int = DEFAULT_DPS,
    use_cache: bool = True,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute ζ(s) on a rectangular grid in the complex s-plane.

    Parameters:
        re_range:   (min, max) for Re(s)
        im_range:   (min, max) for Im(s)
        re_points:  Number of points along real axis
        im_points:  Number of points along imaginary axis
        dps:        mpmath decimal places of precision
        use_cache:  Load from ~/.cache/manifold/ if available

    Returns:
        RE: (re_points, im_points) real parts of s
        IM: (re_points, im_points) imaginary parts of s
        Z:  (re_points, im_points) complex ndarray of ζ(s) values
    """
    key = _cache_key(
        fn="zeta_grid",
        re_range=re_range, im_range=im_range,
        re_points=re_points, im_points=im_points, dps=dps,
    )
    cache_file = _cache_path(key)

    if use_cache and cache_file.exists():
        data = np.load(str(cache_file))
        return data["RE"], data["IM"], data["Z"]

    import mpmath
    mpmath.mp.dps = dps

    re_vals = np.linspace(re_range[0], re_range[1], re_points)
    im_vals = np.linspace(im_range[0], im_range[1], im_points)
    RE, IM = np.meshgrid(re_vals, im_vals, indexing="ij")
    Z = np.zeros_like(RE, dtype=complex)

    total = re_points * im_points
    done = 0
    for i, re in enumerate(re_vals):
        for j, im in enumerate(im_vals):
            try:
                s = mpmath.mpc(float(re), float(im))
                Z[i, j] = complex(mpmath.zeta(s))
            except (ValueError, ZeroDivisionError, mpmath.libmp.libhyper.NoConvergence):
                Z[i, j] = complex(np.nan, np.nan)
            done += 1
        if (i + 1) % max(1, re_points // 10) == 0:
            print(f"  zeta_grid: {done}/{total} points computed...", end="\r")
    print()

    if use_cache:
        np.savez_compressed(str(cache_file), RE=RE, IM=IM, Z=Z)

    return RE, IM, Z


def zeta_on_critical_line(
    t_values: np.ndarray,
    dps: int = DEFAULT_DPS,
    use_cache: bool = True,
) -> np.ndarray:
    """
    Evaluate ζ(1/2 + it) for a vector of t values.

    Returns complex ndarray of same shape as t_values.
    """
    key = _cache_key(
        fn="critical_line",
        t_min=float(t_values[0]),
        t_max=float(t_values[-1]),
        n=len(t_values),
        dps=dps,
    )
    cache_file = _cache_path(key)

    if use_cache and cache_file.exists():
        return np.load(str(cache_file))["Z"]

    import mpmath
    mpmath.mp.dps = dps

    result = np.zeros(len(t_values), dtype=complex)
    for i, t in enumerate(t_values):
        try:
            s = mpmath.mpc(0.5, float(t))
            result[i] = complex(mpmath.zeta(s))
        except (ValueError, ZeroDivisionError):
            result[i] = complex(np.nan, np.nan)
        if (i + 1) % max(1, len(t_values) // 10) == 0:
            print(f"  zeta_on_critical_line: {i+1}/{len(t_values)}...", end="\r")
    print()

    if use_cache:
        np.savez_compressed(str(cache_file), Z=result)

    return result


def find_zeros_on_critical_line(
    n_zeros: int = 15,
    dps: int = HIGH_DPS,
) -> list[complex]:
    """
    Find the first n nontrivial zeros of ζ(s) on the critical line Re(s) = 1/2.

    Uses mpmath.zetazero(n) which returns the n-th zero as 1/2 + it_n.

    Known zeros (Im part): 14.135, 21.022, 25.011, 30.425, 32.935, ...

    Returns list of complex numbers.
    """
    import mpmath
    mpmath.mp.dps = dps

    zeros = []
    for n in range(1, n_zeros + 1):
        z = mpmath.zetazero(n)
        zeros.append(complex(z))
    return zeros


def zeta_on_contour(
    contour_points: np.ndarray,
    dps: int = DEFAULT_DPS,
) -> np.ndarray:
    """
    Evaluate ζ(s) at each point of a contour in the s-plane.

    Parameters:
        contour_points: 1D complex ndarray of s values
    Returns:
        complex ndarray of ζ(s) values
    """
    import mpmath
    mpmath.mp.dps = dps

    result = np.zeros(len(contour_points), dtype=complex)
    for i, s in enumerate(contour_points):
        try:
            mp_s = mpmath.mpc(float(s.real), float(s.imag))
            result[i] = complex(mpmath.zeta(mp_s))
        except (ValueError, ZeroDivisionError):
            result[i] = complex(np.nan, np.nan)
    return result


def winding_number_on_contour(
    contour_points: np.ndarray,
    dps: int = DEFAULT_DPS,
) -> float:
    """
    Estimate the winding number of ζ(s) around the origin for a closed contour
    in the s-plane, using the argument principle.

    N(zeros inside contour) = (1/2πi) ∮ ζ'(s)/ζ(s) ds
    Computed via discrete angle accumulation of ζ(s) values around the contour.

    Returns the winding number (should be a non-negative integer for valid contours
    not passing through any zeros).
    """
    w_values = zeta_on_contour(contour_points, dps=dps)
    # Close the contour if not already closed
    if not np.isclose(w_values[0], w_values[-1]):
        w_values = np.append(w_values, w_values[0])
    angles = np.angle(w_values)
    total_angle = float(np.sum(np.diff(np.unwrap(angles))))
    return total_angle / (2 * np.pi)


def dirichlet_series_partial_sum(
    s_values: np.ndarray,
    n_terms: int = 100,
    dps: int = DEFAULT_DPS,
) -> np.ndarray:
    """
    Compute partial sum of Dirichlet series: sum_{n=1}^{N} n^{-s}

    Only converges for Re(s) > 1. Used to visualize analytic continuation.

    Returns complex ndarray of same shape as s_values.
    """
    # Vectorized over s_values
    result = np.zeros(s_values.shape, dtype=complex)
    for n in range(1, n_terms + 1):
        result += np.power(n, -s_values.astype(complex))
    return result
