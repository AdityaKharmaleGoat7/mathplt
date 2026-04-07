"""
Riemann Zeros Animation.

Two-panel animation showing:
  Left:  Path of ζ(1/2 + it) in the complex output plane.
         The path crosses the origin at each nontrivial zero.
  Right: |ζ(1/2 + it)| vs t, with dashed lines at known zeros.

A cursor advances in real time across both panels.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from manifold.core.animator import AnimationConfig, BaseAnimator
from manifold.core.registry import AnimationRegistry
from manifold.math.zeta import find_zeros_on_critical_line, zeta_on_critical_line
from manifold.config import ACCENT_BLUE, ACCENT_ORANGE, ACCENT_GREEN


@AnimationRegistry.register
class RiemannZerosAnimator(BaseAnimator):
    """
    Animate zeros of ζ(s) along the critical line Re(s) = 1/2.

    Precomputes ζ(1/2 + it) for t in [t_min, t_max] at setup time (cached).
    Animation sweeps t forward and reveals the path in the complex plane.
    """

    NAME = "riemann.zeros"
    DESCRIPTION = "Zeros of ζ(s) on the critical line — path in ℂ + |ζ| vs t"

    def __init__(
        self,
        config: AnimationConfig,
        t_min: float = 0.5,
        t_max: float = 50.0,
        n_zeros: int = 15,
        resolution: int = 2000,
        dps: int = 25,
    ) -> None:
        super().__init__(config)
        self.t_min = t_min
        self.t_max = t_max
        self.n_zeros = n_zeros
        self.resolution = resolution
        self.dps = dps

        self.t_values = np.linspace(t_min, t_max, resolution)

    def setup(self) -> None:
        print("Precomputing ζ(1/2 + it) values (will be cached after first run)...")
        self._zeta_vals = zeta_on_critical_line(self.t_values, dps=self.dps)
        print("Finding nontrivial zeros...")
        self._zeros = find_zeros_on_critical_line(n_zeros=self.n_zeros)
        zero_t_values = [z.imag for z in self._zeros]
        print(f"Found {len(self._zeros)} zeros. First few t-values: "
              f"{[f'{t:.3f}' for t in zero_t_values[:5]]}")

        self.fig = plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        gs = gridspec.GridSpec(1, 2, figure=self.fig, wspace=0.35)
        ax_path = self.fig.add_subplot(gs[0])
        ax_mod = self.fig.add_subplot(gs[1])
        self.axes = [ax_path, ax_mod]

        # --- Left panel: ζ path in complex output plane ---
        ax_path.set_title("ζ(½ + it)  in  ℂ", color="white", fontsize=12)
        ax_path.set_xlabel("Re(ζ)", color="white")
        ax_path.set_ylabel("Im(ζ)", color="white")
        ax_path.axhline(0, color="gray", lw=0.5, alpha=0.6)
        ax_path.axvline(0, color="gray", lw=0.5, alpha=0.6)

        # Plot origin marker (zeros of zeta appear here)
        ax_path.plot(0, 0, "w+", ms=12, markeredgewidth=1.5, alpha=0.5, label="Origin (zeros)")

        # Full faint path (static background)
        ax_path.plot(
            self._zeta_vals.real, self._zeta_vals.imag,
            color=ACCENT_BLUE, alpha=0.15, lw=0.8,
        )

        # Set equal aspect with some padding
        r_max = max(np.abs(self._zeta_vals).max() * 1.1, 1.0)
        ax_path.set_xlim(-r_max, r_max)
        ax_path.set_ylim(-r_max, r_max)
        ax_path.set_aspect("equal")

        # Animated path (revealed progressively)
        self._path_line, = ax_path.plot([], [], color=ACCENT_BLUE, lw=1.5, alpha=0.9)
        self._cursor_dot, = ax_path.plot([], [], "o", color=ACCENT_ORANGE, ms=7, zorder=5)

        ax_path.legend(loc="upper right", fontsize=7)

        # --- Right panel: |ζ| vs t ---
        ax_mod.set_title("|ζ(½ + it)|  vs  t", color="white", fontsize=12)
        ax_mod.set_xlabel("t  (Im part of s)", color="white")
        ax_mod.set_ylabel("|ζ(s)|", color="white")

        mod_vals = np.abs(self._zeta_vals)
        ax_mod.plot(self.t_values, mod_vals, color=ACCENT_BLUE, lw=1.0, alpha=0.9)
        ax_mod.axhline(0, color="gray", lw=0.5, alpha=0.5)
        ax_mod.set_xlim(self.t_min, self.t_max)
        ax_mod.set_ylim(-0.2, mod_vals.max() * 1.1)

        # Mark known zeros with dashed verticals
        for z in self._zeros:
            ax_mod.axvline(
                z.imag, color="red", alpha=0.45, lw=0.9, ls="--"
            )
            ax_mod.text(
                z.imag, mod_vals.max() * 1.05, f"{z.imag:.2f}",
                color="red", fontsize=6, ha="center", va="bottom",
                rotation=90,
            )

        # Animated vertical cursor
        self._vline = ax_mod.axvline(self.t_min, color=ACCENT_ORANGE, lw=1.5, alpha=0.9)
        self._t_text = ax_mod.text(
            0.02, 0.95, f"t = {self.t_min:.2f}",
            transform=ax_mod.transAxes, color="white", fontsize=10,
        )

        self.fig.suptitle(
            "Riemann Zeta Function — Critical Line  Re(s) = ½",
            color="white", fontsize=13, y=1.01,
        )

    def update(self, frame: int) -> list:
        # Map frame → index in precomputed array
        idx = int((frame / max(self.total_frames() - 1, 1)) * (len(self.t_values) - 1))
        idx = min(idx, len(self.t_values) - 1)

        # Reveal path up to current index
        self._path_line.set_data(
            self._zeta_vals[:idx + 1].real,
            self._zeta_vals[:idx + 1].imag,
        )
        self._cursor_dot.set_data(
            [self._zeta_vals[idx].real],
            [self._zeta_vals[idx].imag],
        )

        t_current = self.t_values[idx]
        self._vline.set_xdata([t_current])
        self._t_text.set_text(f"t = {t_current:.2f}")

        return [self._path_line, self._cursor_dot, self._vline, self._t_text]
