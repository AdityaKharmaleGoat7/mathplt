"""Global constants and default style settings."""

# Default figure style
DARK_BG = "#0d1117"
ACCENT_BLUE = "#00BFFF"
ACCENT_ORANGE = "#FF8C00"
ACCENT_GREEN = "#39FF14"
GRID_ALPHA = 0.25

# Colormaps suited for complex/Riemann visualizations
MAGNITUDE_CMAP = "inferno"
PHASE_CMAP = "hsv"
SURFACE_CMAP = "viridis"

# mpmath precision defaults
DEFAULT_DPS = 25       # sufficient for plotting
HIGH_DPS = 50          # for verifying zero locations

# Cache directory for expensive zeta computations
import os
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "manifold")
