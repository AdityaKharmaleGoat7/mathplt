"""Manifold web app — run with: python -m webapp.app"""

import dash
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, ctx, dcc, html, no_update
from plotly.subplots import make_subplots

from manifold.core.equation_parser import EquationParser

app = dash.Dash(__name__, title="Manifold", suppress_callback_exceptions=True)
_parser = EquationParser()


# ── Linear transform helpers ─────────────────────────────────────────────────

def _parse_matrix(text: str) -> np.ndarray:
    """Parse '1, 0; 0, 1' → np.array([[1, 0], [0, 1]])."""
    rows = [r.strip() for r in text.split(";") if r.strip()]
    return np.array([[float(x) for x in row.split(",")] for row in rows])


def _parse_vector(text: str):
    """Parse '1, 2' → np.array([1, 2]) or None if empty."""
    if not text or not text.strip():
        return None
    return np.array([float(x) for x in text.split(",")])

# ── Inject dark-mode CSS for Dash dropdowns and scrollbars ────────────────────
app.index_string = """<!DOCTYPE html>
<html>
  <head>
    {%metas%}<title>{%title%}</title>{%favicon%}{%css%}
    <style>
      /* ── Scrollbar ──────────────────────────────────────────── */
      ::-webkit-scrollbar { width: 6px; }
      ::-webkit-scrollbar-track { background: #0d1117; }
      ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
      ::-webkit-scrollbar-thumb:hover { background: #484f58; }

      /* ── Dash dcc.Dropdown dark theme ───────────────────────── */
      .Select-control {
        background-color: #0d1117 !important;
        border-color: #30363d !important;
      }
      .Select-control:hover { border-color: #58a6ff !important; }
      .Select-value-label, .Select-input input, .Select-placeholder {
        color: #e6edf3 !important;
      }
      .Select-placeholder { color: #484f58 !important; }
      .Select-arrow-zone .Select-arrow { border-top-color: #8b949e !important; }
      .is-open .Select-arrow { border-bottom-color: #8b949e !important; }
      .Select-menu-outer {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5) !important;
        z-index: 9999 !important;
      }
      .Select-option {
        background-color: #161b22 !important;
        color: #c9d1d9 !important;
        font-size: 13px;
        padding: 8px 12px !important;
      }
      .Select-option:hover,
      .Select-option.is-focused {
        background-color: #21262d !important;
        color: #e6edf3 !important;
      }
      .Select-option.is-selected {
        background-color: #1f3a5f !important;
        color: #58a6ff !important;
        font-weight: 600;
      }
      .Select-option.is-disabled {
        color: #30363d !important;
        font-style: italic;
        font-size: 11px !important;
        padding: 4px 10px !important;
        cursor: default !important;
        pointer-events: none;
      }
      .Select-multi-value-wrapper { color: #e6edf3 !important; }
      .Select-noresults { color: #8b949e !important; background: #161b22 !important; }

      /* ── Number inputs ──────────────────────────────────────── */
      input[type=number] { color-scheme: dark; }
      input[type=number]::-webkit-inner-spin-button { opacity: 0.4; }

      /* ── Slider tooltip ─────────────────────────────────────── */
      .rc-slider-tooltip-inner {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        color: #e6edf3 !important;
        font-size: 11px !important;
      }
      .rc-slider-tooltip-arrow { border-top-color: #30363d !important; }

      /* ── Global text ────────────────────────────────────────── */
      body { background: #0d1117; color: #e6edf3; margin: 0; }

      /* ── Preset buttons ─────────────────────────────────────── */
      .preset-btn {
        background: #21262d;
        color: #7ee787;
        border: 1px solid #30363d;
        border-radius: 4px;
        padding: 3px 8px;
        font-family: monospace;
        font-size: 11px;
        cursor: pointer;
        transition: all 0.15s ease;
        white-space: nowrap;
      }
      .preset-btn:hover {
        background: #1f3a5f;
        border-color: #58a6ff;
        color: #e6edf3;
      }

      /* ── Play/Stop button hover states ──────────────────────── */
      .play-btn:hover { filter: brightness(1.15); }
      .stop-btn:hover { background: #30363d !important; color: #e6edf3 !important; }
    </style>
  </head>
  <body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
  </body>
</html>
"""

# ── Dark theme template ────────────────────────────────────────────────────────
DARK = dict(
    template="plotly_dark",
    paper_bgcolor="#0d1117",
    plot_bgcolor="#161b22",
    font=dict(color="#e6edf3"),
    margin=dict(l=50, r=20, t=50, b=50),
    uirevision="keep",
)

# ── Shared style constants ─────────────────────────────────────────────────────
_CARD  = {"background": "#161b22", "border": "1px solid #30363d",
          "borderRadius": "8px", "padding": "12px 14px", "marginBottom": "10px"}
_SEC   = {"fontSize": "10px", "fontWeight": "700", "color": "#58a6ff",
          "textTransform": "uppercase", "letterSpacing": "0.08em", "marginBottom": "10px"}
_LBL   = {"color": "#8b949e", "fontSize": "11px", "fontWeight": "600",
          "marginBottom": "4px", "display": "block"}
_HINT  = {"color": "#6e7681", "fontSize": "10px", "marginTop": "3px", "marginBottom": "8px"}
_INPUT = {"width": "100%", "boxSizing": "border-box",
          "background": "#0d1117", "color": "#e6edf3",
          "border": "1px solid #30363d", "borderRadius": "6px",
          "padding": "8px 10px", "fontFamily": "monospace", "fontSize": "13px",
          "marginBottom": "4px"}

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

