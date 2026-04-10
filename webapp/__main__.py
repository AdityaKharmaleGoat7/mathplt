"""Allow running with: python -m webapp"""

from webapp.main import app

app.run(debug=True, port=8050)
