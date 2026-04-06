"""mathplt web app — run with: python -m webapp.app"""

import dash
from dash import dcc, html, Input, Output, State, ctx
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

from mathplt.core.equation_parser import EquationParser

app = dash.Dash(__name__, title="mathplt", suppress_callback_exceptions=True)
_parser = EquationParser()

# ── Dark theme template ────────────────────────────────────────────────────────
DARK = dict(
    template="plotly_dark",
    paper_bgcolor="#0d1117",
    plot_bgcolor="#161b22",
    font=dict(color="#e6edf3"),
    margin=dict(l=50, r=20, t=50, b=50),
    uirevision="keep",
)

# ── Layout ─────────────────────────────────────────────────────────────────────
app.layout = html.Div(style={
    "display": "flex", "height": "100vh", "background": "#0d1117",
    "color": "#e6edf3", "fontFamily": "monospace", "overflow": "hidden",
}, children=[

    # Sidebar
    html.Div(style={
        "width": "300px", "minWidth": "300px", "padding": "16px 12px",
        "borderRight": "1px solid #30363d", "overflowY": "auto",
        "background": "#0d1117",
    }, children=[

        html.H3("mathplt", style={"color": "#58a6ff", "margin": "0 0 4px 0"}),
        html.Div("interactive math animations", style={"color": "#8b949e", "fontSize": "12px", "marginBottom": "16px"}),

        # Animation type
        html.Label("Animation type", style={"color": "#8b949e", "fontSize": "11px"}),
        dcc.Dropdown(id="anim-type", value="graph2d", clearable=False,
            options=[
                {"label": "2D Graph  f(x, t)",                     "value": "graph2d"},
                {"label": "3D Surface  f(x, y)",                    "value": "graph3d"},
                {"label": "Complex Plane  f(z)",                    "value": "complex"},
                {"label": "Riemann: Zeros on critical line",         "value": "riemann.zeros"},
                {"label": "Riemann: Critical strip heatmap",         "value": "riemann.critical_strip"},
                {"label": "Riemann: Winding number",                 "value": "riemann.winding"},
            ],
            style={"marginBottom": "14px", "fontSize": "13px"},
        ),

        # Equation
        html.Div(id="eq-section", children=[
            html.Label("Equation", style={"color": "#8b949e", "fontSize": "11px"}),
            dcc.Input(id="equation", type="text", debounce=True,
                value="sin(x + t) * exp(-0.1 * x**2)",
                style={
                    "width": "100%", "boxSizing": "border-box",
                    "background": "#161b22", "color": "#e6edf3",
                    "border": "1px solid #30363d", "borderRadius": "6px",
                    "padding": "8px", "fontFamily": "monospace", "fontSize": "13px",
                    "marginBottom": "4px",
                },
            ),
            html.Div(id="eq-status", style={"fontSize": "11px", "marginBottom": "12px", "color": "#8b949e"},
                     children="Press Enter to apply"),
        ]),

        # x range
        html.Div(id="xrange-section", children=[
            html.Label("x range", style={"color": "#8b949e", "fontSize": "11px"}),
            dcc.RangeSlider(id="xrange", min=-20, max=20, step=1, value=[-10, 10],
                marks={-20: "-20", -10: "-10", 0: "0", 10: "10", 20: "20"},
                tooltip={"placement": "bottom", "always_visible": True}),
            html.Div(style={"height": "8px"}),
        ]),

        # y range (3D only)
        html.Div(id="yrange-section", style={"display": "none"}, children=[
            html.Label("y range", style={"color": "#8b949e", "fontSize": "11px"}),
            dcc.RangeSlider(id="yrange", min=-20, max=20, step=1, value=[-5, 5],
                marks={-20: "-20", 0: "0", 20: "20"},
                tooltip={"placement": "bottom", "always_visible": True}),
            html.Div(style={"height": "8px"}),
        ]),

        # Re/Im range (complex)
        html.Div(id="complex-section", style={"display": "none"}, children=[
            html.Label("Re(z) range", style={"color": "#8b949e", "fontSize": "11px"}),
            dcc.RangeSlider(id="rerange", min=-8, max=8, step=0.5, value=[-3, 3],
                marks={-8: "-8", 0: "0", 8: "8"},
                tooltip={"placement": "bottom", "always_visible": True}),
            html.Div(style={"height": "8px"}),
            html.Label("Im(z) range", style={"color": "#8b949e", "fontSize": "11px"}),
            dcc.RangeSlider(id="imrange", min=-8, max=8, step=0.5, value=[-3, 3],
                marks={-8: "-8", 0: "0", 8: "8"},
                tooltip={"placement": "bottom", "always_visible": True}),
            html.Div(style={"height": "8px"}),
        ]),

        # t slider
        html.Div(id="t-section", children=[
            html.Label("t  (time)", style={"color": "#8b949e", "fontSize": "11px"}),
            dcc.Slider(id="tval", min=0, max=20, step=0.05, value=0,
                marks={0: "0", 10: "10", 20: "20"},
                tooltip={"placement": "bottom", "always_visible": True}),
            html.Div(style={"height": "8px"}),
        ]),

        # Resolution
        html.Label("Resolution", style={"color": "#8b949e", "fontSize": "11px"}),
        dcc.Slider(id="resolution", min=30, max=300, step=10, value=150,
            marks={30: "30", 150: "150", 300: "300"},
            tooltip={"placement": "bottom", "always_visible": True}),
        html.Div(style={"height": "14px"}),

        # Colormap
        html.Div(id="cmap-section", children=[
            html.Label("Colormap", style={"color": "#8b949e", "fontSize": "11px"}),
            dcc.Dropdown(id="colormap", value="viridis", clearable=False,
                options=[{"label": c, "value": c} for c in
                         ["viridis", "plasma", "inferno", "magma", "turbo", "RdBu", "Spectral"]],
                style={"marginBottom": "14px", "fontSize": "13px"},
            ),
        ]),

        # Riemann controls
        html.Div(id="riemann-section", style={"display": "none"}, children=[
            html.Label("Zeros to find", style={"color": "#8b949e", "fontSize": "11px"}),
            dcc.Slider(id="nzeros", min=5, max=25, step=1, value=12,
                marks={5: "5", 15: "15", 25: "25"},
                tooltip={"placement": "bottom", "always_visible": True}),
            html.Div(style={"height": "8px"}),
            html.Label("Im(s) max", style={"color": "#8b949e", "fontSize": "11px"}),
            dcc.Slider(id="imsmax", min=5, max=60, step=1, value=40,
                marks={5: "5", 20: "20", 40: "40", 60: "60"},
                tooltip={"placement": "bottom", "always_visible": True}),
            html.Div(style={"height": "8px"}),
            html.Label("Winding contour top", style={"color": "#8b949e", "fontSize": "11px"}),
            dcc.Slider(id="windtop", min=2, max=45, step=0.5, value=15,
                marks={0: "0", 15: "15", 30: "30", 45: "45"},
                tooltip={"placement": "bottom", "always_visible": True}),
            html.Div(style={"height": "8px"}),
        ]),

        # Animate
        html.Div(id="anim-section", children=[
            html.Div(style={"display": "flex", "gap": "8px", "marginBottom": "10px"}, children=[
                html.Button("▶  Play", id="play-btn", n_clicks=0, style={
                    "flex": 1, "background": "#238636", "color": "white",
                    "border": "none", "borderRadius": "6px", "padding": "8px",
                    "cursor": "pointer", "fontSize": "14px",
                }),
                html.Button("■  Stop", id="stop-btn", n_clicks=0, style={
                    "flex": 1, "background": "#6e7681", "color": "white",
                    "border": "none", "borderRadius": "6px", "padding": "8px",
                    "cursor": "pointer", "fontSize": "14px",
                }),
            ]),
            html.Label("Animation speed", style={"color": "#8b949e", "fontSize": "11px"}),
            dcc.Slider(id="speed", min=30, max=500, step=10, value=80,
                marks={30: "fast", 500: "slow"},
                tooltip={"placement": "bottom", "always_visible": True}),
        ]),

        # Info panel
        html.Hr(style={"borderColor": "#30363d", "margin": "16px 0 10px 0"}),
        html.Div(id="info-panel"),

    ]),

    # Main graph area
    html.Div(style={"flex": 1, "overflow": "hidden"}, children=[
        dcc.Graph(id="graph", style={"height": "100vh"},
                  config={"scrollZoom": True, "displayModeBar": True,
                          "toImageButtonOptions": {"format": "png", "scale": 2}}),
    ]),

    # Interval timer
    dcc.Interval(id="interval", interval=80, disabled=True),
])