# ── Layout ─────────────────────────────────────────────────────────────────────
app.layout = html.Div(style={
    "display": "flex", "height": "100vh", "background": "#0d1117",
    "color": "#e6edf3", "fontFamily": "monospace", "overflow": "hidden",
}, children=[

        # ── Sidebar ───────────────────────────────────────────────────────────
        html.Div(style={
            "width": "310px", "minWidth": "310px", "padding": "14px 12px",
            "borderRight": "1px solid #30363d", "overflowY": "auto",
            "background": "#0d1117", "display": "flex", "flexDirection": "column",
        }, children=[

            # Brand
            html.Div(style={"marginBottom": "16px", "textAlign": "center"}, children=[
                html.Img(src="/assets/logo.png", style={
                    "width": "64px", "height": "64px",
                    "marginBottom": "8px", "opacity": "0.95",
                }),
                html.Div(style={
                    "display": "flex", "alignItems": "baseline",
                    "justifyContent": "center", "gap": "8px",
                }, children=[
                    html.Span("Manifold", style={
                        "color": "#58a6ff", "fontSize": "22px",
                        "fontWeight": "700", "letterSpacing": "0.02em",
                    }),
                    html.Span("v0.1", style={
                        "color": "#484f58", "fontSize": "11px",
                    }),
                ]),
                html.Div("Own the space", style={
                    "color": "#8b949e", "fontSize": "11px",
                    "marginTop": "3px", "fontStyle": "italic",
                    "letterSpacing": "0.12em",
                }),
            ]),

            # ── Mode selector ─────────────────────────────────────────────────
            html.Div(style=_CARD, children=[
                html.Div("Visualization mode", style=_SEC),
                dcc.Dropdown(id="anim-type", value="graph2d", clearable=False,
                    options=[
                        {"label": "2D Graph  --  f(x, t)",             "value": "graph2d"},
                        {"label": "3D Surface  --  f(x, y)",           "value": "graph3d"},
                        {"label": "Complex Plane  --  f(z)",           "value": "complex"},
                        {"label": "--- Riemann zeta ----------",       "value": "_sep", "disabled": True},
                        {"label": "  Zeros on critical line",          "value": "riemann.zeros"},
                        {"label": "  Critical strip heatmap",          "value": "riemann.critical_strip"},
                        {"label": "  Winding number",                  "value": "riemann.winding"},
                        {"label": "  Evaluate zeta(a + ib)",           "value": "riemann.point"},
                        {"label": "--- Linear algebra ---------",  "value": "_sep2", "disabled": True},
                        {"label": "  Linear transformation",       "value": "linear_transform"},
                    ],
                    style={"fontSize": "13px"},
                ),
            ]),

            # ── Equation ──────────────────────────────────────────────────────
            html.Div(id="eq-section", style=_CARD, children=[
                html.Div("Equation", id="eq-title", style=_SEC),
                dcc.Input(id="equation", type="text", debounce=True,
                    value="sin(x + t) * exp(-0.1 * x**2)",
                    placeholder="e.g. sin(x + t) * exp(-0.1 * x**2)",
                    style=_INPUT,
                ),
                html.Div(id="eq-status", style={"fontSize": "11px", "color": "#8b949e"},
                         children="Press Enter to apply"),
                html.Div("Use x, t for 2D  |  x, y for 3D  |  z, t for complex",
                         id="eq-hint", style=_HINT),
                # Preset buttons
                html.Div("Quick presets", style={**_LBL, "marginTop": "6px"}),
                html.Div(id="preset-container", style={
                    "display": "flex", "flexWrap": "wrap", "gap": "4px",
                }),
            ]),

            # ── Hidden range inputs (kept for callback compatibility) ─────────
            html.Div(id="xrange-section", style={"display": "none"}, children=[
                dcc.RangeSlider(id="xrange", min=-20, max=20, step=1, value=[-10, 10],
                    marks={-20: "-20", 0: "0", 20: "20"},
                    tooltip={"placement": "bottom", "always_visible": False}),
            ]),
            html.Div(id="yrange-section", style={"display": "none"}, children=[
                dcc.RangeSlider(id="yrange", min=-20, max=20, step=1, value=[-5, 5],
                    marks={-20: "-20", 0: "0", 20: "20"},
                    tooltip={"placement": "bottom", "always_visible": False}),
            ]),
            html.Div(id="complex-section", style={"display": "none"}, children=[
                dcc.RangeSlider(id="rerange", min=-8, max=8, step=0.5, value=[-3, 3],
                    marks={-8: "-8", 0: "0", 8: "8"},
                    tooltip={"placement": "bottom", "always_visible": False}),
                dcc.RangeSlider(id="imrange", min=-8, max=8, step=0.5, value=[-3, 3],
                    marks={-8: "-8", 0: "0", 8: "8"},
                    tooltip={"placement": "bottom", "always_visible": False}),
            ]),

            # ── Time slider ───────────────────────────────────────────────────
            html.Div(id="t-section", style=_CARD, children=[
                html.Div("Time  t", style=_SEC),
                dcc.Slider(id="tval", min=0, max=20, step=0.05, value=0,
                    marks={0: "0", 5: "5", 10: "10", 15: "15", 20: "20"},
                    tooltip={"placement": "bottom", "always_visible": True}),
                html.Div("Drag to scrub  |  use Play below to animate", style=_HINT),
            ]),

            # ── Display settings ──────────────────────────────────────────────
            html.Div(style=_CARD, children=[
                html.Div("Display", style=_SEC),
                html.Span("Resolution", style=_LBL),
                dcc.Slider(id="resolution", min=30, max=300, step=10, value=150,
                    marks={30: "lo", 150: "mid", 300: "hi"},
                    tooltip={"placement": "bottom", "always_visible": True}),
                html.Div("Higher = sharper but slower to compute", style=_HINT),
                html.Div(id="cmap-section", children=[
                    html.Span("Colormap", style=_LBL),
                    dcc.Dropdown(id="colormap", value="viridis", clearable=False,
                        options=[{"label": c, "value": c} for c in
                                 ["viridis", "plasma", "inferno", "magma", "turbo", "RdBu", "Spectral"]],
                        style={"fontSize": "13px"},
                    ),
                ]),
            ]),

            # ── Riemann controls ──────────────────────────────────────────────
            html.Div(id="riemann-section", style={**_CARD, "display": "none"}, children=[
                html.Div("Riemann parameters", style=_SEC),
                html.Span("Zeros to find", style=_LBL),
                dcc.Slider(id="nzeros", min=5, max=25, step=1, value=12,
                    marks={5: "5", 15: "15", 25: "25"},
                    tooltip={"placement": "bottom", "always_visible": True}),
                html.Div("More zeros = slower computation", style=_HINT),
                html.Span("Im(s) max  --  height of plot", style=_LBL),
                dcc.Slider(id="imsmax", min=5, max=60, step=1, value=40,
                    marks={5: "5", 20: "20", 40: "40", 60: "60"},
                    tooltip={"placement": "bottom", "always_visible": True}),
                html.Div(style={"height": "4px"}),
                html.Span("Winding contour top", style=_LBL),
                dcc.Slider(id="windtop", min=2, max=45, step=0.5, value=15,
                    marks={2: "2", 15: "15", 30: "30", 45: "45"},
                    tooltip={"placement": "bottom", "always_visible": True}),
                html.Div("Raise to enclose more zeros in contour", style=_HINT),
            ]),

            # ── Evaluate zeta(a + ib) ─────────────────────────────────────────
            html.Div(id="point-section", style={**_CARD, "display": "none"}, children=[
                html.Div("Evaluate  zeta(a + ib)", style=_SEC),
                html.Div(style={"display": "flex", "gap": "8px", "marginBottom": "4px"}, children=[
                    html.Div(style={"flex": 1}, children=[
                        html.Span("Re(s) = a", style=_LBL),
                        dcc.Input(id="zeta-a", type="number", value=0.5, step=0.1, debounce=True,
                            style={**_INPUT, "marginBottom": "0"}),
                    ]),
                    html.Div(style={"flex": 1}, children=[
                        html.Span("Im(s) = b", style=_LBL),
                        dcc.Input(id="zeta-b", type="number", value=14.135, step=0.5, debounce=True,
                            style={**_INPUT, "marginBottom": "0"}),
                    ]),
                ]),
                html.Div("Try a=0.5, b=14.135 -- the first zero", style=_HINT),
                html.Pre(id="zeta-value", style={
                    "background": "#0d1117", "border": "1px solid #238636",
                    "borderRadius": "6px", "padding": "10px", "fontSize": "12px",
                    "color": "#7ee787", "fontFamily": "monospace",
                    "margin": "0", "whiteSpace": "pre",
                }),
            ]),

            # ── Linear transform controls ─────────────────────────────────────
            html.Div(id="linear-section", style={**_CARD, "display": "none"}, children=[
                html.Div("Dimension", style=_SEC),
                dcc.RadioItems(
                    id="linear-dim", value="2D",
                    options=[{"label": "2D", "value": "2D"}, {"label": "3D", "value": "3D"}],
                    inline=True,
                    inputStyle={"marginRight": "4px"},
                    labelStyle={"marginRight": "16px", "fontSize": "13px", "color": "#c9d1d9"},
                    style={"marginBottom": "8px"},
                ),
                html.Span("Vector (optional)", style=_LBL),
                dcc.Input(
                    id="vector-input", type="text", debounce=True,
                    placeholder="e.g. 1, 2",
                    style=_INPUT,
                ),
                html.Div("Enter components separated by commas", style=_HINT),
            ]),

            # ── Animation controls ────────────────────────────────────────────
            html.Div(id="anim-section", style=_CARD, children=[
                html.Div("Animation", style=_SEC),
                html.Div(style={"display": "flex", "gap": "6px", "marginBottom": "10px"}, children=[
                    html.Button("Play", id="play-btn", n_clicks=0, className="play-btn", style={
                        "flex": 2, "background": "#238636", "color": "white",
                        "border": "none", "borderRadius": "6px", "padding": "10px",
                        "cursor": "pointer", "fontSize": "14px", "fontWeight": "600",
                        "letterSpacing": "0.05em",
                    }),
                    html.Button("Stop", id="stop-btn", n_clicks=0, className="stop-btn", style={
                        "flex": 1, "background": "#21262d", "color": "#8b949e",
                        "border": "1px solid #30363d", "borderRadius": "6px", "padding": "10px",
                        "cursor": "pointer", "fontSize": "13px",
                    }),
                ]),
                html.Div(style={"display": "flex", "justifyContent": "space-between",
                                "marginBottom": "2px"}, children=[
                    html.Span("Speed", style={"color": "#8b949e", "fontSize": "11px"}),
                    html.Span("slow ---- fast", style={"color": "#6e7681", "fontSize": "10px"}),
                ]),
                dcc.Slider(id="speed", min=30, max=500, step=10, value=80,
                    marks={30: "fast", 250: "med", 500: "slow"},
                    tooltip={"placement": "bottom", "always_visible": False}),
            ]),

            # ── Info panel ────────────────────────────────────────────────────
            html.Hr(style={"borderColor": "#21262d", "margin": "6px 0 10px 0"}),
            html.Div(id="info-panel"),

            # ── Footer ───────────────────────────────────────────────────────
            html.Div(style={
                "marginTop": "auto", "paddingTop": "16px",
                "borderTop": "1px solid #21262d",
                "fontSize": "10px", "color": "#484f58", "lineHeight": "1.8",
                "textAlign": "center",
            }, children=[
                html.Img(src="/assets/logo.png", style={
                    "width": "20px", "height": "20px",
                    "verticalAlign": "middle", "marginRight": "6px",
                    "opacity": "0.5",
                }),
                html.Span("Manifold", style={
                    "verticalAlign": "middle", "fontWeight": "600",
                }),
                html.Div("Own the space", style={
                    "color": "#30363d", "fontSize": "9px",
                    "fontStyle": "italic", "marginTop": "2px",
                }),
            ]),
        ]),

        # ── Main graph area ───────────────────────────────────────────────────
        html.Div(style={"flex": 1, "overflow": "hidden", "position": "relative"}, children=[
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
    Output("point-section",   "style"),
    Output("linear-section",  "style"),
    Input("anim-type", "value"),
)
def show_controls(anim):
    show = {"display": "block"}
    hide = {"display": "none"}
    is_lt = anim == "linear_transform"
    eq      = {**_CARD} if anim in ("graph2d", "graph3d", "complex") or is_lt else hide
    xrange  = hide
    yrange  = hide
    cplx    = hide
    t       = {**_CARD} if anim in ("graph2d", "graph3d", "complex", "riemann.zeros") or is_lt else hide
    cmap    = show if anim in ("graph3d", "complex") else hide
    riemann = {**_CARD} if anim.startswith("riemann") and anim != "riemann.point" else hide
    anim_s  = {**_CARD} if anim in ("graph2d", "graph3d", "complex", "riemann.zeros") or is_lt else hide
    point   = {**_CARD} if anim == "riemann.point" else hide
    linear  = {**_CARD} if is_lt else hide
    return eq, xrange, yrange, cplx, t, cmap, riemann, anim_s, point, linear


# Update eq section labels for linear transform mode
@app.callback(
    Output("eq-title", "children"),
    Output("eq-hint",  "children"),
    Input("anim-type", "value"),
)
def update_eq_labels(anim):
    if anim == "linear_transform":
        return "Transformation Matrix", "Rows separated by ;  e.g. 1, 0; 0, 1"
    return "Equation", "Use x, t for 2D  |  x, y for 3D  |  z, t for complex"


# Populate preset buttons based on mode
@app.callback(
    Output("preset-container", "children"),
    Input("anim-type", "value"),
    Input("linear-dim", "value"),
)
def update_presets(anim, dim):
    if anim == "linear_transform":
        key = f"linear_transform_{(dim or '2D').lower()}"
        presets = _PRESETS.get(key, [])
        labels = _PRESET_LABELS.get(key, presets)
        return [
            html.Button(
                labels[i] if i < len(labels) else eq,
                id={"type": "preset-btn", "index": i},
                className="preset-btn", n_clicks=0,
            )
            for i, eq in enumerate(presets)
        ]
    presets = _PRESETS.get(anim, [])
    return [
        html.Button(
            eq, id={"type": "preset-btn", "index": i},
            className="preset-btn",
            n_clicks=0,
        )
        for i, eq in enumerate(presets)
    ]


# Preset button click → set equation
@app.callback(
    Output("equation", "value"),
    Input({"type": "preset-btn", "index": dash.ALL}, "n_clicks"),
    State("anim-type", "value"),
    State("linear-dim", "value"),
    prevent_initial_call=True,
)
def apply_preset(clicks, anim, dim):
    if not ctx.triggered_id or not any(c for c in clicks if c):
        return no_update
    idx = ctx.triggered_id["index"]
    if anim == "linear_transform":
        key = f"linear_transform_{(dim or '2D').lower()}"
    else:
        key = anim
    presets = _PRESETS.get(key, [])
    if idx < len(presets):
        return presets[idx]
    return no_update


# Equation validation
@app.callback(
    Output("eq-status", "children"),
    Output("eq-status", "style"),
    Input("equation", "value"),
    State("anim-type", "value"),
    prevent_initial_call=True,
)
def validate_eq(expr, anim):
    ok_style = {"fontSize": "11px", "color": "#69db7c", "marginBottom": "12px"}
    err_style = {"fontSize": "11px", "color": "#ff6b6b", "marginBottom": "12px"}
    if not expr:
        return "Empty equation.", err_style
    if anim == "linear_transform":
        try:
            M = _parse_matrix(expr)
            r, c = M.shape
            if r != c or r not in (2, 3):
                return f"Need 2x2 or 3x3 matrix, got {r}x{c}", err_style
            det = float(np.linalg.det(M))
            return f"Valid {r}x{r} matrix  |  det = {det:.3g}", ok_style
        except Exception as e:
            return f"Invalid matrix: {e}", err_style
    vars_map = {"graph2d": {"x","t"}, "graph3d": {"x","y"}, "complex": {"z","t"}}
    err = _parser.validate(expr, variables=vars_map.get(anim, {"x","t"}))
    if err:
        return f"Invalid: {err}", err_style
    return "Valid", ok_style


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
    base = {"flex": 2, "color": "white", "border": "none", "borderRadius": "6px",
            "padding": "10px", "cursor": "pointer", "fontSize": "14px", "fontWeight": "600",
            "letterSpacing": "0.05em"}
    if ctx.triggered_id == "stop-btn":
        return True, "Play", {**base, "background": "#238636"}
    now_playing = is_disabled
    if now_playing:
        return False, "Pause", {**base, "background": "#b08800"}
    else:
        return True,  "Play",  {**base, "background": "#238636"}


# Speed slider -> interval
@app.callback(Output("interval", "interval"), Input("speed", "value"))
def set_speed(ms): return ms or 80


# Info panel content per animation type
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


@app.callback(Output("info-panel", "children"), Input("anim-type", "value"))
def update_info(anim):
    info = _INFO.get(anim)
    if not info:
        return []

    children = [
        html.Div(style=_CARD, children=[
            html.Div(info["title"], style={"margin": "0 0 6px 0", "fontSize": "12px",
                                           "fontWeight": "700", "color": "#e6edf3"}),
            html.P(info["desc"], style={"margin": "0", "color": "#8b949e",
                                        "fontSize": "11px", "lineHeight": "1.6"}),
        ]),
    ]

    for section_title, rows in info["sections"]:
        children.append(html.Div(style=_CARD, children=[
            html.Div(section_title, style=_SEC),
            _info_table(rows),
        ]))

    return children


# Interval -> advance t
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
    if anim in ("graph2d", "graph3d", "complex"):
        return round((t + 0.12) % 20.0, 3)
    if anim == "riemann.zeros":
        return round((t + 0.2) % float(imsmax or 40), 3)
    if anim == "linear_transform":
        return round((t + 0.015) % 4.0, 3)
    return t


# Main graph update
@app.callback(
    Output("graph",      "figure"),
    Output("zeta-value", "children"),
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
    Input("zeta-a",     "value"),
    Input("zeta-b",     "value"),
    Input("linear-dim",    "value"),
    Input("vector-input",  "value"),
)
def update_graph(anim, eq, xr, yr, rer, imr, t, res, cmap, nz, imsmax, windtop, za, zb,
                 lin_dim, vec_str):
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
    za      = float(za) if za is not None else 0.5
    zb      = float(zb) if zb is not None else 14.135

    try:
        if anim == "graph2d":
            return _fig_2d(eq, t, res), ""
        if anim == "graph3d":
            return _fig_3d(eq, res, cmap, t), ""
        if anim == "complex":
            return _fig_complex(eq, rer, imr, res, t), ""
        if anim == "riemann.zeros":
            return _fig_zeros(imsmax, nz, res, t), ""
        if anim == "riemann.critical_strip":
            return _fig_strip(imsmax, res), ""
        if anim == "riemann.winding":
            return _fig_winding(windtop, nz), ""
        if anim == "riemann.point":
            return _fig_point(za, zb, res)
        if anim == "linear_transform":
            return _fig_linear_transform(eq, t, lin_dim, vec_str), ""
    except Exception as e:
        fig = go.Figure()
        fig.update_layout(**DARK,
                          title=dict(text=f"Error: {e}", font=dict(color="#ff6b6b")))
        fig.add_annotation(
            text=str(e), xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=14, color="#ff6b6b"),
        )
        return fig, ""

    fig = go.Figure()
    fig.update_layout(**DARK)
    return fig, ""


# ── Figure builders ────────────────────────────────────────────────────────────

def _fig_2d(eq, t, res):
    f = _parser.parse_xt(eq)
    x = np.linspace(-20, 20, res * 2)
    y = np.where(np.isfinite(y := f(x, t)), y, np.nan)
    fig = go.Figure(go.Scatter(x=x, y=y, mode="lines",
                               line=dict(color="#00BFFF", width=2.5)))
    fig.add_hline(y=0, line=dict(color="gray", width=0.5, dash="dot"))
    fig.update_layout(**DARK, title=f"f(x,t) = {eq}   [t = {t:.2f}]",
                      xaxis=dict(title="x", autorange=True),
                      yaxis=dict(title="f(x, t)", autorange=True),
                      dragmode="pan")
    return fig


def _fig_3d(eq, res, cmap, t):
    f = _parser.parse_xy(eq)
    x = np.linspace(-6, 6, res)
    y = np.linspace(-6, 6, res)
    X, Y = np.meshgrid(x, y)
    Z = f(X, Y).astype(float)
    Z[~np.isfinite(Z)] = np.nan
    angle = t * 0.3
    camera = dict(eye=dict(x=2.0 * np.cos(angle), y=2.0 * np.sin(angle), z=0.8))
    fig = go.Figure(go.Surface(x=X, y=Y, z=Z, colorscale=cmap, opacity=0.95))
    fig.update_layout(**DARK, title=f"f(x,y) = {eq}",
                      scene=dict(xaxis_title="x", yaxis_title="y", zaxis_title="f",
                                 camera=camera))
    return fig


def _fig_complex(eq, _rer, _imr, res, t):
    import base64
    import io

    import matplotlib.image as mpimg

    from manifold.math.complex_ops import complex_grid, domain_color_fast

    R  = 20.0
    hi = min(res * 4, 1200)
    Z  = complex_grid((-R, R), (-R, R), re_n=hi, im_n=hi)

    has_t = "t" in eq
    if has_t:
        from manifold.core.equation_parser import ALLOWED_NAMES, _validate_ast
        _validate_ast(eq, extra_vars={"z", "t"})
        ns = dict(ALLOWED_NAMES)
        code = compile(eq, "<eq>", "eval")
        W = eval(code, {"__builtins__": {}}, dict(ns, z=Z, t=t))
    else:
        W = _parser.parse_complex(eq)(Z)

    # Mask infinities from poles (e.g. 1/z at origin)
    W = np.where(np.isfinite(W), W, np.nan + 0j)
    rgb = (domain_color_fast(W, brightness_cycles=1.0, z_input=Z) * 255).astype(np.uint8)

    buf = io.BytesIO()
    mpimg.imsave(buf, rgb[::-1], format="png")
    src = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    tick_z  = np.arange(-20, 21, 5, dtype=float)
    tick_px = (tick_z + R) / (2 * R) * (hi - 1)
    tick_labels = [str(int(v)) for v in tick_z]

    fig = go.Figure()
    fig.add_layout_image(dict(
        source=src,
        xref="x", yref="y",
        x=0, y=hi,
        sizex=hi, sizey=hi,
        sizing="stretch",
        opacity=1,
        layer="below",
    ))

    ax_style = dict(
        range=[0, hi],
        tickvals=tick_px, ticktext=tick_labels,
        tickfont=dict(color="#8b949e", size=10),
        tickcolor="#30363d", ticklen=4,
        showgrid=False, zeroline=False,
        linecolor="#30363d", linewidth=1, showline=True,
    )
    fig.update_xaxes(**ax_style, title=dict(text="Re(z)", font=dict(color="#8b949e", size=12)))
    fig.update_yaxes(**ax_style, title=dict(text="Im(z)", font=dict(color="#8b949e", size=12)))

    title = f"f(z) = {eq}" + (f"   t = {t:.2f}" if has_t else "")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="#e6edf3"),
        margin=dict(l=55, r=10, t=36, b=50),
        uirevision="keep",
        title=dict(text=title, x=0.5, xanchor="center",
                   font=dict(size=13, color="#8b949e")),
    )
    return fig


