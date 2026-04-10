"""Shared utilities — parsers, colors, presets, info panel data."""

import numpy as np
from dash import html


# ── Linear transform helpers ─────────────────────────────────────────────────

def _parse_matrix(text: str) -> np.ndarray:
    """Parse '1, 0; 0, 1' -> np.array([[1, 0], [0, 1]])."""
    rows = [r.strip() for r in text.split(";") if r.strip()]
    return np.array([[float(x) for x in row.split(",")] for row in rows])


def _parse_vector(text: str):
    """Parse '1, 2' -> np.array([1, 2]) or None if empty."""
    if not text or not text.strip():
        return None
    return np.array([float(x) for x in text.split(",")])


def _parse_vectors(text: str, dim: int):
    """Parse semicolon- or newline-separated vectors.

    '1, 2; 3, 4' -> [np.array([1,2]), np.array([3,4])]
    Returns list of valid vectors matching *dim* components. Empty -> [].
    """
    if not text or not text.strip():
        return []
    # Split on semicolons or newlines
    parts = [p.strip() for p in text.replace("\n", ";").split(";") if p.strip()]
    vecs = []
    for p in parts:
        try:
            v = np.array([float(x) for x in p.split(",")])
            if len(v) == dim:
                vecs.append(v)
        except (ValueError, TypeError):
            continue
    return vecs


# Distinct colors for multiple user vectors
_VEC_COLORS = [
    "#00ff88",  # lime green (original)
    "#ff6bff",  # pink
    "#ffcc00",  # gold
    "#00ccff",  # cyan
    "#ff6b6b",  # coral
    "#b388ff",  # lavender
    "#ff9100",  # orange
    "#76ff03",  # light green
]


# ── Equation presets per mode ─────────────────────────────────────────────────
_PRESETS = {
    "graph2d": [
        "sin(x + t)",
        "sin(x) * cos(t)",
        "sin(x + t) * exp(-0.1 * x**2)",
        "cos(3*x - 2*t) + 0.5*sin(5*x + t)",
        "exp(-0.05*(x - 3*t)**2)",
        "sin(x + t) + sin(x + 1.05*t)",
        "tanh(x - 2*t)",
        "sin(x*t) / (1 + x**2)",
    ],
    "graph3d": [
        "sin(sqrt(x**2 + y**2))",
        "exp(-0.1*(x**2+y**2)) * cos(x+y)",
        "sin(x) * cos(y)",
        "x * exp(-x**2 - y**2)",
        "(1 - 2*(x**2+y**2)) * exp(-(x**2+y**2))",
        "sin(x**2 + y**2) / (x**2 + y**2 + 1)",
    ],
    "complex": [
        "z**2",
        "z**3 - 1",
        "(z**2 - 1) / (z**2 + 1)",
        "sin(z)",
        "exp(z)",
        "1 / z",
        "z * exp(-abs(z)**2 / 4)",
        "sin(z + t)",
    ],
    "linear_transform_2d": [
        "0.707, -0.707; 0.707, 0.707",
        "1, 1; 0, 1",
        "2, 0; 0, 0.5",
        "1, 0; 0, -1",
        "0, -1; 1, 0",
        "2, 0; 0, 2",
    ],
    "linear_transform_3d": [
        "0.707, -0.707, 0; 0.707, 0.707, 0; 0, 0, 1",
        "1, 0, 0; 0, 0.707, -0.707; 0, 0.707, 0.707",
        "2, 0, 0; 0, 2, 0; 0, 0, 2",
        "1, 1, 0; 0, 1, 0; 0, 0, 1",
        "1, 0, 0; 0, 1, 0; 0, 0, -1",
        "-1, 0, 0; 0, -1, 0; 0, 0, -1",
    ],
}

# Preset labels for linear transforms (shown on buttons instead of raw matrix text)
_PRESET_LABELS = {
    "linear_transform_2d": [
        "Rotate 45", "Shear", "Aniso scale",
        "Reflect Y", "Rotate 90", "Scale 2x",
    ],
    "linear_transform_3d": [
        "Rot Z 45", "Rot X 45", "Scale 3D",
        "Shear XY", "Reflect Z", "Inversion",
    ],
}