# ── Callbacks ──────────────────────────────────────────────────────────────────

# Show/hide sections based on animation type
@app.callback(
    Output("eq-section",      "style"),
    Output("xrange-section",  "style"),
    Output("yrange-section",  "style"),
    Output("complex-section", "style"),
    Output("t-section",       "style"),
    Output("cmap-section",    "style"),
    Output("riemann-section", "style"),
    Output("anim-section",    "style"),
    Input("anim-type", "value"),
)
def show_controls(anim):
    show = {"display": "block"}
    hide = {"display": "none"}
    eq      = show if anim in ("graph2d", "graph3d", "complex") else hide
    xrange  = show if anim in ("graph2d", "graph3d") else hide
    yrange  = show if anim == "graph3d" else hide
    cplx    = show if anim == "complex" else hide
    t       = show if anim in ("graph2d", "complex", "riemann.zeros") else hide
    cmap    = show if anim in ("graph3d", "complex") else hide
    riemann = show if anim.startswith("riemann") else hide
    anim_s  = show if anim in ("graph2d", "complex", "riemann.zeros") else hide
    return eq, xrange, yrange, cplx, t, cmap, riemann, anim_s


# Equation validation
@app.callback(
    Output("eq-status", "children"),
    Output("eq-status", "style"),
    Input("equation", "value"),
    State("anim-type", "value"),
    prevent_initial_call=True,
)
def validate_eq(expr, anim):
    if not expr:
        return "Empty equation.", {"fontSize": "11px", "color": "#ff6b6b", "marginBottom": "12px"}
    vars_map = {"graph2d": {"x","t"}, "graph3d": {"x","y"}, "complex": {"z","t"}}
    err = _parser.validate(expr, variables=vars_map.get(anim, {"x","t"}))
    if err:
        return f"✗ {err}", {"fontSize": "11px", "color": "#ff6b6b", "marginBottom": "12px"}
    return "✓ Valid", {"fontSize": "11px", "color": "#69db7c", "marginBottom": "12px"}


