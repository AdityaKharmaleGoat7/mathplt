"""Manifold web app — app instance and parser singleton.

Run with: python -m webapp.main
"""

import dash

from manifold.core.equation_parser import EquationParser

app = dash.Dash(__name__, title="Manifold", suppress_callback_exceptions=True)
_parser = EquationParser()