def _fig_point(a: float, b: float, res: int):
    """
    Visualize zeta(a + it) with the specific point s = a + ib highlighted.
    Returns (figure, value_string) matching the two Outputs.
    """
    from manifold.math.zeta import find_zeros_on_critical_line, zeta_on_contour

    half = max(25.0, abs(b) * 0.6)
    t_min = max(0.5, b - half)
    t_max = b + half
    n_pts = max(res * 4, 400)
    t_vals = np.linspace(t_min, t_max, n_pts)

    s_vals = (a + 1j * t_vals).astype(complex)
    zv = zeta_on_contour(s_vals, dps=25)

    # Value at the specific point -- reuse the precomputed path
    idx_closest = int(np.argmin(np.abs(t_vals - b)))
    w_pt = zv[idx_closest]
    re_w, im_w, mag_w = w_pt.real, w_pt.imag, abs(w_pt)
    value_str = (
        f"s = {a:.4g} + {b:.4g}i\n"
        f"zeta(s) = {re_w:.6g} + {im_w:.6g}i\n"
        f"|zeta(s)| = {mag_w:.6g}"
    )

    try:
        zeros = find_zeros_on_critical_line(n_zeros=15, dps=30)
        zero_t = [z.imag for z in zeros if t_min <= z.imag <= t_max]
    except Exception:
        zero_t = []

    fig = make_subplots(
        1, 2,
        subplot_titles=[
            f"Path of zeta({a:.3g}+it) in C",
            f"|zeta({a:.3g}+it)| vs t",
        ],
        horizontal_spacing=0.1,
    )

    # Left: complex path
    fig.add_trace(go.Scatter(
        x=zv.real, y=zv.imag, mode="lines",
        line=dict(color="#00BFFF", width=1), opacity=0.25, showlegend=False,
    ), row=1, col=1)
    idx_b = int(np.searchsorted(t_vals, b))
    half_seg = max(n_pts // 6, 30)
    lo, hi = max(0, idx_b - half_seg), min(n_pts, idx_b + half_seg)
    fig.add_trace(go.Scatter(
        x=zv[lo:hi].real, y=zv[lo:hi].imag, mode="lines",
        line=dict(color="#00BFFF", width=2.5), showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=[w_pt.real], y=[w_pt.imag], mode="markers",
        marker=dict(color="#FF8C00", size=12, symbol="circle"),
        name=f"zeta({a:.3g}+{b:.3g}i)",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers",
        marker=dict(symbol="cross", color="white", size=14, line=dict(width=2)),
        name="origin (zero)",
    ), row=1, col=1)

    # Right: |zeta(a+it)| vs t
    mod = np.abs(zv)
    fig.add_trace(go.Scatter(
        x=t_vals, y=mod, mode="lines",
        line=dict(color="#00BFFF", width=1.8), showlegend=False,
    ), row=1, col=2)
    for zt in zero_t:
        fig.add_vline(x=zt, line=dict(color="red", dash="dash", width=1),
                      opacity=0.5, row=1, col=2)
    fig.add_vline(x=b, line=dict(color="#FF8C00", width=2.5), row=1, col=2)
    fig.add_trace(go.Scatter(
        x=[b], y=[mag_w], mode="markers",
        marker=dict(color="#FF8C00", size=10), showlegend=False,
    ), row=1, col=2)

    fig.update_layout(
        **DARK,
        title=(f"zeta(s) at s = {a:.4g} + {b:.4g}i  |  "
               f"zeta = {re_w:.5g} + {im_w:.5g}i  |  |zeta| = {mag_w:.5g}"),
    )
    fig.update_xaxes(title_text="Re(zeta)", row=1, col=1)
    fig.update_yaxes(title_text="Im(zeta)", row=1, col=1)
    fig.update_xaxes(title_text="t  (imaginary part)", row=1, col=2)
    fig.update_yaxes(title_text="|zeta(a+it)|", row=1, col=2)

    return fig, value_str


def _fig_linear_transform(eq, t, dim, vec_str):
    """Dispatch to 2D or 3D linear transform figure."""
    if (dim or "2D") == "3D":
        return _fig_linear_3d(eq, t, vec_str)
    return _fig_linear_2d(eq, t, vec_str)


def _fig_linear_2d(matrix_str, t, vec_str):
    """2D linear transformation — full dynamics visualization:
    phase portrait, trajectory curves, invariant curves, vector field,
    animated grid morphing, SVD ellipse axes, eigenvector lines."""
    try:
        M = _parse_matrix(matrix_str)
        if M.shape != (2, 2):
            raise ValueError(f"Expected 2x2, got {M.shape[0]}x{M.shape[1]}")
    except Exception as e:
        fig = go.Figure()
        fig.update_layout(**DARK, title=dict(text=f"Matrix error: {e}", font=dict(color="#ff6b6b")))
        return fig

    # Ping-pong interpolation: 0 → 1 → 0 over period 4
    frac = 1 - abs(2 * ((t % 4) / 4) - 1)
    I2 = np.eye(2)

    # ── Matrix logarithm for continuous flow M^t ─────────────────────────────
    # M^t = exp(t log M) gives geodesic interpolation (the "true" dynamics).
    # Falls back to linear interpolation when log(M) is complex or undefined.
    B = None  # generator: M = exp(B)
    try:
        from scipy.linalg import logm as _logm, expm as _expm
        B_cand = _logm(M.astype(complex))
        if np.all(np.abs(B_cand.imag) < 1e-8):
            B_real = B_cand.real
            if np.linalg.norm(B_real) > 1e-10:  # skip trivial (M ~ I)
                B = B_real
    except Exception:
        pass

    if B is not None:
        from scipy.linalg import expm as _expm
        Mt = _expm(frac * B)
    else:
        Mt = (1 - frac) * I2 + frac * M

    det_M = float(np.linalg.det(M))
    eigvals_M, eigvecs_M = np.linalg.eig(M)
    real_eig_mask = np.abs(eigvals_M.imag) < 1e-10
    eig_str = ", ".join(
        f"{v.real:.2g}{'+' if v.imag >= 0 else ''}{v.imag:.2g}i" if abs(v.imag) > 1e-10
        else f"{v.real:.2g}"
        for v in eigvals_M
    )
    U, S, _Vt = np.linalg.svd(Mt)

    # ── Flow trajectory helper (via eigendecomposition of B) ─────────────────
    flow_ok = False
    if B is not None:
        eig_B, P_B = np.linalg.eig(B)
        try:
            Pinv_B = np.linalg.inv(P_B)
            flow_ok = True
        except np.linalg.LinAlgError:
            pass

    def _flow(v0, t_arr):
        """Trajectory of v0 under exp(tB) for times in t_arr."""
        xi0 = Pinv_B @ v0
        return (P_B @ (xi0[:, None] * np.exp(np.outer(eig_B, t_arr)))).real

    fig = go.Figure()

    # ── 1. Vector field: instantaneous velocity log(M) * v ───────────────────
    #    At every grid point, draw a small arrow showing the flow direction.
    #    Trajectories follow these arrows — deeply satisfying to watch.
    if B is not None:
        import plotly.figure_factory as ff
        gxv = np.linspace(-4, 4, 9)
        gyv = np.linspace(-4, 4, 9)
        GXV, GYV = np.meshgrid(gxv, gyv)
        U_f = B[0, 0] * GXV + B[0, 1] * GYV
        V_f = B[1, 0] * GXV + B[1, 1] * GYV
        max_mag = np.max(np.sqrt(U_f**2 + V_f**2)) + 1e-10
        vf_scale = 0.6 / max_mag
        try:
            qfig = ff.create_quiver(
                GXV.ravel(), GYV.ravel(),
                (U_f * vf_scale).ravel(), (V_f * vf_scale).ravel(),
                scale=1, arrow_scale=0.4,
            )
            qt = qfig.data[0]
            qt.line = dict(color="rgba(100, 180, 255, 0.25)", width=1)
            qt.showlegend = True
            qt.name = "Velocity field log(A)*v"
            qt.hoverinfo = "skip"
            fig.add_trace(qt)
        except Exception:
            pass

    # ── 2. Invariant curves: conserved quantity level sets ────────────────────
    #    For saddle/node: H = mu2 ln|xi1| - mu1 ln|xi2|  (hyperbolas etc.)
    #    For center (rotation): H = x^2 + y^2  (circles)
    if flow_ok:
        eig_B_r = eig_B.real if all(abs(v.imag) < 1e-10 for v in eig_B) else None
        inv_drawn = False

        if eig_B_r is not None:
            mu1, mu2 = eig_B_r
            if abs(mu1) > 1e-10 and abs(mu2) > 1e-10 and abs(mu1 - mu2) > 1e-10:
                # Saddle or node — compute H in eigenbasis of B
                P_Br = P_B.real
                Pinv_Br = np.linalg.inv(P_Br)
                gi = np.linspace(-4.8, 4.8, 120)
                GXI, GYI = np.meshgrid(gi, gi)
                xi = Pinv_Br @ np.array([GXI.ravel(), GYI.ravel()])
                with np.errstate(divide="ignore", invalid="ignore"):
                    H = mu2 * np.log(np.abs(xi[0]) + 1e-15) - mu1 * np.log(np.abs(xi[1]) + 1e-15)
                H = H.reshape(GXI.shape)
                H_fin = H[np.isfinite(H)]
                if len(H_fin) > 100:
                    lo, hi = np.percentile(H_fin, [8, 92])
                    levels = np.linspace(lo, hi, 14)
                    # Extract contour paths via matplotlib (computation only)
                    import matplotlib
                    matplotlib.use('Agg')
                    import matplotlib.pyplot as _plt
                    _fig_tmp, _ax_tmp = _plt.subplots()
                    cs = _ax_tmp.contour(GXI, GYI, H, levels=levels)
                    _plt.close(_fig_tmp)
                    x_inv, y_inv = [], []
                    for path in cs.get_paths():
                        v = path.vertices
                        if len(v) > 3:
                            x_inv.extend(list(v[:, 0]) + [None])
                            y_inv.extend(list(v[:, 1]) + [None])
                    if x_inv:
                        fig.add_trace(go.Scatter(
                            x=x_inv, y=y_inv, mode="lines",
                            line=dict(color="rgba(150,130,255,0.2)", width=1, dash="dot"),
                            name="Invariant curves",
                            hoverinfo="skip",
                        ))
                        inv_drawn = True

        if not inv_drawn and eig_B_r is None:
            # Check for center (pure rotation): eigenvalues of B are +/- iw
            if all(abs(v.real) < 1e-10 and abs(v.imag) > 1e-10 for v in eig_B):
                theta_c = np.linspace(0, 2 * np.pi, 100)
                x_inv, y_inv = [], []
                for r in np.arange(0.5, 4.5, 0.5):
                    x_inv.extend(list(r * np.cos(theta_c)) + [None])
                    y_inv.extend(list(r * np.sin(theta_c)) + [None])
                fig.add_trace(go.Scatter(
                    x=x_inv, y=y_inv, mode="lines",
                    line=dict(color="rgba(150,130,255,0.2)", width=1, dash="dot"),
                    name="Invariant circles",
                    hoverinfo="skip",
                ))

    # ── 3. Animated grid lines (space morphs from identity → M) ──────────────
    span = np.linspace(-4, 4, 50)
    for g in np.arange(-4, 5, 1):
        pts = Mt @ np.array([np.full_like(span, g), span])
        fig.add_trace(go.Scatter(
            x=pts[0], y=pts[1], mode="lines",
            line=dict(color="rgba(255, 140, 0, 0.25)", width=1),
            showlegend=False, hoverinfo="skip",
        ))
        pts = Mt @ np.array([span, np.full_like(span, g)])
        fig.add_trace(go.Scatter(
            x=pts[0], y=pts[1], mode="lines",
            line=dict(color="rgba(0, 160, 255, 0.25)", width=1),
            showlegend=False, hoverinfo="skip",
        ))

    # ── 4. Phase portrait: 24 seed vectors flowing under A^t ─────────────────
    #    Seed uniformly around the origin, show full trajectory (static) and
    #    current traversed portion (bright) with moving dots.
    if flow_ok:
        n_seeds = 24
        theta_s = np.linspace(0, 2 * np.pi, n_seeds, endpoint=False)
        seeds = [1.5 * np.array([np.cos(a), np.sin(a)]) for a in theta_s]

        t_full = np.linspace(0, 1.0, 80)
        t_curr = np.linspace(0, frac, max(2, int(frac * 80)))

        # Full trajectories (static, faint) — shows the complete flow pattern
        xf, yf = [], []
        # Current traversed (brighter)
        xc, yc = [], []
        # Current position dots
        dx, dy = [], []

        for seed in seeds:
            tf = _flow(seed, t_full)
            xf.extend(list(tf[0]) + [None])
            yf.extend(list(tf[1]) + [None])
            tc = _flow(seed, t_curr)
            xc.extend(list(tc[0]) + [None])
            yc.extend(list(tc[1]) + [None])
            pos = Mt @ seed
            dx.append(pos[0])
            dy.append(pos[1])

        fig.add_trace(go.Scatter(
            x=xf, y=yf, mode="lines",
            line=dict(color="rgba(180,140,255,0.12)", width=1),
            legendgroup="phase", name="Phase portrait",
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=xc, y=yc, mode="lines",
            line=dict(color="rgba(180,140,255,0.45)", width=1.5),
            legendgroup="phase", showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=dx, y=dy, mode="markers",
            marker=dict(color="rgba(180,140,255,0.7)", size=4),
            legendgroup="phase", showlegend=False,
            hoverinfo="skip",
        ))

    # ── 5. Eigenvector lines (infinite, static reference) ────────────────────
    _EIG_COLORS = ["#ffdd44", "#ff44dd"]
    for k in range(2):
        if not real_eig_mask[k]:
            continue
        ev = eigvecs_M[:, k].real
        ev = ev / np.linalg.norm(ev)
        lam = eigvals_M[k].real
        far = 8
        fig.add_trace(go.Scatter(
            x=[-far * ev[0], far * ev[0]],
            y=[-far * ev[1], far * ev[1]],
            mode="lines",
            line=dict(color=_EIG_COLORS[k], width=1.5, dash="dash"),
            opacity=0.5,
            name=f"eigenvector (lambda={lam:.2g})",
        ))
        tip = Mt @ ev
        fig.add_trace(go.Scatter(
            x=[tip[0]], y=[tip[1]], mode="markers",
            marker=dict(color=_EIG_COLORS[k], size=8, symbol="diamond",
                        line=dict(color="white", width=1)),
            showlegend=False,
        ))

    # ── 6. Unit circle → ellipse with SVD semi-axes ──────────────────────────
    theta = np.linspace(0, 2 * np.pi, 100)
    circle = np.array([np.cos(theta), np.sin(theta)])
    ellipse = Mt @ circle
    fig.add_trace(go.Scatter(
        x=ellipse[0], y=ellipse[1], mode="lines",
        line=dict(color="#e6edf3", width=2), name="Unit circle",
    ))
    for k in range(2):
        axis = U[:, k] * S[k]
        fig.add_trace(go.Scatter(
            x=[-axis[0], axis[0]], y=[-axis[1], axis[1]],
            mode="lines",
            line=dict(color="#ff8800" if k == 0 else "#00aaff", width=2, dash="dot"),
            opacity=0.7,
            name=f"sigma{k+1} = {S[k]:.2g}",
        ))

    # ── 7. Basis vectors ─────────────────────────────────────────────────────
    e1 = Mt @ np.array([1, 0])
    e2 = Mt @ np.array([0, 1])
    fig.add_trace(go.Scatter(
        x=[0, e1[0]], y=[0, e1[1]], mode="lines+markers",
        line=dict(color="#ff4444", width=3),
        marker=dict(symbol=["circle", "arrow"], size=[0, 12],
                    angleref="previous", color="#ff4444"),
        name=f"e1 -> ({e1[0]:.2f}, {e1[1]:.2f})",
    ))
    fig.add_trace(go.Scatter(
        x=[0, e2[0]], y=[0, e2[1]], mode="lines+markers",
        line=dict(color="#4488ff", width=3),
        marker=dict(symbol=["circle", "arrow"], size=[0, 12],
                    angleref="previous", color="#4488ff"),
        name=f"e2 -> ({e2[0]:.2f}, {e2[1]:.2f})",
    ))

    # ── 8. User vector: trajectory curve + arrow + dot ───────────────────────
    vec = _parse_vector(vec_str)
    if vec is not None and len(vec) == 2:
        if flow_ok:
            # Static full trajectory curve (the hyperbola / arc the vector follows)
            t_traj = np.linspace(-0.5, 2.0, 200)
            traj = _flow(vec, t_traj)
            fig.add_trace(go.Scatter(
                x=traj[0], y=traj[1], mode="lines",
                line=dict(color="rgba(0,255,136,0.15)", width=1.5, dash="dot"),
                name="Trajectory curve",
                hoverinfo="skip",
            ))
            # Traversed portion (bright, solid)
            t_done = np.linspace(0, frac, max(2, int(frac * 80)))
            traj_done = _flow(vec, t_done)
            fig.add_trace(go.Scatter(
                x=traj_done[0], y=traj_done[1], mode="lines",
                line=dict(color="rgba(0,255,136,0.5)", width=2.5),
                showlegend=False, hoverinfo="skip",
            ))
        else:
            # Linear interpolation fallback trail
            n_trail = 60
            trail_fracs = np.linspace(0, frac, n_trail)
            trail_pts = np.array([(((1 - f) * I2 + f * M) @ vec) for f in trail_fracs])
            fig.add_trace(go.Scatter(
                x=trail_pts[:, 0], y=trail_pts[:, 1], mode="lines",
                line=dict(color="rgba(0,255,136,0.3)", width=2),
                showlegend=False, hoverinfo="skip",
            ))

        # Current vector arrow
        v_t = Mt @ vec
        fig.add_trace(go.Scatter(
            x=[0, v_t[0]], y=[0, v_t[1]], mode="lines+markers",
            line=dict(color="#00ff88", width=3),
            marker=dict(symbol=["circle", "arrow"], size=[0, 12],
                        angleref="previous", color="#00ff88"),
            name=f"v -> ({v_t[0]:.2f}, {v_t[1]:.2f})",
        ))
        # Bright dot at tip
        fig.add_trace(go.Scatter(
            x=[v_t[0]], y=[v_t[1]], mode="markers",
            marker=dict(color="#00ff88", size=9,
                        line=dict(color="white", width=1.5)),
            showlegend=False,
        ))

    # Origin
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers",
        marker=dict(symbol="cross", color="white", size=10, line=dict(width=2)),
        showlegend=False,
    ))

    fig.update_layout(
        **DARK,
        title=dict(text=(
            f"det = {det_M:.3g}  |  eigenvalues: {eig_str}  |  "
            f"t = {frac:.2f}"
        ), font=dict(size=12)),
        xaxis=dict(
            range=[-5, 5], scaleanchor="y", scaleratio=1,
            zeroline=True, zerolinecolor="#30363d", zerolinewidth=1,
            showgrid=False,
        ),
        yaxis=dict(
            range=[-5, 5],
            zeroline=True, zerolinecolor="#30363d", zerolinewidth=1,
            showgrid=False,
        ),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(13,17,23,0.7)", font=dict(size=11)),
    )
    return fig


