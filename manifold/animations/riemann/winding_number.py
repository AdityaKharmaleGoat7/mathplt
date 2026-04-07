"""
Winding Number / Argument Principle Animation.

Visualizes the argument principle for the Riemann zeta function:
  N(zeros inside C) = (1/2πi) ∮_C ζ'(s)/ζ(s) ds

As a rectangular contour C expands upward in the s-plane (enclosing more of
the critical strip), the image ζ(C) in the w-plane winds around the origin
once per enclosed zero.

Left panel:  Contour C in the s-plane (expanding upward)
Right panel: Image ζ(C) in the w-plane (winding around origin)
Text: Current winding number = number of zeros enclosed
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch

from manifold.core.animator import AnimationConfig, BaseAnimator
from manifold.core.registry import AnimationRegistry
from manifold.math.zeta import zeta_on_contour, find_zeros_on_critical_line
from manifold.config import ACCENT_BLUE, ACCENT_ORANGE, ACCENT_GREEN


def _build_contour(re_lo: float, re_hi: float, im_top: float, n: int = 200) -> np.ndarray:
    """Build closed rectangular contour in s-plane. Returns 1D complex ndarray."""
    n_side = n // 4
    bottom = np.linspace(re_lo, re_hi, n_side) + 0.5j    # bottom at Im=0.5 (avoid pole)
    right  = re_hi + 1j * np.linspace(0.5, im_top, n_side)
    top    = np.linspace(re_hi, re_lo, n_side) + 1j * im_top
    left   = re_lo + 1j * np.linspace(im_top, 0.5, n_side)
    return np.concatenate([bottom, right, top, left, [bottom[0]]])


@AnimationRegistry.register
class WindingNumberAnimator(BaseAnimator):
    """
    Argument principle: as a contour expands in the s-plane, ζ(C) winds around origin.

    Each winding = one zero of ζ(s) enclosed by the contour.
    This directly visualizes why zeros on the critical line matter.
    """

    NAME = "riemann.winding"
    DESCRIPTION = "Argument principle — ζ(C) winding count equals zeros enclosed"

    def __init__(
        self,
        config: AnimationConfig,
        re_lo: float = 0.1,
        re_hi: float = 0.9,
        im_max: float = 40.0,
        im_start: float = 5.0,
        n_contour: int = 300,
        n_zeros: int = 12,
        dps: int = 25,
    ) -> None:
        super().__init__(config)
        self.re_lo = re_lo
        self.re_hi = re_hi
        self.im_max = im_max
        self.im_start = im_start
        self.n_contour = n_contour
        self.n_zeros = n_zeros
        self.dps = dps

    def setup(self) -> None:
        print("Finding zeros on critical line...")
        self._zeros = find_zeros_on_critical_line(n_zeros=self.n_zeros, dps=50)
        self._zero_t = sorted([z.imag for z in self._zeros])

        # Precompute ζ values along the maximum contour (then sub-sample each frame)
        print("Precomputing ζ values along maximum contour...")
        self._max_contour = _build_contour(
            self.re_lo, self.re_hi, self.im_max, n=self.n_contour
        )
        self._max_w = zeta_on_contour(self._max_contour, dps=self.dps)

        self.fig = plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        gs = gridspec.GridSpec(1, 2, figure=self.fig, wspace=0.35)
        self.ax_s = self.fig.add_subplot(gs[0])
        self.ax_w = self.fig.add_subplot(gs[1])
        self.axes = [self.ax_s, self.ax_w]

        # --- s-plane (left) ---
        self.ax_s.set_title("s-plane  (expanding contour)", color="white", fontsize=11)
        self.ax_s.set_xlabel("Re(s)", color="white")
        self.ax_s.set_ylabel("Im(s)", color="white")
        self.ax_s.axvline(0.5, color="cyan", lw=1.0, ls="--", alpha=0.5, label="Re(s)=½")
        self.ax_s.set_xlim(-0.1, 1.1)
        self.ax_s.set_ylim(0, self.im_max * 1.05)

        # Mark all zeros in s-plane
        for t in self._zero_t:
            self.ax_s.plot(0.5, t, "r+", ms=8, markeredgewidth=1.5, alpha=0.7)

        self.ax_s.legend(loc="upper right", fontsize=8, framealpha=0.3)

        # Animated contour in s-plane (4 sides)
        self._contour_line, = self.ax_s.plot([], [], color=ACCENT_ORANGE, lw=2.0)

        # Highlight enclosed zeros count
        self._s_text = self.ax_s.text(
            0.02, 0.95, "", transform=self.ax_s.transAxes,
            color="white", fontsize=10, verticalalignment="top",
        )

        # --- w-plane (right) ---
        w_range = max(np.abs(self._max_w[np.isfinite(self._max_w)]).max() * 1.2, 2.0)
        self.ax_w.set_title("w-plane  ζ(C)  (winding around origin)", color="white", fontsize=11)
        self.ax_w.set_xlabel("Re(ζ)", color="white")
        self.ax_w.set_ylabel("Im(ζ)", color="white")
        self.ax_w.axhline(0, color="gray", lw=0.4, alpha=0.5)
        self.ax_w.axvline(0, color="gray", lw=0.4, alpha=0.5)
        self.ax_w.plot(0, 0, "w+", ms=14, markeredgewidth=2, zorder=5, label="Origin (zeros)")
        self.ax_w.set_xlim(-w_range, w_range)
        self.ax_w.set_ylim(-w_range, w_range)
        self.ax_w.set_aspect("equal")
        self.ax_w.legend(loc="upper right", fontsize=8, framealpha=0.3)

        self._w_line, = self.ax_w.plot([], [], color=ACCENT_ORANGE, lw=2.0)
        self._w_dot, = self.ax_w.plot([], [], "o", color=ACCENT_GREEN, ms=7, zorder=6)
        self._w_text = self.ax_w.text(
            0.02, 0.95, "Winding ≈ 0",
            transform=self.ax_w.transAxes, color="white", fontsize=11,
            verticalalignment="top", fontweight="bold",
        )

        self.fig.suptitle(
            "Argument Principle — Zeros of ζ(s)",
            color="white", fontsize=13, y=1.01,
        )

    def _count_zeros_below(self, im_top: float) -> int:
        """Count known zeros with Im(t) < im_top."""
        return sum(1 for t in self._zero_t if t < im_top)

    def update(self, frame: int) -> list:
        frac = frame / max(self.total_frames() - 1, 1)
        im_top = self.im_start + frac * (self.im_max - self.im_start)

        # Build current contour
        contour = _build_contour(self.re_lo, self.re_hi, im_top, n=self.n_contour)
        self._contour_line.set_data(contour.real, contour.imag)

        # Compute winding number via angle accumulation on precomputed max contour
        # (recompute only up to current im_top fraction)
        idx = int(frac * len(self._max_w))
        w_slice = self._max_w[:idx + 1] if idx > 0 else self._max_w[:2]
        finite = w_slice[np.isfinite(w_slice)]
        if len(finite) > 2:
            angles = np.angle(finite)
            total = float(np.sum(np.diff(np.unwrap(angles))))
            winding = total / (2 * np.pi)
        else:
            winding = 0.0

        n_zeros = self._count_zeros_below(im_top)

        self._contour_line.set_data(contour.real, contour.imag)
        self._s_text.set_text(
            f"Im_top = {im_top:.1f}\nZeros enclosed: {n_zeros}"
        )

        self._w_line.set_data(finite.real, finite.imag)
        if len(finite) > 0:
            self._w_dot.set_data([finite[-1].real], [finite[-1].imag])
        self._w_text.set_text(f"Winding ≈ {winding:.1f}\n(= {n_zeros} zeros)")

        return [
            self._contour_line, self._s_text,
            self._w_line, self._w_dot, self._w_text,
        ]
