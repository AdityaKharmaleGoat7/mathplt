"""Manifold web app — app instance and parser singleton.

Run with: python -m webapp.main
"""

import dash

from manifold.core.equation_parser import EquationParser

app = dash.Dash(__name__, title="Own the space", suppress_callback_exceptions=True)
app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/png" href="/assets/logo.png">
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""
_parser = EquationParser()