# Play / Stop
@app.callback(
    Output("interval", "disabled"),
    Output("play-btn", "children"),
    Output("play-btn", "style"),
    Input("play-btn", "n_clicks"),
    Input("stop-btn", "n_clicks"),
    State("interval", "disabled"),
    prevent_initial_call=True,
)
def toggle_play(_p, _s, is_disabled):
    base = {"flex": 1, "color": "white", "border": "none", "borderRadius": "6px",
            "padding": "8px", "cursor": "pointer", "fontSize": "14px"}
    if ctx.triggered_id == "stop-btn":
        return True, "▶  Play", {**base, "background": "#238636"}
    # toggle
    now_playing = is_disabled  # if was disabled, now playing
    if now_playing:
        return False, "⏸  Pause", {**base, "background": "#b08800"}
    else:
        return True,  "▶  Play",  {**base, "background": "#238636"}


# Speed slider → interval
@app.callback(Output("interval", "interval"), Input("speed", "value"))
def set_speed(ms): return ms or 80


# Info panel content per animation type
_INFO = {
    "graph2d": {
        "title": "2D Animated Graph — f(x, t)",
        "desc": (
            "Plot any curve y = f(x, t) where x is the spatial axis "
            "and t advances each frame. At 30 fps, frame 60 gives t = 2.0. "
            "The curve redraws every frame, animating anything that depends on t."
        ),
        "sections": [
            ("Wave equation building blocks", [
                ("Term", "Controls", "Example"),
                ("A * sin(...)", "Amplitude — peak height", "2 * sin(x) doubles height"),
                ("sin(k*x)", "Spatial frequency — peaks per unit", "sin(3*x) is 3× denser"),
                ("sin(x - v*t)", "Travelling right at speed v", "sin(x - 2*t)"),
                ("sin(x + v*t)", "Travelling left at speed v", "sin(x + t)"),
                ("sin(x) * cos(t)", "Standing wave — nodes fixed", "nodes at multiples of π"),
                ("* exp(-a*x**2)", "Gaussian envelope — localises wave", "sin(x+t) * exp(-0.1*x**2)"),
                ("f(x) + g(x)", "Superposition — interference / beats", "sin(x+t) + sin(x+1.05*t)"),
            ]),
            ("Example equations", [
                ("Equation", "What you see"),
                ("sin(x + t)", "Simple leftward travelling wave"),
                ("sin(x) * cos(t)", "Standing wave — nodes stay fixed"),
                ("sin(x + t) * exp(-0.1*x**2)", "Travelling wave with Gaussian decay"),
                ("cos(3*x - 2*t) + 0.5*sin(5*x + t)", "Two waves — beating pattern"),
                ("sin(x*t) / (1 + x**2)", "Frequency chirp — rate grows with time"),
                ("exp(-0.05*(x - 3*t)**2)", "Gaussian pulse travelling right at speed 3"),
                ("sin(x + t) + sin(x + 1.05*t)", "Beats — two close frequencies interfering"),
                ("tanh(x - 2*t)", "Kink / soliton — smooth step front moving right"),
            ]),
        ],
    },
    "graph3d": {
        "title": "3D Surface Explorer — f(x, y)",
        "desc": (
            "Animate an orbital 360° rotation of any surface f(x, y). "
            "x and y form the input plane; height z = f(x, y) is the output. "
            "Color also encodes height via the colorbar."
        ),
        "sections": [
            ("Surface features", [
                ("Feature", "What it means"),
                ("Peak (local max)", "∂f/∂x = 0 and ∂f/∂y = 0 — curves downward in all directions"),
                ("Valley (local min)", "Same conditions, curves upward"),
                ("Saddle point", "Curves up in one direction, down in another"),
                ("Flat ridge", "Constant along one axis, varying along the other"),
                ("Oscillating", "sin(x)*cos(y) — periodic in both directions"),
                ("Decaying amplitude", "exp(-(x²+y²)) shrinks surface toward zero from origin"),
            ]),
            ("Example equations", [
                ("Equation", "What you see", "Best range"),
                ("sin(sqrt(x**2 + y**2))", "Circular ripples from origin", "−6 to 6"),
                ("exp(-0.1*(x**2+y**2)) * cos(x+y)", "Gaussian-modulated diagonal wave", "−5 to 5"),
                ("sin(x) * cos(y)", "Saddle-wave egg-carton grid", "−4 to 4"),
                ("x * exp(-x**2 - y**2)", "Ricker wavelet — positive/negative ridge", "−3 to 3"),
                ("(1 - 2*(x**2+y**2)) * exp(-(x**2+y**2))", "Mexican hat / Laplacian of Gaussian", "−3 to 3"),
                ("sin(x**2 + y**2) / (x**2 + y**2 + 1)", "Sinc-like decay from origin", "−5 to 5"),
            ]),
        ],
    },
    "complex": {
        "title": "Complex Plane — Domain Coloring",
        "desc": (
            "Visualize complex functions f(z) where every pixel is colored by "
            "phase (hue) and magnitude (brightness rings). Include t in your equation to animate."
        ),
        "sections": [
            ("How to read the colors", [
                ("Visual feature", "What it encodes", "Formula"),
                ("Hue (color wheel)", "Phase / argument of output", "arg(f(z)) in [−π, π]"),
                ("Brightness rings", "Magnitude (log scale) — each ring = ×e", "log(1 + |f(z)|)"),
                ("Dark pinch-points", "Zeros — f(z) = 0", "All colors converge inward"),
                ("Bright chaos", "Poles — |f(z)| → ∞", "Colors cycle rapidly outward"),
                ("Color cycles per loop", "Winding number / order", "One full cycle = order-1 zero or pole"),
            ]),
            ("Phase color wheel", [
                ("Color", "Phase"),
                ("Red", "0"),
                ("Yellow", "π/3"),
                ("Green", "2π/3"),
                ("Cyan", "±π"),
                ("Blue", "−2π/3"),
                ("Magenta", "−π/3"),
            ]),
            ("Example equations", [
                ("Equation", "What you see"),
                ("z**2", "Two sectors; zero of order 2 at origin"),
                ("z**3 - 1", "Three zeros (cube roots of unity) in a triangle"),
                ("(z**2 - 1) / (z**2 + 1)", "Two zeros at ±1, two poles at ±i"),
                ("sin(z)", "Infinitely many zeros along real axis"),
                ("1 / z", "Single pole at origin — colors spiral outward"),
                ("exp(z)", "No zeros, no poles — magnitude grows rightward"),
                ("(z - 1j) / (z + 1j)", "Möbius transform — one zero, one pole"),
                ("z * exp(-abs(z)**2 / 4)", "Zero at origin with Gaussian decay"),
            ]),
        ],
    },
    "riemann.zeros": {
        "title": "Riemann ζ — Zeros on Critical Line",
        "desc": (
            "Traces the path of ζ(½+it) in the complex plane as t grows. "
            "Every time the orange dot crosses the origin (white cross), "
            "a nontrivial zero of ζ(s) occurs. Red dashed lines on the right "
            "panel mark the zero locations."
        ),
        "sections": [
            ("What is the Riemann Zeta Function?", [
                ("Property", "Details"),
                ("Definition (Re(s) > 1)", "ζ(s) = 1 + 1/2ˢ + 1/3ˢ + … = Σ 1/nˢ"),
                ("Analytic continuation", "Extends to all ℂ except s = 1 (pole)"),
                ("Trivial zeros", "Negative even integers: s = −2, −4, −6, …"),
                ("Nontrivial zeros", "All known ones lie on Re(s) = ½ (critical line)"),
                ("Riemann Hypothesis", "All nontrivial zeros have Re(s) = ½ — unproven since 1859"),
                ("Millennium Prize", "$1 million — unsolved for 165 years"),
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
        "title": "Riemann ζ — Critical Strip Heatmap",
        "desc": (
            "Shows log(1+|ζ(s)|) and arg(ζ(s)) as heatmaps over the critical strip "
            "0 < Re(s) < 1. The cyan dashed line marks Re(s) = ½ — the critical line "
            "where the Riemann Hypothesis predicts all nontrivial zeros lie."
        ),
        "sections": [
            ("Reading the heatmaps", [
                ("Panel", "What it shows"),
                ("Left — log magnitude", "Dark = |ζ(s)| near 0 (zeros), bright = large magnitude"),
                ("Right — phase (HSV)", "Phase cycles wrap around ±π; zeros are phase vortices"),
                ("Cyan dashed line", "Critical line Re(s) = ½"),
                ("Horizontal bands", "Zeros appear as dark spots on the left, phase singularities on the right"),
            ]),
            ("What is the critical strip?", [
                ("Region", "Significance"),
                ("Re(s) < 0", "Trivial zeros at even negative integers; ζ is well-understood"),
                ("0 < Re(s) < 1", "Critical strip — all nontrivial zeros live here"),
                ("Re(s) = ½", "Critical line — Riemann conjectured all zeros are here"),
                ("Re(s) > 1", "ζ(s) = Σ 1/nˢ converges; no zeros exist here"),
            ]),
        ],
    },
    "riemann.winding": {
        "title": "Riemann ζ — Winding Number (Argument Principle)",
        "desc": (
            "Applies the Argument Principle: the number of zeros of ζ(s) inside a "
            "rectangular contour C equals the winding number of ζ(C) around the origin. "
            "Red × marks are zeros inside the contour; grey × are outside."
        ),
        "sections": [
            ("The Argument Principle", [
                ("Concept", "Details"),
                ("Formula", "N(zeros) = (1/2π) × total change in arg(ζ(C))"),
                ("Winding number", "How many times ζ(C) loops around the origin"),
                ("Each red ×", "A nontrivial zero of ζ(s) on the critical line (Im part shown)"),
                ("Orange curve (left)", "The rectangular contour C in the s-plane"),
                ("Orange curve (right)", "Image ζ(C) in the ζ-plane; loops = zeros enclosed"),
                ("White cross", "Origin in ζ-plane — loops counted around this point"),
            ]),
            ("How to use", [
                ("Control", "Effect"),
                ("Winding contour top", "Raise Im(s) max to enclose more zeros"),
                ("Zeros to find", "How many zeros are computed and shown as ×"),
                ("Winding ≈ N", "Should equal the number of red × enclosed by contour"),
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
                    html.Td(cell, style=(td_code_style if j == 0 and "*" not in cell
                                        and any(c in cell for c in ("(", "/", "**", "=", "ζ", "∂", "Σ"))
                                        else td_style))
                    for j, cell in enumerate(row)
                ])
                for row in body
            ]),
        ]
    )


@app.callback(Output("info-panel", "children"), Input("anim-type", "value"))
def update_info(anim):
    info = _INFO.get(anim)
    if not info:
        return []

    card_style = {"background": "#161b22", "border": "1px solid #30363d",
                  "borderRadius": "8px", "padding": "12px 14px", "marginBottom": "10px"}
    h2_style = {"margin": "0 0 8px 0", "fontSize": "11px", "fontWeight": "700",
                "color": "#58a6ff", "textTransform": "uppercase", "letterSpacing": "0.07em"}
    p_style = {"margin": "0", "color": "#8b949e", "fontSize": "12px", "lineHeight": "1.6"}

    children = [
        html.Div(style=card_style, children=[
            html.H2(info["title"], style={"margin": "0 0 6px 0", "fontSize": "13px",
                                          "fontWeight": "700", "color": "#e6edf3"}),
            html.P(info["desc"], style=p_style),
        ]),
    ]

    for section_title, rows in info["sections"]:
        children.append(html.Div(style=card_style, children=[
            html.H2(section_title, style=h2_style),
            _info_table(rows),
        ]))

    return children


# Interval → advance t
@app.callback(
    Output("tval", "value"),
    Input("interval", "n_intervals"),
    State("tval", "value"),
    State("anim-type", "value"),
    State("imsmax", "value"),
    prevent_initial_call=True,
)
def tick(_, t, anim, imsmax):
    t = t or 0.0
    if anim in ("graph2d", "complex"):
        return round((t + 0.12) % 20.0, 3)
    if anim == "riemann.zeros":
        return round((t + 0.2) % float(imsmax or 40), 3)
    return t


# Main graph update
@app.callback(
    Output("graph", "figure"),
    Input("anim-type",  "value"),
    Input("equation",   "value"),
    Input("xrange",     "value"),
    Input("yrange",     "value"),
    Input("rerange",    "value"),
    Input("imrange",    "value"),
    Input("tval",       "value"),
    Input("resolution", "value"),
    Input("colormap",   "value"),
    Input("nzeros",     "value"),
    Input("imsmax",     "value"),
    Input("windtop",    "value"),
)
def update_graph(anim, eq, xr, yr, rer, imr, t, res, cmap, nz, imsmax, windtop):
    # Defaults
    eq      = eq      or "sin(x + t)"
    xr      = xr      or [-10, 10]
    yr      = yr      or [-5, 5]
    rer     = rer     or [-3, 3]
    imr     = imr     or [-3, 3]
    t       = float(t)   if t  is not None else 0.0
    res     = int(res)   if res is not None else 150
    cmap    = cmap    or "viridis"
    nz      = int(nz)    if nz  is not None else 12
    imsmax  = float(imsmax) if imsmax is not None else 40.0
    windtop = float(windtop) if windtop is not None else 15.0

    try:
        if anim == "graph2d":
            return _fig_2d(eq, xr, t, res)
        if anim == "graph3d":
            return _fig_3d(eq, xr, yr, res, cmap)
        if anim == "complex":
            return _fig_complex(eq, rer, imr, res, t)
        if anim == "riemann.zeros":
            return _fig_zeros(imsmax, nz, res, t)
        if anim == "riemann.critical_strip":
            return _fig_strip(imsmax, res)
        if anim == "riemann.winding":
            return _fig_winding(windtop, nz)
    except Exception as e:
        fig = go.Figure()
        fig.update_layout(**DARK, title=f"Error: {e}")
        return fig

    fig = go.Figure()
    fig.update_layout(**DARK)
    return fig


# ── Figure builders ────────────────────────────────────────────────────────────

def _fig_2d(eq, xr, t, res):
    f = _parser.parse_xt(eq)
    x = np.linspace(xr[0], xr[1], res)
    y = np.where(np.isfinite(y := f(x, t)), y, np.nan)
    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines",
                               line=dict(color="#00BFFF", width=2.5)))
    fig.add_hline(y=0, line=dict(color="gray", width=0.5, dash="dot"))
    fig.update_layout(**DARK, title=f"f(x,t) = {eq}   [t = {t:.2f}]",
                      xaxis_title="x", yaxis_title="f(x, t)", dragmode="pan")
    return fig


