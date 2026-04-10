"""All Dash callbacks — registered via @app.callback at import time."""

import dash
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, ctx, html, no_update

from webapp.app import app, _parser
from webapp.figures import (
    _fig_2d, _fig_3d, _fig_complex, _fig_linear_transform,
    _fig_point, _fig_strip, _fig_winding, _fig_zeros,
)
from webapp.helpers import (
    _INFO, _PRESET_LABELS, _PRESETS, _info_table, _parse_matrix,
)
from webapp.theme import DARK, _CARD, _SEC


# ── Show/hide sections based on animation type ───────────────────────────────

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


# ── Update eq section labels and toggle text input vs matrix grid ─────────────

@app.callback(
    Output("eq-title", "children"),
    Output("eq-hint",  "children"),
    Output("eq-input-wrapper", "style"),
    Output("matrix-grid-2d", "style"),
    Output("matrix-grid-3d", "style"),
    Input("anim-type", "value"),
    Input("linear-dim", "value"),
)
def update_eq_labels(anim, dim):
    hide = {"display": "none"}
    show_text = {"display": "block"}
    if anim == "linear_transform":
        if (dim or "2D") == "2D":
            return ("Transformation Matrix",
                    "Edit values directly  |  or use a preset below",
                    hide, {"display": "block"}, hide)
        return ("Transformation Matrix",
                "Edit values directly  |  or use a preset below",
                hide, hide, {"display": "block"})
    return ("Equation",
            "Use x, t for 2D  |  x, y for 3D  |  z, t for complex",
            show_text, hide, hide)


# ── Populate preset buttons based on mode ─────────────────────────────────────

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


# ── Preset button click -> set equation (or matrix cells for LT) ─────────────

@app.callback(
    Output("equation", "value"),
    Output("mat-00", "value"),
    Output("mat-01", "value"),
    Output("mat-10", "value"),
    Output("mat-11", "value"),
    Output("mat3-00", "value"),
    Output("mat3-01", "value"),
    Output("mat3-02", "value"),
    Output("mat3-10", "value"),
    Output("mat3-11", "value"),
    Output("mat3-12", "value"),
    Output("mat3-20", "value"),
    Output("mat3-21", "value"),
    Output("mat3-22", "value"),
    Input({"type": "preset-btn", "index": dash.ALL}, "n_clicks"),
    State("anim-type", "value"),
    State("linear-dim", "value"),
    prevent_initial_call=True,
)
def apply_preset(clicks, anim, dim):
    nu = no_update
    nu14 = (nu,) * 14
    if not ctx.triggered_id or not any(c for c in clicks if c):
        return nu14
    idx = ctx.triggered_id["index"]
    if anim == "linear_transform":
        key = f"linear_transform_{(dim or '2D').lower()}"
    else:
        key = anim
    presets = _PRESETS.get(key, [])
    if idx >= len(presets):
        return nu14
    preset = presets[idx]
    if anim == "linear_transform":
        try:
            M = _parse_matrix(preset)
            if (dim or "2D") == "2D" and M.shape == (2, 2):
                return (nu,
                        float(M[0,0]), float(M[0,1]), float(M[1,0]), float(M[1,1]),
                        nu, nu, nu, nu, nu, nu, nu, nu, nu)
            if (dim or "2D") == "3D" and M.shape == (3, 3):
                return (nu, nu, nu, nu, nu,
                        float(M[0,0]), float(M[0,1]), float(M[0,2]),
                        float(M[1,0]), float(M[1,1]), float(M[1,2]),
                        float(M[2,0]), float(M[2,1]), float(M[2,2]))
        except Exception:
            return nu14
    return (preset,) + (nu,) * 13


# ── Equation validation ──────────────────────────────────────────────────────

