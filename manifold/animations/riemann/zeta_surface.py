"""
Zeta Surface Animation.

Domain coloring of ζ(s) over the complex plane, showing the full analytic structure:
- Pole at s = 1 (bright singularity)
- Trivial zeros at s = -2, -4, -6, ...
- Nontrivial zeros on the critical line Re(s) = 1/2

Animates as a slow pan/zoom into the critical strip, or as a static domain coloring.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from manifold.core.animator import AnimationConfig, BaseAnimator
from manifold.core.registry import AnimationRegistry
from manifold.math.complex_ops import domain_color_fast
from manifold.math.zeta import find_zeros_on_critical_line


@AnimationRegistry.register
class ZetaSurfaceAnimator(BaseAnimator):
    """
    Domain coloring of ζ(s) over a region of the complex plane.

    Hue encodes arg(ζ(s)), brightness encodes |ζ(s)|.
    A slow zoom animation focuses on the critical strip to reveal zeros.
    """

    NAME = "riemann.zeta_surface"
    DESCRIPTION = "Domain coloring of ζ(s) — full complex plane view"

    def __init__(
        self,
        config: AnimationConfig,
        re_range: tuple[float, float] = (-2.0, 2.0),
        im_range: tuple[float, float] = (0.0, 35.0),
        resolution: int = 200,
        dps: int = 25,
        n_zeros_marked: int = 8,
        animate_zoom: bool = False,
    ) -> None:
        super().__init__(config)
        self.re_range = re_range
        self.im_range = im_range
        self.resolution = resolution
        self.dps = dps
        self.n_zeros_marked = n_zeros_marked
        self.animate_zoom = animate_zoom

    def _compute_domain_color(
        self,
        re_range: tuple[float, float],
        im_range: tuple[float, float],
    ) -> np.ndarray:
        """Compute ζ(s) on a grid and return domain-colored RGB image."""
        from manifold.math.zeta_fast import zeta_array

        re = np.linspace(re_range[0], re_range[1], self.resolution)
        im = np.linspace(im_range[0], im_range[1], self.resolution)
        RE, IM = np.meshgrid(re, im)
        W = zeta_array(RE + 1j * IM)

        return domain_color_fast(W)

    def setup(self) -> None:
        print("Computing ζ(s) domain coloring (will be cached)...")
        # Cache the RGB image
        import hashlib, os
        from pathlib import Path
        from manifold.config import CACHE_DIR
        key = hashlib.md5(
            f"zeta_dc_{self.re_range}_{self.im_range}_{self.resolution}_{self.dps}".encode()
        ).hexdigest()[:16]
        cache = Path(CACHE_DIR) / f"{key}.npy"
        os.makedirs(CACHE_DIR, exist_ok=True)

        if cache.exists():
            self._rgb = np.load(str(cache))
        else:
            self._rgb = self._compute_domain_color(self.re_range, self.im_range)
            np.save(str(cache), self._rgb)

        print("Finding zeros to annotate...")
        zeros = find_zeros_on_critical_line(n_zeros=self.n_zeros_marked, dps=50)

        self.fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)
        self.axes = [ax]

        extent = [self.re_range[0], self.re_range[1], self.im_range[0], self.im_range[1]]
        self._im = ax.imshow(
            self._rgb, origin="lower", extent=extent, aspect="auto",
            interpolation="bilinear",
        )

        # Critical line
        ax.axvline(0.5, color="white", lw=1.0, ls="--", alpha=0.6, label="Critical line")
        # Re(s) = 1 boundary
        ax.axvline(1.0, color="yellow", lw=0.8, ls=":", alpha=0.5, label="Re(s) = 1")

        # Mark nontrivial zeros
        for z in zeros:
            if self.im_range[0] <= z.imag <= self.im_range[1]:
                ax.plot(0.5, z.imag, "wo", ms=5, alpha=0.8, zorder=5)
                ax.text(0.52, z.imag, f"t={z.imag:.2f}", color="white",
                        fontsize=6, va="center", alpha=0.7)

        ax.set_title("ζ(s) — Domain Coloring (hue = arg, brightness = |ζ|)", color="white")
        ax.set_xlabel("Re(s)", color="white")
        ax.set_ylabel("Im(s)", color="white")
        ax.legend(loc="upper right", fontsize=8, framealpha=0.3)

        if self.animate_zoom:
            # Start from wide view, zoom into critical strip
            self._zoom_re = list(self.re_range)
            self._zoom_im = list(self.im_range)
            self._target_re = (-0.5, 1.5)
            self._target_im = (10.0, 35.0)

        self._frame_text = ax.text(
            0.02, 0.97, "", transform=ax.transAxes,
            color="white", fontsize=9, verticalalignment="top",
        )

    def update(self, frame: int) -> list:
        if not self.animate_zoom:
            # Static image, no animation needed — just a slow rotation label
            t = frame / self.config.fps
            self._frame_text.set_text(f"t = {t:.1f}s")
            return [self._frame_text]

        # Animate zoom into critical strip
        frac = frame / max(self.total_frames() - 1, 1)
        re_lo = self.re_range[0] + frac * (self._target_re[0] - self.re_range[0])
        re_hi = self.re_range[1] + frac * (self._target_re[1] - self.re_range[1])
        im_lo = self.im_range[0] + frac * (self._target_im[0] - self.im_range[0])
        im_hi = self.im_range[1] + frac * (self._target_im[1] - self.im_range[1])

        self.axes[0].set_xlim(re_lo, re_hi)
        self.axes[0].set_ylim(im_lo, im_hi)
        self._frame_text.set_text(f"Zooming into critical strip...")
        return [self._frame_text]
