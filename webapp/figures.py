"""Figure builders — all _fig_* functions for each visualization mode."""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from webapp.app import _parser
from webapp.helpers import _VEC_COLORS, _parse_matrix, _parse_vectors
from webapp.theme import DARK


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

    # Ping-pong interpolation: 0 -> 1 -> 0 over period 4
    frac = 1 - abs(2 * ((t % 4) / 4) - 1)
    I2 = np.eye(2)

    # ── Matrix logarithm for continuous flow M^t ─────────────────────────────
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
    if flow_ok:
        eig_B_r = eig_B.real if all(abs(v.imag) < 1e-10 for v in eig_B) else None
        inv_drawn = False

        if eig_B_r is not None:
            mu1, mu2 = eig_B_r
            if abs(mu1) > 1e-10 and abs(mu2) > 1e-10 and abs(mu1 - mu2) > 1e-10:
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

    # ── 3. Animated grid lines (space morphs from identity -> M) ──────────────
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
    if flow_ok:
        n_seeds = 24
        theta_s = np.linspace(0, 2 * np.pi, n_seeds, endpoint=False)
        seeds = [1.5 * np.array([np.cos(a), np.sin(a)]) for a in theta_s]

        t_full = np.linspace(0, 1.0, 80)
        t_curr = np.linspace(0, frac, max(2, int(frac * 80)))

        xf, yf = [], []
        xc, yc = [], []
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

    # ── 6. Unit circle -> ellipse with SVD semi-axes ──────────────────────────
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

    # ── 8. User vectors: trajectory curves + arrows + dots ──────────────────
    user_vecs = _parse_vectors(vec_str, 2)
    for vi, vec in enumerate(user_vecs):
        col = _VEC_COLORS[vi % len(_VEC_COLORS)]
        r, g, b = int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)
        col_faint = f"rgba({r},{g},{b},0.15)"
        col_mid = f"rgba({r},{g},{b},0.5)"
        col_trail = f"rgba({r},{g},{b},0.3)"

        if flow_ok:
            t_traj = np.linspace(-0.5, 2.0, 200)
            traj = _flow(vec, t_traj)
            fig.add_trace(go.Scatter(
                x=traj[0], y=traj[1], mode="lines",
                line=dict(color=col_faint, width=1.5, dash="dot"),
                name=f"Traj v{vi+1}",
                hoverinfo="skip",
            ))
            t_done = np.linspace(0, frac, max(2, int(frac * 80)))
            traj_done = _flow(vec, t_done)
            fig.add_trace(go.Scatter(
                x=traj_done[0], y=traj_done[1], mode="lines",
                line=dict(color=col_mid, width=2.5),
                showlegend=False, hoverinfo="skip",
            ))
        else:
            n_trail = 60
            trail_fracs = np.linspace(0, frac, n_trail)
            trail_pts = np.array([(((1 - f) * I2 + f * M) @ vec) for f in trail_fracs])
            fig.add_trace(go.Scatter(
                x=trail_pts[:, 0], y=trail_pts[:, 1], mode="lines",
                line=dict(color=col_trail, width=2),
                showlegend=False, hoverinfo="skip",
            ))

        v_t = Mt @ vec
        fig.add_trace(go.Scatter(
            x=[0, v_t[0]], y=[0, v_t[1]], mode="lines+markers",
            line=dict(color=col, width=3),
            marker=dict(symbol=["circle", "arrow"], size=[0, 12],
                        angleref="previous", color=col),
            name=f"v{vi+1} -> ({v_t[0]:.2f}, {v_t[1]:.2f})",
        ))
        fig.add_trace(go.Scatter(
            x=[v_t[0]], y=[v_t[1]], mode="markers",
            marker=dict(color=col, size=9,
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

    # ── User vectors with trajectory curves ─────────────────────────────────
    user_vecs = _parse_vectors(vec_str, 3)
    for vi, vec in enumerate(user_vecs):
        col = _VEC_COLORS[vi % len(_VEC_COLORS)]
        r, g, b = int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)
        col_faint = f"rgba({r},{g},{b},0.15)"
        col_mid = f"rgba({r},{g},{b},0.5)"
        col_trail = f"rgba({r},{g},{b},0.3)"

        if flow_ok:
            t_traj = np.linspace(-0.5, 2.0, 150)
            traj = _flow3(vec, t_traj)
            fig.add_trace(go.Scatter3d(
                x=traj[0], y=traj[1], z=traj[2], mode="lines",
                line=dict(color=col_faint, width=2, dash="dot"),
                name=f"Traj v{vi+1}",
                hoverinfo="skip",
            ))
            t_done = np.linspace(0, frac, max(2, int(frac * 60)))
            traj_done = _flow3(vec, t_done)
            fig.add_trace(go.Scatter3d(
                x=traj_done[0], y=traj_done[1], z=traj_done[2], mode="lines",
                line=dict(color=col_mid, width=4),
                showlegend=False, hoverinfo="skip",
            ))
        else:
            n_trail = 60
            trail_fracs = np.linspace(0, frac, n_trail)
            trail_pts = np.array([(((1 - f) * I3 + f * M) @ vec) for f in trail_fracs])
            fig.add_trace(go.Scatter3d(
                x=trail_pts[:, 0], y=trail_pts[:, 1], z=trail_pts[:, 2],
                mode="lines", line=dict(color=col_trail, width=3),
                showlegend=False, hoverinfo="skip",
            ))

        vt = Mt @ vec
        fig.add_trace(go.Scatter3d(
            x=[0, vt[0]], y=[0, vt[1]], z=[0, vt[2]],
            mode="lines+markers",
            line=dict(color=col, width=6),
            marker=dict(size=[0, 5], color=col),
            name=f"v{vi+1} -> ({vt[0]:.2f}, {vt[1]:.2f}, {vt[2]:.2f})",
        ))
        fig.add_trace(go.Cone(
            x=[vt[0]], y=[vt[1]], z=[vt[2]],
            u=[vt[0]*0.15], v=[vt[1]*0.15], w=[vt[2]*0.15],
            colorscale=[[0, col], [1, col]],
            showscale=False, sizemode="absolute", sizeref=0.15,
            showlegend=False,
        ))
        fig.add_trace(go.Scatter3d(
            x=[vt[0]], y=[vt[1]], z=[vt[2]], mode="markers",
            marker=dict(color=col, size=5,
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