# ── Info panel content per animation type ─────────────────────────────────────
_INFO = {
    "graph2d": {
        "title": "2D Animated Graph -- f(x, t)",
        "desc": (
            "Plot any curve y = f(x, t) where x is the spatial axis "
            "and t advances each frame. The curve redraws every frame, "
            "animating anything that depends on t."
        ),
        "sections": [
            ("Wave equation building blocks", [
                ("Term", "Controls", "Example"),
                ("A * sin(...)", "Amplitude -- peak height", "2 * sin(x) doubles height"),
                ("sin(k*x)", "Spatial frequency -- peaks per unit", "sin(3*x) is 3x denser"),
                ("sin(x - v*t)", "Travelling right at speed v", "sin(x - 2*t)"),
                ("sin(x + v*t)", "Travelling left at speed v", "sin(x + t)"),
                ("sin(x) * cos(t)", "Standing wave -- nodes fixed", "nodes at multiples of pi"),
                ("* exp(-a*x**2)", "Gaussian envelope", "sin(x+t) * exp(-0.1*x**2)"),
                ("f(x) + g(x)", "Superposition / beats", "sin(x+t) + sin(x+1.05*t)"),
            ]),
        ],
    },
    "graph3d": {
        "title": "3D Surface Explorer -- f(x, y)",
        "desc": (
            "Animate an orbital 360 degree rotation of any surface f(x, y). "
            "x and y form the input plane; height z = f(x, y) is the output. "
            "Color encodes height via the colorbar."
        ),
        "sections": [
            ("Surface features", [
                ("Feature", "What it means"),
                ("Peak (local max)", "Curves downward in all directions"),
                ("Valley (local min)", "Curves upward in all directions"),
                ("Saddle point", "Curves up in one direction, down in another"),
                ("Oscillating", "sin(x)*cos(y) -- periodic in both directions"),
            ]),
        ],
    },
    "complex": {
        "title": "Complex Plane -- Domain Coloring",
        "desc": (
            "Visualize complex functions f(z) where every pixel is colored by "
            "phase (hue) and magnitude (brightness rings). Include t to animate."
        ),
        "sections": [
            ("How to read the colors", [
                ("Visual feature", "What it encodes", "Formula"),
                ("Hue (color wheel)", "Phase / argument", "arg(f(z)) in [-pi, pi]"),
                ("Brightness rings", "Magnitude (log scale)", "log(1 + |f(z)|)"),
                ("Dark pinch-points", "Zeros -- f(z) = 0", "All colors converge inward"),
                ("Bright chaos", "Poles -- |f(z)| -> inf", "Colors cycle rapidly outward"),
            ]),
        ],
    },
    "riemann.zeros": {
        "title": "Riemann zeta -- Zeros on Critical Line",
        "desc": (
            "Traces the path of zeta(1/2+it) in the complex plane as t grows. "
            "Every time the orange dot crosses the origin (white cross), "
            "a nontrivial zero of zeta(s) occurs."
        ),
        "sections": [
            ("What is the Riemann Zeta Function?", [
                ("Property", "Details"),
                ("Definition (Re(s) > 1)", "zeta(s) = 1 + 1/2^s + 1/3^s + ..."),
                ("Analytic continuation", "Extends to all C except s = 1 (pole)"),
                ("Nontrivial zeros", "All known ones lie on Re(s) = 1/2"),
                ("Riemann Hypothesis", "All nontrivial zeros have Re(s) = 1/2 -- unproven since 1859"),
            ]),
            ("Known nontrivial zeros (Im part)", [
                ("#", "Imaginary part"),
                ("1", "14.135"),
                ("2", "21.022"),
                ("3", "25.011"),
                ("4", "30.425"),
                ("5", "32.935"),
                ("6", "37.586"),
                ("7", "40.919"),
                ("8", "43.327"),
            ]),
        ],
    },
    "riemann.critical_strip": {
        "title": "Riemann zeta -- Critical Strip Heatmap",
        "desc": (
            "Shows log(1+|zeta(s)|) and arg(zeta(s)) as heatmaps over the critical strip "
            "0 < Re(s) < 1. The cyan dashed line marks Re(s) = 1/2."
        ),
        "sections": [
            ("Reading the heatmaps", [
                ("Panel", "What it shows"),
                ("Left -- log magnitude", "Dark = |zeta(s)| near 0 (zeros), bright = large"),
                ("Right -- phase (HSV)", "Phase cycles; zeros are phase vortices"),
                ("Cyan dashed line", "Critical line Re(s) = 1/2"),
            ]),
        ],
    },
    "riemann.winding": {
        "title": "Riemann zeta -- Winding Number",
        "desc": (
            "Applies the Argument Principle: the number of zeros of zeta(s) inside a "
            "rectangular contour C equals the winding number of zeta(C) around the origin."
        ),
        "sections": [
            ("The Argument Principle", [
                ("Concept", "Details"),
                ("Formula", "N(zeros) = (1/2pi) x total change in arg(zeta(C))"),
                ("Each red x", "A nontrivial zero inside the contour"),
                ("Orange curve (right)", "Image zeta(C); loops = zeros enclosed"),
            ]),
        ],
    },
    "riemann.point": {
        "title": "Riemann zeta -- Evaluate zeta(a + ib)",
        "desc": (
            "Enter any complex number s = a + ib. "
            "Left panel shows zeta(a+it) path in the complex plane. "
            "Right panel shows |zeta(a+it)| vs t."
        ),
        "sections": [
            ("Interesting values to try", [
                ("a", "b", "What you see"),
                ("0.5", "14.135", "First nontrivial zero -- passes through origin"),
                ("0.5", "21.022", "Second zero"),
                ("1.5", "any", "Convergence region -- no zeros"),
                ("0.1", "14.135", "Left of critical line -- shifted"),
                ("0.9", "14.135", "Right of critical line -- symmetric"),
            ]),
        ],
    },
    "linear_transform": {
        "title": "Linear Transformation Visualizer",
        "desc": (
            "Watch how a matrix transforms space. The grid smoothly "
            "interpolates from identity to the given matrix. Basis vectors "
            "(red = e1, blue = e2) show where the standard basis lands."
        ),
        "sections": [
            ("Key concepts", [
                ("Concept", "What to look for"),
                ("Determinant", "Area/volume scaling factor; det=0 collapses space"),
                ("Eigenvectors", "Directions that only get scaled, not rotated"),
                ("Rotation", "Off-diagonal elements; columns rotate basis vectors"),
                ("Shear", "One axis slides along another; parallelism preserved"),
                ("Reflection", "Negative determinant; orientation flips"),
            ]),
            ("2D presets explained", [
                ("Preset", "Matrix", "Effect"),
                ("Rotate 45", "0.707, -0.707; 0.707, 0.707", "Counter-clockwise 45 degrees"),
                ("Shear", "1, 1; 0, 1", "Horizontal shear; top slides right"),
                ("Aniso scale", "2, 0; 0, 0.5", "Stretch x, compress y"),
                ("Reflect Y", "1, 0; 0, -1", "Mirror across x-axis"),
            ]),
        ],
    },
}


def _info_table(rows):
    header = rows[0]
    body = rows[1:]
    th_style = {"background": "#21262d", "color": "#8b949e", "padding": "5px 8px",
                "fontSize": "11px", "fontWeight": "600", "textAlign": "left",
                "borderBottom": "1px solid #30363d"}
    td_style = {"padding": "5px 8px", "color": "#c9d1d9", "fontSize": "12px",
                "borderBottom": "1px solid #21262d", "verticalAlign": "top"}
    td_code_style = {**td_style, "fontFamily": "monospace", "color": "#7ee787"}
    return html.Table(style={"width": "100%", "borderCollapse": "collapse", "marginTop": "6px"},
        children=[
            html.Thead(html.Tr([html.Th(h, style=th_style) for h in header])),
            html.Tbody([
                html.Tr([
                    html.Td(cell, style=(td_code_style if j == 0 and
                                        any(c in cell for c in ("(", "/", "**", "="))
                                        else td_style))
                    for j, cell in enumerate(row)
                ])
                for row in body
            ]),
        ]
    )