def _fig_3d(eq, xr, yr, res, cmap):
    f = _parser.parse_xy(eq)
    x = np.linspace(xr[0], xr[1], res)
    y = np.linspace(yr[0], yr[1], res)
    X, Y = np.meshgrid(x, y)
    Z = f(X, Y).astype(float)
    Z[~np.isfinite(Z)] = np.nan
    fig = go.Figure(go.Surface(x=X, y=Y, z=Z, colorscale=cmap, opacity=0.95))
    fig.update_layout(**DARK, title=f"f(x,y) = {eq}",
                      scene=dict(xaxis_title="x", yaxis_title="y", zaxis_title="f",
                                 uirevision="keep"))
    return fig


def _fig_complex(eq, rer, imr, res, t):
    from mathplt.math.complex_ops import complex_grid, domain_color_fast
    import plotly.express as px
    Z = complex_grid((rer[0], rer[1]), (imr[0], imr[1]), re_n=res, im_n=res)
    has_t = "t" in eq
    if has_t:
        from mathplt.core.equation_parser import ALLOWED_NAMES, _validate_ast
        _validate_ast(eq, extra_vars={"z", "t"})
        ns = dict(ALLOWED_NAMES)
        code = compile(eq, "<eq>", "eval")
        W = eval(code, {"__builtins__": {}}, dict(ns, z=Z, t=t))
    else:
        W = _parser.parse_complex(eq)(Z)
    rgb = (domain_color_fast(W) * 255).astype(np.uint8)
    fig = px.imshow(rgb, origin="lower")
    n = 5
    fig.update_xaxes(tickvals=np.linspace(0, res-1, n),
                     ticktext=[f"{v:.1f}" for v in np.linspace(rer[0], rer[1], n)],
                     title="Re(z)")
    fig.update_yaxes(tickvals=np.linspace(0, res-1, n),
                     ticktext=[f"{v:.1f}" for v in np.linspace(imr[0], imr[1], n)],
                     title="Im(z)")
    title = f"f(z) = {eq}" + (f"  [t={t:.2f}]" if has_t else "")
    fig.update_layout(**DARK, title=title)
    return fig


