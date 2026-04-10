"""Manifold web app — entry point. Run with: python -m webapp.main"""

from webapp.app import app
from webapp.layout import build_layout
from webapp.theme import INDEX_STRING

# Set the custom HTML template (dark-mode CSS injection)
app.index_string = INDEX_STRING

# Build and assign the layout
app.layout = build_layout()

# Import callbacks module to register all @app.callback decorators
import webapp.callbacks  # noqa: F401

if __name__ == "__main__":
    app.run(debug=True, port=8050)
