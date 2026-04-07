"""Grid generation and numeric helper utilities."""

from __future__ import annotations

from typing import Callable

import numpy as np


def linspace_grid(
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    nx: int = 200,
    ny: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    """Return meshgrid arrays (X, Y) over the given ranges."""
    x = np.linspace(x_range[0], x_range[1], nx)
    y = np.linspace(y_range[0], y_range[1], ny)
    return np.meshgrid(x, y)


def make_xt_function(expression: str) -> Callable[[np.ndarray, float], np.ndarray]:
    """
    Compile an equation string referencing 'x' and 't' into a callable f(x, t).
    This is a thin wrapper for convenience; full validation happens in EquationParser.
    """
    from manifold.core.equation_parser import EquationParser
    return EquationParser().parse_xt(expression)


def auto_ylim(
    y: np.ndarray, margin_frac: float = 0.1, min_span: float = 0.5
) -> tuple[float, float]:
    """Compute y-axis limits with a percentage margin, handling NaN/Inf gracefully."""
    finite = y[np.isfinite(y)]
    if len(finite) == 0:
        return -1.0, 1.0
    ymin, ymax = float(finite.min()), float(finite.max())
    span = max(ymax - ymin, min_span)
    margin = span * margin_frac
    return ymin - margin, ymax + margin
