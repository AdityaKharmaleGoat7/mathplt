"""Dash layout — sidebar controls + main graph area."""

from dash import dcc, html

from webapp.theme import _CARD, _HINT, _INPUT, _LBL, _MAT_INPUT, _SEC


def build_layout():
    """Return the full app layout component tree."""
    return html.Div(style={
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
                html.Div(id="eq-input-wrapper", children=[
                    dcc.Input(id="equation", type="text", debounce=True,
                        value="sin(x + t) * exp(-0.1 * x**2)",
                        placeholder="e.g. sin(x + t) * exp(-0.1 * x**2)",
                        style=_INPUT,
                    ),
                ]),
                html.Div(id="matrix-grid-2d", style={"display": "none"}, children=[
                    html.Div(style={
                        "display": "grid", "gridTemplateColumns": "1fr 1fr",
                        "gap": "6px", "maxWidth": "180px", "margin": "0 auto 6px auto",
                    }, children=[
                        dcc.Input(id="mat-00", type="number", value=1, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                        dcc.Input(id="mat-01", type="number", value=0, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                        dcc.Input(id="mat-10", type="number", value=0, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                        dcc.Input(id="mat-11", type="number", value=1, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                    ]),
                    html.Div(style={
                        "textAlign": "center", "fontSize": "10px", "color": "#484f58",
                    }, children="[ a  b ]  /  [ c  d ]"),
                ]),
                html.Div(id="matrix-grid-3d", style={"display": "none"}, children=[
                    html.Div(style={
                        "display": "grid", "gridTemplateColumns": "1fr 1fr 1fr",
                        "gap": "5px", "maxWidth": "240px", "margin": "0 auto 6px auto",
                    }, children=[
                        dcc.Input(id="mat3-00", type="number", value=1, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                        dcc.Input(id="mat3-01", type="number", value=0, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                        dcc.Input(id="mat3-02", type="number", value=0, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                        dcc.Input(id="mat3-10", type="number", value=0, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                        dcc.Input(id="mat3-11", type="number", value=1, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                        dcc.Input(id="mat3-12", type="number", value=0, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                        dcc.Input(id="mat3-20", type="number", value=0, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                        dcc.Input(id="mat3-21", type="number", value=0, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                        dcc.Input(id="mat3-22", type="number", value=1, step=0.1,
                                  debounce=True, style=_MAT_INPUT),
                    ]),
                    html.Div(style={
                        "textAlign": "center", "fontSize": "10px", "color": "#484f58",
                    }, children="3x3 matrix  \u2014  rows top to bottom"),
                ]),
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
                dcc.Checklist(
                    id="show-ref-grid", value=["on"],
                    options=[{"label": " Show reference grid", "value": "on"}],
                    inputStyle={"marginRight": "6px"},
                    labelStyle={"fontSize": "12px", "color": "#8b949e"},
                    style={"marginBottom": "8px"},
                ),
                html.Span("Vectors (optional)", style=_LBL),
                dcc.Input(
                    id="vector-input", type="text", debounce=True,
                    placeholder="e.g. 1,2; 3,-1; 0,1",
                    style=_INPUT,
                ),
                html.Div("Separate vectors with ;   (e.g. 1,2; 3,-1; 0,1)", style=_HINT),
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

        # ── Home splash overlay (covers entire viewport incl. sidebar) ────────
        html.Div(id="home-splash", style={
            "position": "fixed", "top": "0", "left": "0",
            "width": "100vw", "height": "100vh",
            "background": "#0d1117",
            "display": "flex", "flexDirection": "column",
            "alignItems": "center", "justifyContent": "center",
            "zIndex": "9999",
        }, children=[
            html.Img(src="/assets/logo.png", style={
                "width": "180px", "height": "180px",
                "marginBottom": "24px", "opacity": "0.98",
                "filter": "drop-shadow(0 4px 24px rgba(88, 166, 255, 0.35))",
            }),
            html.Div("Manifold", style={
                "color": "#58a6ff", "fontSize": "56px",
                "fontWeight": "700", "letterSpacing": "0.04em",
                "marginBottom": "6px",
            }),
            html.Div("Own the space", style={
                "color": "#8b949e", "fontSize": "18px",
                "fontStyle": "italic", "letterSpacing": "0.32em",
                "marginBottom": "36px", "textTransform": "uppercase",
            }),
            html.Button("Get Started", id="home-dismiss", n_clicks=0, style={
                "background": "#238636", "color": "white",
                "border": "none", "borderRadius": "8px",
                "padding": "12px 32px", "fontSize": "14px",
                "fontWeight": "600", "letterSpacing": "0.08em",
                "cursor": "pointer", "fontFamily": "monospace",
            }),
        ]),

        # Interval timer
        dcc.Interval(id="interval", interval=80, disabled=True),
    ])