@app.callback(
    Output("eq-status", "children"),
    Output("eq-status", "style"),
    Input("equation", "value"),
    Input("mat-00", "value"),
    Input("mat-01", "value"),
    Input("mat-10", "value"),
    Input("mat-11", "value"),
    Input("mat3-00", "value"),
    Input("mat3-01", "value"),
    Input("mat3-02", "value"),
    Input("mat3-10", "value"),
    Input("mat3-11", "value"),
    Input("mat3-12", "value"),
    Input("mat3-20", "value"),
    Input("mat3-21", "value"),
    Input("mat3-22", "value"),
    State("anim-type", "value"),
    State("linear-dim", "value"),
    prevent_initial_call=True,
)
def validate_eq(expr, m00, m01, m10, m11,
                m3_00, m3_01, m3_02, m3_10, m3_11, m3_12, m3_20, m3_21, m3_22,
                anim, dim):
    ok_style = {"fontSize": "11px", "color": "#69db7c", "marginBottom": "12px"}
    err_style = {"fontSize": "11px", "color": "#ff6b6b", "marginBottom": "12px"}
    if anim == "linear_transform":
        if (dim or "2D") == "2D":
            vals = [m00, m01, m10, m11]
            if any(v is None for v in vals):
                return "Fill all matrix cells", err_style
            try:
                M = np.array([[float(m00), float(m01)], [float(m10), float(m11)]])
                det = float(np.linalg.det(M))
                return f"Valid 2x2 matrix  |  det = {det:.3g}", ok_style
            except Exception as e:
                return f"Invalid matrix: {e}", err_style
        # 3D
        vals3 = [m3_00, m3_01, m3_02, m3_10, m3_11, m3_12, m3_20, m3_21, m3_22]
        if any(v is None for v in vals3):
            return "Fill all matrix cells", err_style
        try:
            M = np.array([
                [float(m3_00), float(m3_01), float(m3_02)],
                [float(m3_10), float(m3_11), float(m3_12)],
                [float(m3_20), float(m3_21), float(m3_22)],
            ])
            det = float(np.linalg.det(M))
            return f"Valid 3x3 matrix  |  det = {det:.3g}", ok_style
        except Exception as e:
            return f"Invalid matrix: {e}", err_style
    if not expr:
        return "Empty equation.", err_style
    vars_map = {"graph2d": {"x","t"}, "graph3d": {"x","y"}, "complex": {"z","t"}}
    err = _parser.validate(expr, variables=vars_map.get(anim, {"x","t"}))
    if err:
        return f"Invalid: {err}", err_style
    return "Valid", ok_style


# ── Play / Stop ──────────────────────────────────────────────────────────────

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


# ── Speed slider -> interval ─────────────────────────────────────────────────

@app.callback(Output("interval", "interval"), Input("speed", "value"))
def set_speed(ms): return ms or 80


# ── Info panel ───────────────────────────────────────────────────────────────

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


# ── Interval -> advance t ────────────────────────────────────────────────────

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


# ── Main graph update ────────────────────────────────────────────────────────

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
    Input("mat-00", "value"),
    Input("mat-01", "value"),
    Input("mat-10", "value"),
    Input("mat-11", "value"),
    Input("mat3-00", "value"),
    Input("mat3-01", "value"),
    Input("mat3-02", "value"),
    Input("mat3-10", "value"),
    Input("mat3-11", "value"),
    Input("mat3-12", "value"),
    Input("mat3-20", "value"),
    Input("mat3-21", "value"),
    Input("mat3-22", "value"),
)
def update_graph(anim, eq, xr, yr, rer, imr, t, res, cmap, nz, imsmax, windtop, za, zb,
                 lin_dim, vec_str, m00, m01, m10, m11,
                 m3_00, m3_01, m3_02, m3_10, m3_11, m3_12, m3_20, m3_21, m3_22):
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
            if (lin_dim or "2D") == "2D":
                matrix_str = f"{m00 or 0}, {m01 or 0}; {m10 or 0}, {m11 or 0}"
            else:
                matrix_str = (f"{m3_00 or 0}, {m3_01 or 0}, {m3_02 or 0}; "
                              f"{m3_10 or 0}, {m3_11 or 0}, {m3_12 or 0}; "
                              f"{m3_20 or 0}, {m3_21 or 0}, {m3_22 or 0}")
            return _fig_linear_transform(matrix_str, t, lin_dim, vec_str), ""
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
