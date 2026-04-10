"""Visual constants — dark theme, styles, CSS template."""

# ── Inject dark-mode CSS for Dash dropdowns and scrollbars ────────────────────
INDEX_STRING = """<!DOCTYPE html>
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
_MAT_INPUT = {"width": "100%", "boxSizing": "border-box", "textAlign": "center",
              "background": "#0d1117", "color": "#e6edf3",
              "border": "1px solid #30363d", "borderRadius": "6px",
              "padding": "10px 4px", "fontFamily": "monospace", "fontSize": "15px",
              "fontWeight": "600"}
