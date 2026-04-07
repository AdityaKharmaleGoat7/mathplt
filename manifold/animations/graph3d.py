"""3D surface animation: rotating f(x, y) surface."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — registers 3d projection

from manifold.core.animator import AnimationConfig, BaseAnimator
from manifold.core.equation_parser import EquationParser
from manifold.core.registry import AnimationRegistry
from manifold.config import SURFACE_CMAP


@AnimationRegistry.register
class Graph3DAnimator(BaseAnimator):
    """
    Animated 3D surface for f(x, y) with correct orbital rotation.

    The surface collection is removed and replotted every frame so that
    matplotlib recomputes polygon depth-sorting for each viewing angle —
    this is what makes the orbital rotation look correct.

    Example equations:
        sin(sqrt(x**2 + y**2))
        exp(-0.1*(x**2 + y**2)) * cos(x + y)
        sin(x) * cos(y)
        x * exp(-x**2 - y**2)
    """

    NAME = "graph3d"
    DESCRIPTION = "Rotating 3D surface f(x, y)"

    def __init__(
        self,
        config: AnimationConfig,
        equation: str = "sin(sqrt(x**2 + y**2))",
        x_range: tuple[float, float] = (-5.0, 5.0),
        y_range: tuple[float, float] = (-5.0, 5.0),
        resolution: int = 50,
        cmap: str = SURFACE_CMAP,
        azim_start: float = -60.0,
        azim_per_frame: float = 2.25,   # 360° / (20fps × 8s) = one full orbit
        elev: float = 28.0,
        alpha: float = 0.88,
    ) -> None:
        super().__init__(config)
        self.equation = equation
        self.x_range = x_range
        self.y_range = y_range
        self.resolution = resolution
        self.cmap = cmap
        self.azim_start = azim_start
        self.azim_per_frame = azim_per_frame
        self.elev = elev
        self.alpha = alpha

        parser = EquationParser()
        self._f = parser.parse_xy(equation)

        x = np.linspace(x_range[0], x_range[1], resolution)
        y = np.linspace(y_range[0], y_range[1], resolution)
        self.X, self.Y = np.meshgrid(x, y)
        self.Z = self._f(self.X, self.Y)
        self._z_min = float(np.nanmin(self.Z))
        self._z_max = float(np.nanmax(self.Z))

        # Set in setup(); kept as instance var so update() can call .remove()
        self._surf = None
        self._cbar = None

    def setup(self) -> None:
        bg = "#0d0d0d" if self.config.dark_mode else "white"
        lc = "white" if self.config.dark_mode else "black"

        self.fig = plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        self.fig.patch.set_facecolor(bg)

        ax = self.fig.add_subplot(111, projection="3d")
        ax.set_facecolor(bg)
        self.axes = [ax]

        ax.set_title(f"$f(x,y) = {self.equation}$", color=lc, pad=12, fontsize=12)
        ax.set_xlabel("x", color=lc, labelpad=8)
        ax.set_ylabel("y", color=lc, labelpad=8)
        ax.set_zlabel("f(x, y)", color=lc, labelpad=8)
        ax.tick_params(colors=lc)
        ax.set_zlim(self._z_min, self._z_max)
        ax.view_init(elev=self.elev, azim=self.azim_start)

        self._surf = ax.plot_surface(
            self.X, self.Y, self.Z,
            cmap=self.cmap, alpha=self.alpha,
            linewidth=0, antialiased=True,
            vmin=self._z_min, vmax=self._z_max,
        )
        self._cbar = self.fig.colorbar(
            self._surf, ax=ax, shrink=0.45, pad=0.1, aspect=20
        )
        self._cbar.ax.tick_params(colors=lc)
        plt.setp(self._cbar.ax.yaxis.get_ticklabels(), color=lc)
        self.fig.tight_layout(pad=1.5)

    def update(self, frame: int) -> list:
        ax = self.axes[0]
        azim = self.azim_start + frame * self.azim_per_frame

        # ── Remove old surface and replot ──────────────────────────────────
        # Must remove and re-add every frame: plot_surface re-sorts polygon
        # depth for the current viewpoint, which is what makes the orbital
        # rotation look correct (without this, back-faces bleed through).
        self._surf.remove()
        self._surf = ax.plot_surface(
            self.X, self.Y, self.Z,
            cmap=self.cmap, alpha=self.alpha,
            linewidth=0, antialiased=True,
            vmin=self._z_min, vmax=self._z_max,
        )

        # Keep colorbar mappable in sync with the new surface
        self._cbar.update_normal(self._surf)

        # Lock z-axis so it doesn't rescale after replot
        ax.set_zlim(self._z_min, self._z_max)
        ax.view_init(elev=self.elev, azim=azim)
        return []

    def build(self):
        """Override to disable blit — 3D rotation requires full redraws."""
        self.setup()
        if self.config.title and self.fig is not None:
            lc = "white" if self.config.dark_mode else "black"
            self.fig.suptitle(self.config.title, color=lc)

        import matplotlib.animation as animation
        self._anim = animation.FuncAnimation(
            self.fig,
            self.update,
            frames=self.total_frames(),
            interval=1000 // self.config.fps,
            blit=False,
        )
        return self._anim
