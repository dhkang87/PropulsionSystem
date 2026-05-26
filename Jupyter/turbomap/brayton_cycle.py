"""
brayton_cycle — Ideal and actual Brayton cycle computation & plotting.

Functions:
    brayton_states          Compute ideal 4-state thermodynamic points.
    build_cycle_curves      Build smooth ideal cycle curves (T-s, P-v).
    build_actual_cycle_curves  Build actual cycle with component losses.
    plot_brayton_ideal       Plot ideal Brayton cycle (T-s + P-v).
    plot_ideal_vs_actual     Plot ideal vs actual comparison.
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ──────────────────────────────────────────────────────────────────────────────
# Thermodynamic state computation
# ──────────────────────────────────────────────────────────────────────────────

def brayton_states(pr=8.0, gamma=1.4, t1=300.0, t3=1400.0, p1=1.0):
    """Return ideal Brayton state variables for points 1-4."""
    p2 = p1 * pr
    p3 = p2
    p4 = p1

    t2 = t1 * pr ** ((gamma - 1.0) / gamma)
    t4 = t3 / pr ** ((gamma - 1.0) / gamma)

    return {
        "T": np.array([t1, t2, t3, t4], dtype=float),
        "P": np.array([p1, p2, p3, p4], dtype=float),
    }


def build_cycle_curves(pr=8.0, gamma=1.4, t1=300.0, t3=1400.0, cp=1.005, m_dot=1.0):
    """Build smooth ideal Brayton cycle curves for T-s and P-v plotting."""
    states = brayton_states(pr=pr, gamma=gamma, t1=t1, t3=t3, p1=1.0)
    T = states["T"]
    P = states["P"]

    R = cp * (gamma - 1.0) / gamma

    # Entropy (relative, s1=0)
    s1 = 0.0
    s2 = s1
    s3 = s2 + cp * np.log(T[2] / T[1])
    s4 = s3
    s = np.array([s1, s2, s3, s4], dtype=float)

    # Specific volume at state points
    v = R * T / P

    n = 80

    # 1→2 isentropic compression
    p12 = np.linspace(P[0], P[1], n)
    c12 = P[0] * (v[0] ** gamma)
    v12 = (c12 / p12) ** (1.0 / gamma)
    t12 = p12 * v12 / R
    s12 = np.full_like(t12, s1)

    # 2→3 isobaric heating
    t23 = np.linspace(T[1], T[2], n)
    p23 = np.full_like(t23, P[1])
    s23 = s2 + cp * np.log(t23 / T[1])
    v23 = R * t23 / p23

    # 3→4 isentropic expansion
    p34 = np.linspace(P[2], P[3], n)
    c34 = P[2] * (v[2] ** gamma)
    v34 = (c34 / p34) ** (1.0 / gamma)
    t34 = p34 * v34 / R
    s34 = np.full_like(t34, s3)

    # 4→1 isobaric heat rejection
    t41 = np.linspace(T[3], T[0], n)
    p41 = np.full_like(t41, P[3])
    s41 = s4 + cp * np.log(t41 / T[3])
    v41 = R * t41 / p41

    eta_th = 1.0 - 1.0 / (pr ** ((gamma - 1.0) / gamma))
    w_net = m_dot * cp * ((T[2] - T[3]) - (T[1] - T[0]))

    return {
        "T": T,
        "P": P,
        "s": s,
        "v": v,
        "segments": {
            "12": (s12, t12, p12, v12),
            "23": (s23, t23, p23, v23),
            "34": (s34, t34, p34, v34),
            "41": (s41, t41, p41, v41),
        },
        "eta": eta_th,
        "w_net": w_net,
    }


def _poly_n_from_endpoints(t_in, t_out, p_in, p_out, default_n=1.35):
    """Estimate polytropic exponent n from endpoint states."""
    if p_in <= 0 or p_out <= 0 or t_in <= 0 or t_out <= 0:
        return default_n
    if np.isclose(p_in, p_out) or np.isclose(t_in, t_out):
        return default_n
    ratio = np.log(t_out / t_in) / np.log(p_out / p_in)
    denom = 1.0 - ratio
    if np.isclose(denom, 0.0):
        return default_n
    n = 1.0 / denom
    if not np.isfinite(n) or n <= 1.0:
        return default_n
    return n


def build_actual_cycle_curves(
    pr=8.0,
    gamma=1.4,
    t1=300.0,
    t3=1400.0,
    cp=1.005,
    eta_c=0.86,
    eta_t=0.90,
    combustor_dp=0.05,
    m_dot=1.0,
):
    """Build actual Brayton cycle curves with component losses."""
    p1 = 1.0
    p2 = p1 * pr
    p3 = p2 * (1.0 - combustor_dp)
    p4 = p1

    # Compressor actual outlet temperature
    t2s = t1 * (p2 / p1) ** ((gamma - 1.0) / gamma)
    t2 = t1 + (t2s - t1) / eta_c

    # Turbine actual outlet temperature
    t4s = t3 * (p4 / p3) ** ((gamma - 1.0) / gamma)
    t4 = t3 - eta_t * (t3 - t4s)

    R = cp * (gamma - 1.0) / gamma

    # State entropies relative to s1 = 0
    s1 = 0.0
    s2 = s1 + cp * np.log(t2 / t1) - R * np.log(p2 / p1)
    s3 = s2 + cp * np.log(t3 / t2) - R * np.log(p3 / p2)
    s4 = s3 + cp * np.log(t4 / t3) - R * np.log(p4 / p3)

    T = np.array([t1, t2, t3, t4], dtype=float)
    P = np.array([p1, p2, p3, p4], dtype=float)
    s = np.array([s1, s2, s3, s4], dtype=float)
    v = R * T / P

    n = 80

    # 1→2 actual compression (polytropic-like)
    n12 = _poly_n_from_endpoints(t1, t2, p1, p2, default_n=1.38)
    p12 = np.linspace(p1, p2, n)
    t12 = t1 * (p12 / p1) ** ((n12 - 1.0) / n12)
    s12 = s1 + cp * np.log(t12 / t1) - R * np.log(p12 / p1)
    v12 = R * t12 / p12

    # 2→3 combustor with pressure drop
    t23 = np.linspace(t2, t3, n)
    p23 = np.linspace(p2, p3, n)
    s23 = s2 + cp * np.log(t23 / t2) - R * np.log(p23 / p2)
    v23 = R * t23 / p23

    # 3→4 actual expansion (polytropic-like)
    n34 = _poly_n_from_endpoints(t3, t4, p3, p4, default_n=1.30)
    p34 = np.linspace(p3, p4, n)
    t34 = t3 * (p34 / p3) ** ((n34 - 1.0) / n34)
    s34 = s3 + cp * np.log(t34 / t3) - R * np.log(p34 / p3)
    v34 = R * t34 / p34

    # 4→1 exhaust/heat rejection
    t41 = np.linspace(t4, t1, n)
    p41 = np.full_like(t41, p4)
    s41 = s4 + cp * np.log(t41 / t4)
    v41 = R * t41 / p41

    w_net = m_dot * cp * ((t3 - t4) - (t2 - t1))
    q_in = m_dot * cp * max(t3 - t2, 1e-9)
    eta_th = w_net / q_in

    return {
        "T": T,
        "P": P,
        "s": s,
        "v": v,
        "segments": {
            "12": (s12, t12, p12, v12),
            "23": (s23, t23, p23, v23),
            "34": (s34, t34, p34, v34),
            "41": (s41, t41, p41, v41),
        },
        "eta": eta_th,
        "w_net": w_net,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Plotting functions
# ──────────────────────────────────────────────────────────────────────────────

def plot_brayton_ideal(pr=8.0, gamma=1.4, t1=300.0, t3=1400.0, cp=1.005, m_dot=1.0):
    """Plot ideal Brayton cycle T-s and P-v diagrams."""
    data = build_cycle_curves(pr, gamma, t1, t3, cp, m_dot)

    fig = make_subplots(rows=1, cols=2, subplot_titles=("T-s Diagram", "P-v Diagram"))

    for key, name in zip(["12", "23", "34", "41"], ["1→2", "2→3", "3→4", "4→1"]):
        s_seg, t_seg, _, _ = data["segments"][key]
        fig.add_trace(
            go.Scatter(x=s_seg, y=t_seg, mode="lines", name=f"{name} (T-s)"),
            row=1, col=1,
        )

    fig.add_trace(
        go.Scatter(
            x=data["s"], y=data["T"], mode="markers+text",
            text=["1", "2", "3", "4"], textposition="top center",
            name="States (T-s)", marker=dict(size=9),
        ),
        row=1, col=1,
    )

    for key, name in zip(["12", "23", "34", "41"], ["1→2", "2→3", "3→4", "4→1"]):
        _, _, p_seg, v_seg = data["segments"][key]
        fig.add_trace(
            go.Scatter(x=v_seg, y=p_seg, mode="lines", name=f"{name} (P-v)"),
            row=1, col=2,
        )

    fig.add_trace(
        go.Scatter(
            x=data["v"], y=data["P"], mode="markers+text",
            text=["1", "2", "3", "4"], textposition="top center",
            name="States (P-v)", marker=dict(size=9),
        ),
        row=1, col=2,
    )

    fig.update_xaxes(title_text="s [kJ/kg-K, relative]", row=1, col=1)
    fig.update_yaxes(title_text="T [K]", row=1, col=1)
    fig.update_xaxes(title_text="v [relative units]", row=1, col=2)
    fig.update_yaxes(title_text="P [bar, normalized]", row=1, col=2)

    fig.update_layout(
        width=1200, height=500, template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        title=(
            f"Ideal Brayton Cycle | PR={pr:.2f}, γ={gamma:.3f}, "
            f"η_th={100.0*data['eta']:.2f}% | W_net={data['w_net']:.2f} kW"
        ),
    )
    fig.show()
    return data


def plot_ideal_vs_actual(
    pr=8.0, gamma=1.4, t1=300.0, t3=1400.0, cp=1.005, m_dot=1.0,
    eta_c=0.86, eta_t=0.90, combustor_dp=0.05,
):
    """Plot ideal vs actual Brayton cycle comparison on T-s and P-v."""
    ideal = build_cycle_curves(pr, gamma, t1, t3, cp, m_dot)
    actual = build_actual_cycle_curves(pr, gamma, t1, t3, cp, eta_c, eta_t, combustor_dp, m_dot)

    fig = make_subplots(rows=1, cols=2, subplot_titles=("T-s: Ideal vs Actual", "P-v: Ideal vs Actual"))

    proc_keys = ["12", "23", "34", "41"]
    proc_labels = ["1→2", "2→3", "3→4", "4→1"]
    colors = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e"]

    # T-s diagram
    for k, label, color in zip(proc_keys, proc_labels, colors):
        s_i, t_i, _, _ = ideal["segments"][k]
        s_a, t_a, _, _ = actual["segments"][k]
        fig.add_trace(go.Scatter(x=s_i, y=t_i, mode="lines", line=dict(width=3, color=color), name=f"Ideal {label}"), row=1, col=1)
        fig.add_trace(go.Scatter(x=s_a, y=t_a, mode="lines", line=dict(width=2, color=color, dash="dash"), name=f"Actual {label}"), row=1, col=1)

    fig.add_trace(
        go.Scatter(
            x=ideal["s"], y=ideal["T"], mode="markers+text", text=["1", "2", "3", "4"],
            textposition="top center", marker=dict(size=9), name="Ideal states"
        ), row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=actual["s"], y=actual["T"], mode="markers+text", text=["1'", "2'", "3'", "4'"],
            textposition="bottom center", marker=dict(size=9, symbol="diamond"), name="Actual states"
        ), row=1, col=1,
    )

    # P-v diagram
    for k, label, color in zip(proc_keys, proc_labels, colors):
        _, _, p_i, v_i = ideal["segments"][k]
        _, _, p_a, v_a = actual["segments"][k]
        fig.add_trace(go.Scatter(x=v_i, y=p_i, mode="lines", line=dict(width=3, color=color), name=f"Ideal {label}", showlegend=False), row=1, col=2)
        fig.add_trace(go.Scatter(x=v_a, y=p_a, mode="lines", line=dict(width=2, color=color, dash="dash"), name=f"Actual {label}", showlegend=False), row=1, col=2)

    fig.add_trace(
        go.Scatter(
            x=ideal["v"], y=ideal["P"], mode="markers+text", text=["1", "2", "3", "4"],
            textposition="top center", marker=dict(size=9), name="Ideal states", showlegend=False
        ), row=1, col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=actual["v"], y=actual["P"], mode="markers+text", text=["1'", "2'", "3'", "4'"],
            textposition="bottom center", marker=dict(size=9, symbol="diamond"), name="Actual states", showlegend=False
        ), row=1, col=2,
    )

    fig.update_xaxes(title_text="s [kJ/kg-K, relative]", row=1, col=1)
    fig.update_yaxes(title_text="T [K]", row=1, col=1)
    fig.update_xaxes(title_text="v [relative units]", row=1, col=2)
    fig.update_yaxes(title_text="P [bar, normalized]", row=1, col=2)

    fig.update_layout(
        template="plotly_white", width=1280, height=560,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        title=(
            f"Ideal vs Actual Brayton Cycle | "
            f"η_ideal={100*ideal['eta']:.2f}% , η_actual={100*actual['eta']:.2f}%"
        ),
    )
    fig.show()
    return {"ideal": ideal, "actual": actual}
