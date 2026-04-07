"""
Critical Strip Animation.

Two-panel heatmap of the Riemann zeta function over the critical strip
0 < Re(s) < 1, animated with a horizontal scan line sweeping Im(s).

Left panel:  log(1 + |ζ(s)|) — magnitude (inferno colormap)
Right panel: arg(ζ(s))       — phase (HSV colormap)

A cyan dashed line marks the critical line Re(s) = 1/2.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D

from manifold.core.animator import AnimationConfig, BaseAnimator
from manifold.core.registry import AnimationRegistry
from manifold.math.zeta import zeta_grid
from manifold.config import MAGNITUDE_CMAP, PHASE_CMAP


@AnimationRegistry.register
class CriticalStripAnimator(BaseAnimator):
    """
    Heatmap of ζ(s) over the critical strip 0 < Re(s) < 1, with animated scan.

    Grid is precomputed and cached. The scan line reveals Im(s) position.
    Zeros of ζ(s) appear as dark spots on the critical line in the magnitude panel.
    """

    NAME = "riemann.critical_strip"
    DESCRIPTION = "Magnitude + phase heatmap of ζ(s) over the critical strip"

    def __init__(
        self,
        config: AnimationConfig,
        im_range: tuple[float, float] = (0.5, 50.0),
        re_points: int = 60,
        im_points: int = 250,
        dps: int = 25,
    ) -> None:
        super().__init__(config)
        self.im_range = im_range
        self.re_points = re_points
        self.im_points = im_points
        self.dps = dps

    def setup(self) -> None:
        print("Computing ζ(s) grid over critical strip (will be cached)...")
        RE, IM, Z = zeta_grid(
            re_range=(0.02, 0.98),
            im_range=self.im_range,
            re_points=self.re_points,
            im_points=self.im_points,
            dps=self.dps,
        )
        # RE, IM, Z have shape (re_points, im_points); transpose for imshow (y=im, x=re)
        RE_t = RE.T    # (im_points, re_points)
        IM_t = IM.T
        Z_t = Z.T

        mag = np.log1p(np.abs(Z_t))
        phase = np.angle(Z_t)

        self.fig = plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        gs = gridspec.GridSpec(1, 2, figure=self.fig, wspace=0.3)
        ax_mag = self.fig.add_subplot(gs[0])
        ax_phase = self.fig.add_subplot(gs[1], sharey=ax_mag)
        self.axes = [ax_mag, ax_phase]

        extent = [0.02, 0.98, self.im_range[0], self.im_range[1]]

        # --- Magnitude panel ---
        ax_mag.imshow(
            mag, origin="lower", extent=extent, aspect="auto",
            cmap=MAGNITUDE_CMAP, interpolation="bilinear",
            vmin=0, vmax=np.percentile(mag, 98),
        )
        ax_mag.axvline(0.5, color="cyan", lw=1.2, ls="--", alpha=0.8, label="Re(s)=½")
        ax_mag.set_title("log(1 + |ζ(s)|)", color="white", fontsize=11)
        ax_mag.set_xlabel("Re(s)", color="white")
        ax_mag.set_ylabel("Im(s)", color="white")
        ax_mag.legend(loc="upper right", fontsize=8, framealpha=0.3)

        # --- Phase panel ---
        ax_phase.imshow(
            phase, origin="lower", extent=extent, aspect="auto",
            cmap=PHASE_CMAP, interpolation="bilinear",
            vmin=-np.pi, vmax=np.pi,
        )
        ax_phase.axvline(0.5, color="white", lw=1.2, ls="--", alpha=0.7)
        ax_phase.set_title("arg(ζ(s))  [phase]", color="white", fontsize=11)
        ax_phase.set_xlabel("Re(s)", color="white")

        # --- Animated horizontal scan lines ---
        y0 = self.im_range[0]
        self._scan_mag = ax_mag.axhline(y0, color="lime", lw=1.5, alpha=0.85)
        self._scan_phase = ax_phase.axhline(y0, color="lime", lw=1.5, alpha=0.85)
        self._t_text = ax_mag.text(
            0.02, 0.97, f"Im(s) = {y0:.2f}",
            transform=ax_mag.transAxes, color="white", fontsize=9,
            verticalalignment="top",
        )

        self.fig.suptitle(
            "Riemann ζ(s) over the Critical Strip  0 < Re(s) < 1",
            color="white", fontsize=13, y=1.01,
        )

    def update(self, frame: int) -> list:
        frac = frame / max(self.total_frames() - 1, 1)
        im_s = self.im_range[0] + frac * (self.im_range[1] - self.im_range[0])

        self._scan_mag.set_ydata([im_s])
        self._scan_phase.set_ydata([im_s])
        self._t_text.set_text(f"Im(s) = {im_s:.2f}")

        return [self._scan_mag, self._scan_phase, self._t_text]
