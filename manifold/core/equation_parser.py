"""
Safe equation parser using AST whitelisting.

Never uses raw eval() on user input. Blocks imports, attribute access,
subscripts, and all builtins via an AST node whitelist + empty __builtins__.
"""

from __future__ import annotations

import ast
from typing import Callable

import numpy as np


# Names available to user equations
ALLOWED_NAMES: dict[str, object] = {
    # Trig
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "arcsin": np.arcsin,
    "arccos": np.arccos,
    "arctan": np.arctan,
    "arctan2": np.arctan2,
    # Exponential / log
    "exp": np.exp,
    "log": np.log,
    "log2": np.log2,
    "log10": np.log10,
    "sqrt": np.sqrt,
    # Misc
    "abs": np.abs,
    "sign": np.sign,
    "floor": np.floor,
    "ceil": np.ceil,
    "round": np.round,
    # Complex
    "real": np.real,
    "imag": np.imag,
    "conj": np.conj,
    "angle": np.angle,
    # Constants
    "pi": np.pi,
    "e": np.e,
    "inf": np.inf,
    # Hyperbolic
    "sinh": np.sinh,
    "cosh": np.cosh,
    "tanh": np.tanh,
}

_SAFE_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Constant,
    ast.Name,
    ast.Load,
    # Operators
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv,
    ast.Pow, ast.Mod, ast.USub, ast.UAdd,
    # Comparison (for conditional expressions)
    ast.Compare, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.NotEq,
    # Boolean (for masking)
    ast.BoolOp, ast.And, ast.Or, ast.Not,
    # Ternary: a if cond else b
    ast.IfExp,
)


def _validate_ast(expression: str, extra_vars: set[str] = frozenset()) -> None:
    """Walk AST and reject any unsafe node type or unknown name."""
    tree = ast.parse(expression, mode="eval")
    allowed_names = set(ALLOWED_NAMES.keys()) | extra_vars
    for node in ast.walk(tree):
        if not isinstance(node, _SAFE_NODES):
            raise ValueError(
                f"Disallowed expression construct: {type(node).__name__}. "
                "Only arithmetic, numpy math functions, and constants are allowed."
            )
        if isinstance(node, ast.Name) and node.id not in allowed_names:
            raise ValueError(
                f"Unknown name '{node.id}'. "
                f"Available: {', '.join(sorted(allowed_names))}"
            )


class EquationParser:
    """
    Safely compiles user-typed equation strings into vectorized callables.

    Examples:
        parser = EquationParser()
        f = parser.parse("sin(x) + x**2")
        f(np.linspace(-5, 5, 100))   # → ndarray

        g = parser.parse_xt("sin(x + t) * exp(-0.1 * x**2)")
        g(x_arr, t=1.5)              # → ndarray

        h = parser.parse_complex("z**2 + 1")
        h(complex_grid)              # → complex ndarray
    """

    def parse(
        self, expression: str, variable: str = "x"
    ) -> Callable[[np.ndarray], np.ndarray]:
        """Compile expression with one spatial variable."""
        _validate_ast(expression, extra_vars={variable})
        ns = dict(ALLOWED_NAMES)
        code = compile(expression, "<equation>", "eval")

        def f(x: np.ndarray) -> np.ndarray:
            local = dict(ns, **{variable: x})
            return eval(code, {"__builtins__": {}}, local)

        f.__doc__ = expression
        return f

    def parse_xt(self, expression: str) -> Callable[[np.ndarray, float], np.ndarray]:
        """Compile expression with spatial variable 'x' and time 't'."""
        _validate_ast(expression, extra_vars={"x", "t"})
        ns = dict(ALLOWED_NAMES)
        code = compile(expression, "<equation>", "eval")

        def f(x: np.ndarray, t: float) -> np.ndarray:
            local = dict(ns, x=x, t=t)
            return eval(code, {"__builtins__": {}}, local)

        f.__doc__ = expression
        return f

    def parse_xy(self, expression: str) -> Callable[[np.ndarray, np.ndarray], np.ndarray]:
        """Compile expression with 'x' and 'y' spatial variables (for 3D surfaces)."""
        _validate_ast(expression, extra_vars={"x", "y"})
        ns = dict(ALLOWED_NAMES)
        code = compile(expression, "<equation>", "eval")

        def f(x: np.ndarray, y: np.ndarray) -> np.ndarray:
            local = dict(ns, x=x, y=y)
            return eval(code, {"__builtins__": {}}, local)

        f.__doc__ = expression
        return f

    def parse_complex(self, expression: str) -> Callable[[np.ndarray], np.ndarray]:
        """Compile expression with complex variable 'z'."""
        _validate_ast(expression, extra_vars={"z"})
        ns = dict(ALLOWED_NAMES)
        code = compile(expression, "<equation>", "eval")

        def f(z: np.ndarray) -> np.ndarray:
            local = dict(ns, z=z)
            return eval(code, {"__builtins__": {}}, local)

        f.__doc__ = expression
        return f

    def validate(self, expression: str, variables: set[str] = frozenset({"x"})) -> str | None:
        """
        Validate an expression string without compiling a callable.
        Returns None if valid, or an error message string if invalid.
        """
        try:
            _validate_ast(expression, extra_vars=variables)
            return None
        except (ValueError, SyntaxError) as exc:
            return str(exc)
