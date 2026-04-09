"""
Fast vectorized Riemann zeta function — GPU-accelerated with automatic CPU fallback.

Uses the Euler-Maclaurin summation formula (DLMF §25.2.9) which provides
analytic continuation of ζ(s) to the entire complex plane (except the pole
at s = 1).

Precision: float64 (~15 significant digits) — more than sufficient for
every visualisation in Manifold.

When CuPy is installed and a CUDA GPU is reachable, all heavy array work
runs on the GPU.  Otherwise NumPy is used transparently.
"""

from __future__ import annotations

import numpy as np

from manifold.math.gpu_backend import get_xp, to_device, to_numpy

# ── Precomputed constants ────────────────────────────────────────────────────
# Bernoulli numbers B_{2k} for k = 1 … 10
_B2K: list[float] = [
    1 / 6,          # B_2
    -1 / 30,        # B_4
    1 / 42,         # B_6
    -1 / 30,        # B_8
    5 / 66,         # B_10
    -691 / 2730,    # B_12
    7 / 6,          # B_14
    -3617 / 510,    # B_16
    43867 / 798,    # B_18
    -174611 / 330,  # B_20
]

# Factorials (2k)! for k = 1 … 10
_FACT2K: list[int] = []
_f = 1
for _i in range(1, 21):
    _f *= _i
    if _i % 2 == 0:
        _FACT2K.append(_f)


# ── Core vectorised zeta ─────────────────────────────────────────────────────

def zeta_array(
    s: np.ndarray,
    *,
    N: int = 128,
    K: int = 10,
    force_cpu: bool = False,
) -> np.ndarray:
    """
    Compute ζ(s) for an array of complex *s* values.

    Parameters
    ----------
    s : complex ndarray of any shape
    N : direct-summation cutoff  (default 128 — excellent for |Im s| ≤ 100)
    K : Bernoulli correction terms, max 10  (default 10)
    force_cpu : bypass CuPy even when a GPU is present

    Returns
    -------
    complex ndarray of ζ(s) values, same shape as *s*.
    """
    try:
        return _zeta_core(s, N=N, K=K, force_cpu=force_cpu)
    except Exception:
        # GPU out-of-memory or driver hiccup → retry on CPU
        if not force_cpu:
            return _zeta_core(s, N=N, K=K, force_cpu=True)
        raise


def _zeta_core(
    s: np.ndarray,
    *,
    N: int,
    K: int,
    force_cpu: bool,
) -> np.ndarray:
    xp = get_xp(force_cpu=force_cpu)

    shape = s.shape
    s_flat = to_device(
        np.asarray(s, dtype=np.complex128).ravel(),
        force_cpu=force_cpu,
    )

    # ── Direct sum   Σ_{n=1}^{N} n^{-s}  ────────────────────────────────────
    result = xp.zeros_like(s_flat)
    # Pre-compute log(n) once on host — tiny list, avoids repeated log calls
    log_ns = [float(np.log(n)) for n in range(1, N + 1)]
    for ln in log_ns:
        result += xp.exp(-ln * s_flat)

    # ── Euler-Maclaurin tail correction ──────────────────────────────────────
    log_N = float(np.log(N))

    #   N^{1-s} / (s - 1)
    result += xp.exp(log_N * (1 - s_flat)) / (s_flat - 1)
    #  −N^{-s} / 2
    result -= xp.exp(-log_N * s_flat) / 2

    # Bernoulli correction terms
    K = min(K, len(_B2K))
    for k in range(1, K + 1):
        # Rising Pochhammer: s(s+1)(s+2)…(s+2k−2)
        poch = xp.ones_like(s_flat)
        for j in range(2 * k - 1):
            poch = poch * (s_flat + j)
        coeff = _B2K[k - 1] / _FACT2K[k - 1]
        result += coeff * poch * xp.exp(-log_N * (s_flat + 2 * k - 1))

    # ── Pole at s = 1 → NaN ─────────────────────────────────────────────────
    near_pole = xp.abs(s_flat - 1) < 1e-10
    result = xp.where(near_pole, xp.array(complex("nan+nanj")), result)

    return to_numpy(result.reshape(shape))


# ── Convenience wrappers ─────────────────────────────────────────────────────

def zeta_critical_line(
    t_values: np.ndarray,
    **kw,
) -> np.ndarray:
    """Evaluate ζ(½ + it) for a real vector *t_values*."""
    s = 0.5 + 1j * np.asarray(t_values, dtype=float)
    return zeta_array(s, **kw)


def find_zeros(n_zeros: int = 15) -> list[complex]:
    """
    Locate the first *n_zeros* nontrivial zeros on the critical line
    using a fast grid evaluation of the Riemann-Siegel Z function
    followed by Brent root-finding.
    """
    from scipy.optimize import brentq
    from scipy.special import loggamma

    # Riemann-Siegel theta function  (vectorised, CPU)
    def theta(t: np.ndarray) -> np.ndarray:
        return (
            np.imag(loggamma(0.25 + 0.5j * t))
            - (t / 2) * np.log(np.pi)
        )

    # Scalar Z(t) for Brent refinement
    def Z_scalar(t: float) -> float:
        s = np.array([0.5 + 1j * t])
        z = zeta_array(s, force_cpu=True)[0]
        return float((np.exp(1j * theta(np.array([t]))[0]) * z).real)

    # ── Phase 1: coarse grid — find sign changes of Z(t) ────────────────────
    t_max = max(60.0, n_zeros * 4.0)
    n_grid = max(20_000, n_zeros * 2_000)
    t_grid = np.linspace(1.0, t_max, n_grid)

    zeta_vals = zeta_array(0.5 + 1j * t_grid)          # GPU-accelerated
    theta_vals = theta(t_grid)
    Z_vals = (np.exp(1j * theta_vals) * zeta_vals).real

    signs = np.sign(Z_vals)
    changes = np.where(np.diff(signs) != 0)[0]

    # ── Phase 2: refine each sign change with Brent's method ────────────────
    zeros: list[complex] = []
    for idx in changes:
        if len(zeros) >= n_zeros:
            break
        t_lo = float(t_grid[idx])
        t_hi = float(t_grid[idx + 1])
        try:
            t_zero = brentq(Z_scalar, t_lo, t_hi, xtol=1e-12)
            zeros.append(complex(0.5, t_zero))
        except ValueError:
            continue

    return zeros[:n_zeros]


def dirichlet_partial_sum(
    s_values: np.ndarray,
    n_terms: int = 100,
    force_cpu: bool = False,
) -> np.ndarray:
    """
    Partial sum of the Dirichlet series  Σ_{n=1}^{N} n^{-s}.

    Converges only for Re(s) > 1.  GPU-accelerated.
    """
    xp = get_xp(force_cpu=force_cpu)
    s_dev = to_device(s_values.astype(np.complex128), force_cpu=force_cpu)
    result = xp.zeros(s_dev.shape, dtype=xp.complex128)
    for n in range(1, n_terms + 1):
        result += xp.exp(-float(np.log(n)) * s_dev)
    return to_numpy(result)
