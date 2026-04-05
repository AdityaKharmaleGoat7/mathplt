"""3D surface animation: rotating f(x, y) surface."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — registers 3d projection

from mathplt.core.animator import AnimationConfig, BaseAnimator
from mathplt.core.equation_parser import EquationParser
from mathplt.core.registry import AnimationRegistry
from mathplt.config import SURFACE_CMAP


@AnimationRegistry.register
class Graph3DAnimator(BaseAnimator):
    """
    Animated 3D surface for f(x, y).

    Redraws the surface each frame so polygon depth-sorting is correct for
    every viewing angle — this is what makes the rotation look right.

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
        azim_per_frame: float = 1.5,
        elev_mean: float = 28.0,
        elev_amplitude: float = 8.0,   # elevation gently bobs ±amplitude degrees
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
        self.elev_mean = elev_mean
        self.elev_amplitude = elev_amplitude
        self.alpha = alpha

        parser = EquationParser()
        self._f = parser.parse_xy(equation)

        x = np.linspace(x_range[0], x_range[1], resolution)
        y = np.linspace(y_range[0], y_range[1], resolution)
        self.X, self.Y = np.meshgrid(x, y)
        self.Z = self._f(self.X, self.Y)
        self._z_min = float(np.nanmin(self.Z))
        self._z_max = float(np.nanmax(self.Z))

    def setup(self) -> None:
        self.fig = plt.figure(figsize=self.config.figsize, dpi=self.config.dpi)
        self.fig.patch.set_facecolor("#0d0d0d" if self.config.dark_mode else "white")

        ax = self.fig.add_subplot(111, projection="3d")
        ax.set_facecolor("#0d0d0d" if self.config.dark_mode else "white")
        self.axes = [ax]

        label_color = "white" if self.config.dark_mode else "black"
        ax.set_title(f"$f(x,y) = {self.equation}$", color=label_color, pad=12, fontsize=13)
        ax.set_xlabel("x", color=label_color, labelpad=8)
        ax.set_ylabel("y", color=label_color, labelpad=8)
        ax.set_zlabel("f(x, y)", color=label_color, labelpad=8)

        # Tick color
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.label.set_color(label_color)
            axis._axinfo["tick"]["color"] = label_color

        ax.tick_params(colors=label_color)
        ax.set_zlim(self._z_min, self._z_max)
        ax.view_init(elev=self.elev_mean, azim=self.azim_start)

        # Draw initial surface so colorbar is available
        self._surf = ax.plot_surface(
            self.X, self.Y, self.Z,
            cmap=self.cmap, alpha=self.alpha,
            linewidth=0, antialiased=True,
            vmin=self._z_min, vmax=self._z_max,
        )
        cbar = self.fig.colorbar(self._surf, ax=ax, shrink=0.45, pad=0.1, aspect=20)
        cbar.ax.yaxis.set_tick_params(color=label_color)
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color=label_color)

        self.fig.tight_layout(pad=1.5)

    def _redraw_surface(self, ax) -> None:
        """Remove existing surface collection and replot with current cmap/alpha.

        This is required so matplotlib recomputes polygon depth order for the
        new viewing angle — without it, faces render in the wrong z-order as
        the surface rotates.
        """
        # Remove old surface (always the last PathCollection added)
        if ax.collections:
            ax.collections[-1].remove()

        ax.plot_surface(
            self.X, self.Y, self.Z,
            cmap=self.cmap, alpha=self.alpha,
            linewidth=0, antialiased=True,
            vmin=self._z_min, vmax=self._z_max,
        )

    def update(self, frame: int) -> list:
        ax = self.axes[0]

        azim = self.azim_start + frame * self.azim_per_frame
        # Gentle elevation bob so the surface looks dynamic from different heights
        total_frames = self.total_frames()
        elev = self.elev_mean + self.elev_amplitude * np.sin(
            2 * np.pi * frame / max(total_frames, 1)
        )

        self._redraw_surface(ax)
        ax.view_init(elev=elev, azim=azim)
        return []

    def build(self):
        """Override to disable blit — 3D rotation requires full redraws."""
        self.setup()
        if self.config.title and self.fig is not None:
            color = "white" if self.config.dark_mode else "black"
            self.fig.suptitle(self.config.title, color=color)

        import matplotlib.animation as animation
        self._anim = animation.FuncAnimation(
            self.fig,
            self.update,
            frames=self.total_frames(),
            interval=1000 // self.config.fps,
            blit=False,
        )
        return self._anim
