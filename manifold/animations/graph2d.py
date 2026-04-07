"""2D animated graph: f(x, t) where t advances each frame."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from manifold.core.animator import AnimationConfig, BaseAnimator
from manifold.core.equation_parser import EquationParser
from manifold.core.registry import AnimationRegistry
from manifold.math.numerics import auto_ylim
from manifold.config import ACCENT_BLUE, GRID_ALPHA


@AnimationRegistry.register
class Graph2DAnimator(BaseAnimator):
    """
    Animated 2D curve for any equation f(x, t).

    The variable 'x' is the spatial axis; 't' advances with each frame.
    Example equations:
        sin(x + t)
        sin(x + t) * exp(-0.1 * x**2)
        cos(3*x - 2*t) + 0.5 * sin(5*x + t)
        x**2 * sin(t) - x * cos(t)
    """

    NAME = "graph2d"
    DESCRIPTION = "Animated 2D curve f(x, t) — equation input via EquationWidget"

    def __init__(
        self,
        config: AnimationConfig,
        equation: str = "sin(x + t)",
        x_range: tuple[float, float] = (-10.0, 10.0),
        y_range: tuple[float, float] | None = None,
        resolution: int = 800,
        color: str = ACCENT_BLUE,
        show_zero_line: bool = True,
    ) -> None:
        super().__init__(config)
        self.equation = equation
        self.x_range = x_range
        self.y_range = y_range   # None → auto-scale per frame
        self.resolution = resolution
        self.color = color
        self.show_zero_line = show_zero_line

        parser = EquationParser()
        self._f = parser.parse_xt(equation)
        self.x = np.linspace(x_range[0], x_range[1], resolution)

    def setup(self) -> None:
        self.fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)
        self.axes = [ax]

        ax.set_xlim(self.x_range[0], self.x_range[1])
        ax.set_xlabel("x", color="white")
        ax.set_ylabel("f(x, t)", color="white")
        ax.set_title(f"f(x, t) = {self.equation}", color="white", pad=10)
        ax.grid(True, alpha=GRID_ALPHA)

        if self.show_zero_line:
            ax.axhline(0, color="gray", linewidth=0.6, alpha=0.5)

        # Initial y-limits
        if self.y_range is not None:
            ax.set_ylim(self.y_range[0], self.y_range[1])
        else:
            y0 = self._f(self.x, 0.0)
            ax.set_ylim(*auto_ylim(y0))

        self._line, = ax.plot([], [], lw=2, color=self.color)
        self._time_text = ax.text(
            0.02, 0.95, "t = 0.00",
            transform=ax.transAxes,
            color="white", fontsize=10,
        )

    def update(self, frame: int) -> list:
        t = frame / self.config.fps
        y = self._f(self.x, t)

        self._line.set_data(self.x, y)
        if self.y_range is None:
            self.axes[0].set_ylim(*auto_ylim(y))
        self._time_text.set_text(f"t = {t:.2f}")

        return [self._line, self._time_text]