def _fig_zeros(t_max, n_zeros, res, t_cursor):
    from mathplt.math.zeta import zeta_on_critical_line, find_zeros_on_critical_line
    t_vals = np.linspace(0.5, t_max, max(res * 5, 500))
    zv = zeta_on_critical_line(t_vals, dps=25)
    zeros = find_zeros_on_critical_line(n_zeros=n_zeros, dps=30)
    idx = min(int(np.searchsorted(t_vals, t_cursor)), len(t_vals)-1)

    fig = make_subplots(1, 2, subplot_titles=["ζ(½+it) in ℂ", "|ζ(½+it)| vs t"])
    # Left
    fig.add_trace(go.Scatter(x=zv.real, y=zv.imag, mode="lines",
                             line=dict(color="#00BFFF", width=0.8), opacity=0.2,
                             showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=zv[:idx+1].real, y=zv[:idx+1].imag, mode="lines",
                             line=dict(color="#00BFFF", width=2), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=[zv[idx].real], y=[zv[idx].imag], mode="markers",
                             marker=dict(color="#FF8C00", size=10), name="current"), row=1, col=1)
    fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers",
                             marker=dict(symbol="cross", color="white", size=12, line=dict(width=2)),
                             name="origin"), row=1, col=1)
    # Right
    mod = np.abs(zv)
    fig.add_trace(go.Scatter(x=t_vals, y=mod, mode="lines",
                             line=dict(color="#00BFFF", width=1.5), showlegend=False), row=1, col=2)
    for z in zeros:
        fig.add_vline(x=z.imag, line=dict(color="red", dash="dash", width=1), opacity=0.5, row=1, col=2)
    fig.add_vline(x=t_cursor, line=dict(color="#FF8C00", width=2), row=1, col=2)

    fig.update_layout(**DARK, title="Riemann ζ(s) — Critical Line Re(s) = ½")
    return fig


