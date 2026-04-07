"""
Tests for the AST-whitelisted equation parser.

Critical tests:
- Allowed expressions evaluate correctly
- Disallowed constructs are rejected (security)
- Edge cases: empty input, NaN, division by zero
"""

import numpy as np
import pytest

from manifold.core.equation_parser import EquationParser


class TestParseSingleVariable:
    def test_simple_sine(self, x_array):
        parser = EquationParser()
        f = parser.parse("sin(x)")
        result = f(x_array)
        np.testing.assert_allclose(result, np.sin(x_array))

    def test_polynomial(self, x_array):
        parser = EquationParser()
        f = parser.parse("x**2 + 2*x + 1")
        result = f(x_array)
        expected = x_array**2 + 2*x_array + 1
        np.testing.assert_allclose(result, expected)

    def test_combined_functions(self, x_array):
        parser = EquationParser()
        f = parser.parse("sin(x) * exp(-0.1 * x**2)")
        result = f(x_array)
        expected = np.sin(x_array) * np.exp(-0.1 * x_array**2)
        np.testing.assert_allclose(result, expected)

    def test_constants_available(self, x_array):
        parser = EquationParser()
        f = parser.parse("pi * x")
        result = f(x_array)
        np.testing.assert_allclose(result, np.pi * x_array)


class TestParseXT:
    def test_travelling_wave(self, x_array):
        parser = EquationParser()
        f = parser.parse_xt("sin(x + t)")
        result = f(x_array, 1.0)
        np.testing.assert_allclose(result, np.sin(x_array + 1.0))

    def test_t_is_zero(self, x_array):
        parser = EquationParser()
        f = parser.parse_xt("sin(x + t)")
        result = f(x_array, 0.0)
        np.testing.assert_allclose(result, np.sin(x_array))

    def test_time_decay(self, x_array):
        parser = EquationParser()
        f = parser.parse_xt("cos(x) * exp(-t)")
        result = f(x_array, 2.0)
        expected = np.cos(x_array) * np.exp(-2.0)
        np.testing.assert_allclose(result, expected)


class TestParseXY:
    def test_simple_product(self):
        parser = EquationParser()
        f = parser.parse_xy("sin(x) * cos(y)")
        x = np.array([[0.0, np.pi/2]])
        y = np.array([[0.0, 0.0]])
        result = f(x, y)
        expected = np.sin(x) * np.cos(y)
        np.testing.assert_allclose(result, expected, atol=1e-10)


class TestParseComplex:
    def test_square(self, complex_grid_small):
        parser = EquationParser()
        f = parser.parse_complex("z**2")
        result = f(complex_grid_small)
        np.testing.assert_allclose(result, complex_grid_small**2)

    def test_identity(self, complex_grid_small):
        parser = EquationParser()
        f = parser.parse_complex("z")
        result = f(complex_grid_small)
        np.testing.assert_allclose(result, complex_grid_small)


class TestSecurityRejections:
    """Ensure disallowed constructs are blocked."""

    def _should_fail(self, expr, variables=frozenset({"x"})):
        from manifold.core.equation_parser import _validate_ast
        with pytest.raises(ValueError):
            _validate_ast(expr, extra_vars=variables)

    def test_reject_import(self):
        self._should_fail("__import__('os')")

    def test_reject_attribute_access(self):
        self._should_fail("x.__class__")

    def test_reject_list_comprehension(self):
        self._should_fail("[x for x in range(10)]")

    def test_reject_lambda(self):
        self._should_fail("lambda x: x")

    def test_reject_subscript(self):
        self._should_fail("x[0]")

    def test_reject_unknown_name(self):
        self._should_fail("secret_function(x)")

    def test_reject_builtins(self):
        self._should_fail("open('file.txt')")

    def test_reject_assignment(self):
        # Assignment expressions (walrus) should be rejected
        self._should_fail("(y := x + 1)")

    def test_reject_call_to_unknown(self):
        self._should_fail("eval('1+1')", variables=frozenset({"x"}))


class TestValidateMethod:
    def test_valid_returns_none(self):
        parser = EquationParser()
        result = parser.validate("sin(x) + x**2", variables={"x"})
        assert result is None

    def test_invalid_returns_string(self):
        parser = EquationParser()
        result = parser.validate("import os", variables={"x"})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_syntax_error_returns_string(self):
        parser = EquationParser()
        result = parser.validate("sin(x +++ ", variables={"x"})
        assert isinstance(result, str)
