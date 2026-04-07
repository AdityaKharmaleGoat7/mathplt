"""Domain coloring animation for complex functions f(z)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from manifold.core.animator import AnimationConfig, BaseAnimator
from manifold.core.equation_parser import EquationParser
from manifold.core.registry import AnimationRegistry
from manifold.math.complex_ops import complex_grid, domain_color_fast


@AnimationRegistry.register
class ComplexPlaneAnimator(BaseAnimator):
    """
    Domain coloring visualization of a complex function f(z).

    Hue encodes arg(f(z)), brightness encodes |f(z)|.
    If the equation includes 't', it animates over time.

    Example equations (use variable 'z'):
        z**2
        z**3 - 1
        (z**2 - 1) / (z**2 + 1)
        sin(z)
        exp(z)
    """

    NAME = "complex"
    DESCRIPTION = "Domain coloring of f(z) — hue=arg, brightness=|z|"

    def __init__(
        self,
        config: AnimationConfig,
        equation: str = "z**2 - 1",
        re_range: tuple[float, float] = (-3.0, 3.0),
        im_range: tuple[float, float] = (-3.0, 3.0),
        resolution: int = 300,
        brightness_cycles: float = 1.0,
    ) -> None:
        super().__init__(config)
        self.equation = equation
        self.re_range = re_range
        self.im_range = im_range
        self.resolution = resolution
        self.brightness_cycles = brightness_cycles

        self._Z = complex_grid(re_range, im_range, re_n=resolution, im_n=resolution)

        # Try parsing as static f(z); if 't' appears we'll animate
        parser = EquationParser()
        self._has_t = "t" in equation
        if self._has_t:
            # Parse as f(z, t) — needs special handling since parse_complex only knows z
            from manifold.core.equation_parser import ALLOWED_NAMES, _validate_ast
            _validate_ast(equation, extra_vars={"z", "t"})
            ns = dict(ALLOWED_NAMES)
            code = compile(equation, "<equation>", "eval")
            def _f(z, t):
                local = dict(ns, z=z, t=t)
                return eval(code, {"__builtins__": {}}, local)
            self._f = _f
        else:
            self._f = parser.parse_complex(equation)

    def setup(self) -> None:
        self.fig, ax = plt.subplots(figsize=self.config.figsize, dpi=self.config.dpi)
        self.axes = [ax]

        ax.set_title(f"f(z) = {self.equation}", color="white", pad=10)
        ax.set_xlabel("Re(z)")
        ax.set_ylabel("Im(z)")
        ax.axhline(0, color="white", lw=0.3, alpha=0.4)
        ax.axvline(0, color="white", lw=0.3, alpha=0.4)

        # Initial image — mask infinities from poles
        w = self._f(self._Z, 0.0) if self._has_t else self._f(self._Z)
        w = np.where(np.isfinite(w), w, np.nan + 0j)
        rgb = domain_color_fast(w, brightness_cycles=self.brightness_cycles)

        extent = [self.re_range[0], self.re_range[1], self.im_range[0], self.im_range[1]]
        self._im = ax.imshow(
            rgb, origin="lower", extent=extent, aspect="equal", interpolation="bilinear"
        )
        self._time_text = ax.text(
            0.02, 0.97, "t = 0.00" if self._has_t else "",
            transform=ax.transAxes, color="white", fontsize=9,
            verticalalignment="top",
        )

    def update(self, frame: int) -> list:
        t = frame / self.config.fps
        w = self._f(self._Z, t) if self._has_t else self._f(self._Z)
        w = np.where(np.isfinite(w), w, np.nan + 0j)
        rgb = domain_color_fast(w, brightness_cycles=self.brightness_cycles)
        self._im.set_data(rgb)
        if self._has_t:
            self._time_text.set_text(f"t = {t:.2f}")
        return [self._im, self._time_text]