def _fig_strip(im_max, res):
    from mathplt.math.zeta import zeta_grid
    rp = max(20, min(res // 3, 60))
    ip = max(50, min(res, 200))
    RE, IM, Z = zeta_grid(re_range=(0.02, 0.98), im_range=(0.5, im_max),
                           re_points=rp, im_points=ip, dps=25)
    Z_t = Z.T
    re_vals = np.linspace(0.02, 0.98, rp)
    im_vals = np.linspace(0.5, im_max, ip)
    mag = np.log1p(np.abs(Z_t))
    phase = np.angle(Z_t)

    fig = make_subplots(1, 2, subplot_titles=["log(1+|ζ(s)|)", "arg(ζ(s))"])
    fig.add_trace(go.Heatmap(x=re_vals, y=im_vals, z=mag, colorscale="inferno",
                             showscale=False), row=1, col=1)
    fig.add_trace(go.Heatmap(x=re_vals, y=im_vals, z=phase, colorscale="hsv",
                             zmin=-np.pi, zmax=np.pi, showscale=False), row=1, col=2)
    for col in (1, 2):
        fig.add_vline(x=0.5, line=dict(color="cyan", dash="dash", width=1.5), row=1, col=col)
    fig.update_layout(**DARK, title="ζ(s) over Critical Strip  0 < Re(s) < 1")
    return fig


def _fig_winding(im_top, n_zeros):
    from mathplt.math.zeta import zeta_on_contour, find_zeros_on_critical_line
    im_top = max(im_top, 2.0)
    n = 80
    re_lo, re_hi = 0.1, 0.9
    bottom = np.linspace(re_lo, re_hi, n) + 0.5j
    right  = re_hi + 1j*np.linspace(0.5, im_top, n)
    top    = np.linspace(re_hi, re_lo, n) + 1j*im_top
    left   = re_lo + 1j*np.linspace(im_top, 0.5, n)
    contour = np.concatenate([bottom, right, top, left, [bottom[0]]])
    w = zeta_on_contour(contour, dps=25)
    zeros = find_zeros_on_critical_line(n_zeros=n_zeros, dps=30)
    n_enc = sum(1 for z in zeros if z.imag < im_top)
    fw = w[np.isfinite(w)]
    winding = float(np.sum(np.diff(np.unwrap(np.angle(fw))))) / (2*np.pi) if len(fw) > 2 else 0.0

    fig = make_subplots(1, 2, subplot_titles=["s-plane contour", f"ζ(C) — winding ≈ {winding:.1f}"])
    fig.add_trace(go.Scatter(x=contour.real, y=contour.imag, mode="lines",
                             line=dict(color="#FF8C00", width=2), showlegend=False), row=1, col=1)
    for z in zeros:
        col = "red" if z.imag < im_top else "#444"
        fig.add_trace(go.Scatter(x=[0.5], y=[z.imag], mode="markers",
                                 marker=dict(symbol="x", color=col, size=8),
                                 showlegend=False), row=1, col=1)
    fig.add_vline(x=0.5, line=dict(color="cyan", dash="dash", width=1), row=1, col=1)
    fig.add_trace(go.Scatter(x=fw.real, y=fw.imag, mode="lines",
                             line=dict(color="#FF8C00", width=2), showlegend=False), row=1, col=2)
    fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers",
                             marker=dict(symbol="cross", color="white", size=14, line=dict(width=2)),
                             showlegend=False), row=1, col=2)
    fig.update_layout(**DARK, title=f"Argument Principle — zeros enclosed: {n_enc}")
    return fig


if __name__ == "__main__":
    app.run(debug=True, port=8050)
