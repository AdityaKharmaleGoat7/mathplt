"""
Analytic Continuation Animation.

Visualizes how the Riemann zeta function, originally defined as a Dirichlet series
  ζ(s) = Σ n^{-s}  for Re(s) > 1
is extended to the entire complex plane (except s = 1) via analytic continuation.

The animation shows:
  Left panel:  Re(s) > 1 region — Dirichlet partial sum converging to ζ(s)
               Color = |Σ_{n=1}^{N} n^{-s}| as N grows (increasing terms)
  Right panel: True ζ(s) via mpmath for the full strip -1 < Re(s) < 3
               Critical line, pole at s=1, and the functional equation boundary

A vertical sweep animates N (number of terms added), showing convergence on the right
and the analytic continuation "filling in" the left side.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from manifold.core.animator import AnimationConfig, BaseAnimator
from manifold.core.registry import AnimationRegistry
from manifold.math.zeta import zeta_grid, dirichlet_series_partial_sum
from manifold.math.complex_ops import domain_color_fast


@AnimationRegistry.register
class AnalyticContinuationAnimator(BaseAnimator):
    """
    Side-by-side comparison: Dirichlet series (Re > 1) vs full ζ(s).

    Shows that:
    - The Dirichlet series only converges for Re(s) > 1 (left side stays correct)
    - The analytic continuation extends ζ(s) to all s ≠ 1
    - The functional equation ζ(s) = 2^s π^{s-1} sin(πs/2) Γ(1-s) ζ(1-s) links both sides
    """

    NAME = "riemann.continuation"
    DESCRIPTION = "Analytic continuation of ζ(s) — Dirichlet series vs full zeta"

    def __init__(
        self,
        config: AnimationConfig,
        re_range: tuple[float, float] = (-1.0, 3.0),
        im_range: tuple[float, float] = (0.5, 30.0),
        resolution: int = 150,
        max_terms: int = 50,
        dps: int = 25,
    ) -> None:
        super().__init__(config)
        self.re_range = re_range
        self.im_range = im_range
        self.resolution = resolution
        self.max_terms = max_terms
        self.dps = dps

        re = np.linspace(re_range[0], re_range[1], resolution)
        im = np.linspace(im_range[0], im_range[1], resolution)
        RE, IM = np.meshgrid(re, im)
        self._S = RE + 1j * IM

    def setup(self) -> None:
        print("Computing true ζ(s) via mpmath (will be cached)...")
        RE, IM, Z_true = zeta_grid(
            re_range=self.re_range,
            im_range=self.im_range,
            re_points=self.resolution,
            im_points=self.resolution,
            dps=self.dps,
        )
        self._Z_true = Z_true.T   # shape (resolution, resolution)
        self._rgb_true = domain_color_fast(self._Z_true)

        print(f"Precomputing Dirichlet partial sums up to N={self.max_terms}...")
        self._partial_sums = []
        cumsum = np.zeros_like(self._S, dtype=complex)
        for n in range(1, self.max_terms + 1):
            with np.errstate(over="ignore", invalid="ignore"):
                cumsum = cumsum + np.power(n + 0j, -self._S)
            self._partial_sums.append(cumsum.copy())

        self.fig = plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        gs = gridspec.GridSpec(1, 2, figure=self.fig, wspace=0.3)
        self.ax_dirichlet = self.fig.add_subplot(gs[0])
        self.ax_true = self.fig.add_subplot(gs[1])
        self.axes = [self.ax_dirichlet, self.ax_true]

        extent = [self.re_range[0], self.re_range[1], self.im_range[0], self.im_range[1]]

        # --- Left: Dirichlet partial sum ---
        rgb0 = domain_color_fast(self._partial_sums[0])
        self._im_dirichlet = self.ax_dirichlet.imshow(
            rgb0, origin="lower", extent=extent, aspect="auto", interpolation="bilinear",
        )
        self.ax_dirichlet.axvline(1.0, color="red", lw=1.5, ls="--", alpha=0.7, label="Re(s)=1")
        self.ax_dirichlet.axvline(0.5, color="cyan", lw=1.0, ls="--", alpha=0.5, label="Re(s)=½")
        self.ax_dirichlet.set_title("Σ n⁻ˢ  (N terms)", color="white", fontsize=11)
        self.ax_dirichlet.set_xlabel("Re(s)", color="white")
        self.ax_dirichlet.set_ylabel("Im(s)", color="white")
        self.ax_dirichlet.legend(loc="upper right", fontsize=8, framealpha=0.3)
        self._n_text = self.ax_dirichlet.text(
            0.02, 0.97, "N = 1",
            transform=self.ax_dirichlet.transAxes,
            color="white", fontsize=11, verticalalignment="top", fontweight="bold",
        )

        # --- Right: True ζ(s) ---
        self.ax_true.imshow(
            self._rgb_true, origin="lower", extent=extent, aspect="auto",
            interpolation="bilinear",
        )
        self.ax_true.axvline(1.0, color="red", lw=1.5, ls="--", alpha=0.7, label="Pole s=1")
        self.ax_true.axvline(0.5, color="cyan", lw=1.0, ls="--", alpha=0.5, label="Critical line")
        self.ax_true.set_title("ζ(s) — Analytic continuation", color="white", fontsize=11)
        self.ax_true.set_xlabel("Re(s)", color="white")
        self.ax_true.legend(loc="upper right", fontsize=8, framealpha=0.3)

        # Convergence boundary indicator on left panel
        self._boundary = self.ax_dirichlet.axvline(
            1.0, color="yellow", lw=2.0, alpha=0.0
        )

        self.fig.suptitle(
            "Analytic Continuation of ζ(s)\n"
            "Left: Dirichlet series  |  Right: Full zeta function",
            color="white", fontsize=12, y=1.02,
        )

    def update(self, frame: int) -> list:
        n_idx = int((frame / max(self.total_frames() - 1, 1)) * (self.max_terms - 1))
        n_idx = min(n_idx, self.max_terms - 1)
        n_terms = n_idx + 1

        rgb = domain_color_fast(self._partial_sums[n_idx])
        self._im_dirichlet.set_data(rgb)
        self._n_text.set_text(f"N = {n_terms}")

        return [self._im_dirichlet, self._n_text]