def _fig_linear_3d(matrix_str, t, vec_str):
    """3D linear transformation — animated cube, phase portrait,
    trajectory curves, eigenvector lines, basis vectors."""
    try:
        M = _parse_matrix(matrix_str)
        if M.shape != (3, 3):
            raise ValueError(f"Expected 3x3, got {M.shape[0]}x{M.shape[1]}")
    except Exception as e:
        fig = go.Figure()
        fig.update_layout(**DARK, title=dict(text=f"Matrix error: {e}", font=dict(color="#ff6b6b")))
        return fig

    frac = 1 - abs(2 * ((t % 4) / 4) - 1)
    I3 = np.eye(3)

    # Matrix logarithm for continuous flow
    B = None
    try:
        from scipy.linalg import logm as _logm, expm as _expm
        B_cand = _logm(M.astype(complex))
        if np.all(np.abs(B_cand.imag) < 1e-8):
            B_real = B_cand.real
            if np.linalg.norm(B_real) > 1e-10:
                B = B_real
    except Exception:
        pass

    if B is not None:
        from scipy.linalg import expm as _expm
        Mt = _expm(frac * B)
    else:
        Mt = (1 - frac) * I3 + frac * M

    det_M = float(np.linalg.det(M))
    eigvals_M, eigvecs_M = np.linalg.eig(M)
    real_eig_mask = np.abs(eigvals_M.imag) < 1e-10
    eig_str = ", ".join(
        f"{v.real:.2g}{'+' if v.imag >= 0 else ''}{v.imag:.2g}i" if abs(v.imag) > 1e-10
        else f"{v.real:.2g}"
        for v in eigvals_M
    )

    # Flow trajectory helper
    flow_ok = False
    if B is not None:
        eig_B3, P_B3 = np.linalg.eig(B)
        try:
            Pinv_B3 = np.linalg.inv(P_B3)
            flow_ok = True
        except np.linalg.LinAlgError:
            pass

    def _flow3(v0, t_arr):
        xi0 = Pinv_B3 @ v0
        return (P_B3 @ (xi0[:, None] * np.exp(np.outer(eig_B3, t_arr)))).real

    fig = go.Figure()

    # ── Animated cube wireframe ───────────────────────────────────────────────
    corners = np.array([
        [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
        [-1, -1,  1], [1, -1,  1], [1, 1,  1], [-1, 1,  1],
    ], dtype=float)
    edges = [
        (0,1),(1,2),(2,3),(3,0),
        (4,5),(5,6),(6,7),(7,4),
        (0,4),(1,5),(2,6),(3,7),
    ]
    tc = (Mt @ corners.T).T
    for i, j in edges:
        fig.add_trace(go.Scatter3d(
            x=[tc[i,0], tc[j,0]], y=[tc[i,1], tc[j,1]], z=[tc[i,2], tc[j,2]],
            mode="lines", line=dict(color="rgba(230,237,243,0.5)", width=3),
            showlegend=False, hoverinfo="skip",
        ))

    # ── Grid lines on cube faces ──────────────────────────────────────────────
    span = np.linspace(-1, 1, 10)
    for g in np.linspace(-1, 1, 5):
        for zv in [-1, 1]:
            pts = Mt @ np.array([span, np.full_like(span, g), np.full_like(span, zv)])
            fig.add_trace(go.Scatter3d(
                x=pts[0], y=pts[1], z=pts[2], mode="lines",
                line=dict(color="rgba(0,160,255,0.15)", width=1),
                showlegend=False, hoverinfo="skip",
            ))
            pts = Mt @ np.array([np.full_like(span, g), span, np.full_like(span, zv)])
            fig.add_trace(go.Scatter3d(
                x=pts[0], y=pts[1], z=pts[2], mode="lines",
                line=dict(color="rgba(255,140,0,0.15)", width=1),
                showlegend=False, hoverinfo="skip",
            ))

    # ── Phase portrait: 12 seed vectors flowing under A^t ─────────────────────
    if flow_ok:
        # Icosahedron vertices as evenly-distributed seed directions
        phi = (1 + np.sqrt(5)) / 2
        ico_raw = [
            (0, 1, phi), (0, -1, phi), (0, 1, -phi), (0, -1, -phi),
            (1, phi, 0), (-1, phi, 0), (1, -phi, 0), (-1, -phi, 0),
            (phi, 0, 1), (-phi, 0, 1), (phi, 0, -1), (-phi, 0, -1),
        ]
        seeds3 = [1.2 * np.array(v) / np.linalg.norm(v) for v in ico_raw]

        t_full = np.linspace(0, 1.0, 60)
        t_curr = np.linspace(0, frac, max(2, int(frac * 60)))

        xf, yf, zf = [], [], []
        xc, yc, zc = [], [], []
        ddx, ddy, ddz = [], [], []

        for seed in seeds3:
            tf = _flow3(seed, t_full)
            xf.extend(list(tf[0]) + [None])
            yf.extend(list(tf[1]) + [None])
            zf.extend(list(tf[2]) + [None])
            tc_arr = _flow3(seed, t_curr)
            xc.extend(list(tc_arr[0]) + [None])
            yc.extend(list(tc_arr[1]) + [None])
            zc.extend(list(tc_arr[2]) + [None])
            pos = Mt @ seed
            ddx.append(pos[0]); ddy.append(pos[1]); ddz.append(pos[2])

        fig.add_trace(go.Scatter3d(
            x=xf, y=yf, z=zf, mode="lines",
            line=dict(color="rgba(180,140,255,0.15)", width=2),
            legendgroup="phase", name="Phase portrait",
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter3d(
            x=xc, y=yc, z=zc, mode="lines",
            line=dict(color="rgba(180,140,255,0.5)", width=3),
            legendgroup="phase", showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter3d(
            x=ddx, y=ddy, z=ddz, mode="markers",
            marker=dict(color="rgba(180,140,255,0.7)", size=3),
            legendgroup="phase", showlegend=False,
            hoverinfo="skip",
        ))

    # ── Eigenvector lines ─────────────────────────────────────────────────────
    _EIG_COLORS_3D = ["#ffdd44", "#ff44dd", "#44ffdd"]
    for k in range(3):
        if not real_eig_mask[k]:
            continue
        ev = eigvecs_M[:, k].real
        ev = ev / np.linalg.norm(ev)
        lam = eigvals_M[k].real
        far = 5
        fig.add_trace(go.Scatter3d(
            x=[-far*ev[0], far*ev[0]],
            y=[-far*ev[1], far*ev[1]],
            z=[-far*ev[2], far*ev[2]],
            mode="lines",
            line=dict(color=_EIG_COLORS_3D[k], width=3, dash="dash"),
            opacity=0.5,
            name=f"eigvec (lambda={lam:.2g})",
        ))
        tip = Mt @ ev
        fig.add_trace(go.Scatter3d(
            x=[tip[0]], y=[tip[1]], z=[tip[2]], mode="markers",
            marker=dict(color=_EIG_COLORS_3D[k], size=5, symbol="diamond"),
            showlegend=False,
        ))

    # ── Basis vectors ─────────────────────────────────────────────────────────
    colors = ["#ff4444", "#4488ff", "#00cc44"]
    names = ["e1", "e2", "e3"]
    for k in range(3):
        e = np.zeros(3)
        e[k] = 1
        v = Mt @ e
        fig.add_trace(go.Scatter3d(
            x=[0, v[0]], y=[0, v[1]], z=[0, v[2]],
            mode="lines+markers",
            line=dict(color=colors[k], width=6),
            marker=dict(size=[0, 5], color=colors[k]),
            name=f"{names[k]} -> ({v[0]:.2f}, {v[1]:.2f}, {v[2]:.2f})",
        ))
        fig.add_trace(go.Cone(
            x=[v[0]], y=[v[1]], z=[v[2]],
            u=[v[0]*0.15], v=[v[1]*0.15], w=[v[2]*0.15],
            colorscale=[[0, colors[k]], [1, colors[k]]],
            showscale=False, sizemode="absolute", sizeref=0.15,
            showlegend=False,
        ))

    # ── User vector with trajectory curve ─────────────────────────────────────
    vec = _parse_vector(vec_str)
    if vec is not None and len(vec) == 3:
        if flow_ok:
            # Static full trajectory
            t_traj = np.linspace(-0.5, 2.0, 150)
            traj = _flow3(vec, t_traj)
            fig.add_trace(go.Scatter3d(
                x=traj[0], y=traj[1], z=traj[2], mode="lines",
                line=dict(color="rgba(0,255,136,0.15)", width=2, dash="dot"),
                name="Trajectory curve",
                hoverinfo="skip",
            ))
            t_done = np.linspace(0, frac, max(2, int(frac * 60)))
            traj_done = _flow3(vec, t_done)
            fig.add_trace(go.Scatter3d(
                x=traj_done[0], y=traj_done[1], z=traj_done[2], mode="lines",
                line=dict(color="rgba(0,255,136,0.5)", width=4),
                showlegend=False, hoverinfo="skip",
            ))
        else:
            n_trail = 60
            trail_fracs = np.linspace(0, frac, n_trail)
            trail_pts = np.array([(((1 - f) * I3 + f * M) @ vec) for f in trail_fracs])
            fig.add_trace(go.Scatter3d(
                x=trail_pts[:, 0], y=trail_pts[:, 1], z=trail_pts[:, 2],
                mode="lines", line=dict(color="rgba(0,255,136,0.3)", width=3),
                showlegend=False, hoverinfo="skip",
            ))

        vt = Mt @ vec
        fig.add_trace(go.Scatter3d(
            x=[0, vt[0]], y=[0, vt[1]], z=[0, vt[2]],
            mode="lines+markers",
            line=dict(color="#00ff88", width=6),
            marker=dict(size=[0, 5], color="#00ff88"),
            name=f"v -> ({vt[0]:.2f}, {vt[1]:.2f}, {vt[2]:.2f})",
        ))
        fig.add_trace(go.Cone(
            x=[vt[0]], y=[vt[1]], z=[vt[2]],
            u=[vt[0]*0.15], v=[vt[1]*0.15], w=[vt[2]*0.15],
            colorscale=[[0, "#00ff88"], [1, "#00ff88"]],
            showscale=False, sizemode="absolute", sizeref=0.15,
            showlegend=False,
        ))
        fig.add_trace(go.Scatter3d(
            x=[vt[0]], y=[vt[1]], z=[vt[2]], mode="markers",
            marker=dict(color="#00ff88", size=5,
                        line=dict(color="white", width=1)),
            showlegend=False,
        ))

    # Origin
    fig.add_trace(go.Scatter3d(
        x=[0], y=[0], z=[0], mode="markers",
        marker=dict(symbol="cross", color="white", size=4),
        showlegend=False,
    ))

    angle = t * 0.3
    camera = dict(eye=dict(x=2.5*np.cos(angle), y=2.5*np.sin(angle), z=1.2))

    fig.update_layout(
        **DARK,
        title=dict(text=(
            f"det = {det_M:.3g}  |  eigenvalues: {eig_str}  |  t = {frac:.2f}"
        ), font=dict(size=12)),
        scene=dict(
            xaxis=dict(range=[-4, 4], title="x"),
            yaxis=dict(range=[-4, 4], title="y"),
            zaxis=dict(range=[-4, 4], title="z"),
            camera=camera,
            aspectmode="cube",
        ),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(13,17,23,0.7)", font=dict(size=10)),
    )
    return fig


def _fig_zeros(t_max, n_zeros, res, t_cursor):
    from manifold.math.zeta import find_zeros_on_critical_line, zeta_on_critical_line
    t_vals = np.linspace(0.5, t_max, max(res * 5, 500))
    zv = zeta_on_critical_line(t_vals, dps=25)
    zeros = find_zeros_on_critical_line(n_zeros=n_zeros, dps=30)
    idx = min(int(np.searchsorted(t_vals, t_cursor)), len(t_vals)-1)

    fig = make_subplots(1, 2, subplot_titles=["zeta(1/2+it) in C", "|zeta(1/2+it)| vs t"])
    fig.add_trace(go.Scatter(x=zv.real, y=zv.imag, mode="lines",
                             line=dict(color="#00BFFF", width=0.8), opacity=0.2,
                             showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=zv[:idx+1].real, y=zv[:idx+1].imag, mode="lines",
                             line=dict(color="#00BFFF", width=2), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=[zv[idx].real], y=[zv[idx].imag], mode="markers",
                             marker=dict(color="#FF8C00", size=10), name="current"), row=1, col=1)
    _cross = dict(symbol="cross", color="white", size=12, line=dict(width=2))
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers",
        marker=_cross, name="origin"), row=1, col=1)
    mod = np.abs(zv)
    fig.add_trace(go.Scatter(
        x=t_vals, y=mod, mode="lines",
        line=dict(color="#00BFFF", width=1.5), showlegend=False,
    ), row=1, col=2)
    for z in zeros:
        fig.add_vline(
            x=z.imag, line=dict(color="red", dash="dash", width=1),
            opacity=0.5, row=1, col=2)
    fig.add_vline(x=t_cursor, line=dict(color="#FF8C00", width=2), row=1, col=2)

    fig.update_layout(**DARK, title="Riemann zeta(s) -- Critical Line Re(s) = 1/2")
    return fig


def _fig_strip(im_max, res):
    from manifold.math.zeta import zeta_grid
    rp = max(20, min(res // 3, 60))
    ip = max(50, min(res, 200))
    _, _, Z = zeta_grid(re_range=(0.02, 0.98), im_range=(0.5, im_max),
                           re_points=rp, im_points=ip, dps=25)
    Z_t = Z.T
    re_vals = np.linspace(0.02, 0.98, rp)
    im_vals = np.linspace(0.5, im_max, ip)
    mag = np.log1p(np.abs(Z_t))
    phase = np.angle(Z_t)

    fig = make_subplots(1, 2, subplot_titles=["log(1+|zeta(s)|)", "arg(zeta(s))"])
    fig.add_trace(go.Heatmap(x=re_vals, y=im_vals, z=mag, colorscale="inferno",
                             showscale=False), row=1, col=1)
    fig.add_trace(go.Heatmap(x=re_vals, y=im_vals, z=phase, colorscale="hsv",
                             zmin=-np.pi, zmax=np.pi, showscale=False), row=1, col=2)
    for col in (1, 2):
        fig.add_vline(x=0.5, line=dict(color="cyan", dash="dash", width=1.5), row=1, col=col)
    fig.update_layout(**DARK, title="zeta(s) over Critical Strip  0 < Re(s) < 1")
    return fig


def _fig_winding(im_top, n_zeros):
    from manifold.math.zeta import find_zeros_on_critical_line, zeta_on_contour
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

    titles = ["s-plane contour", f"zeta(C) -- winding = {winding:.1f}"]
    fig = make_subplots(1, 2, subplot_titles=titles)
    fig.add_trace(go.Scatter(
        x=contour.real, y=contour.imag, mode="lines",
        line=dict(color="#FF8C00", width=2), showlegend=False,
    ), row=1, col=1)
    for z in zeros:
        col = "red" if z.imag < im_top else "#444"
        fig.add_trace(go.Scatter(
            x=[0.5], y=[z.imag], mode="markers",
            marker=dict(symbol="x", color=col, size=8),
            showlegend=False), row=1, col=1)
    fig.add_vline(
        x=0.5, line=dict(color="cyan", dash="dash", width=1),
        row=1, col=1)
    fig.add_trace(go.Scatter(
        x=fw.real, y=fw.imag, mode="lines",
        line=dict(color="#FF8C00", width=2), showlegend=False,
    ), row=1, col=2)
    _cross = dict(
        symbol="cross", color="white", size=14, line=dict(width=2))
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers",
        marker=_cross, showlegend=False), row=1, col=2)
    fig.update_layout(**DARK, title=f"Argument Principle -- zeros enclosed: {n_enc}")
    return fig


if __name__ == "__main__":
    app.run(debug=True, port=8050)
