"""Shared Plotly style helpers for TwinBuilder notebooks."""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

MATLAB_BG = "#e6e6e6"
MATLAB_GRID = "#bcbcbc"
MATLAB_EFF_SCALE = [
    [0.0, "#f2b94b"],
    [1.0, "#e39b2e"],
]
MATLAB_SPEED = "#0072BD"
MATLAB_CHOKE = "#b2182b"
MATLAB_SURGE = "#7a0177"


def build_matlab_compressor_template() -> go.layout.Template:
    """Return a MATLAB-like template for compressor-map style plots."""
    return go.layout.Template(
        layout=dict(
            paper_bgcolor=MATLAB_BG,
            plot_bgcolor=MATLAB_BG,
            font=dict(color="black"),
            xaxis=dict(
                gridcolor=MATLAB_GRID,
                zeroline=False,
                showline=True,
                linecolor="#777777",
                mirror=True,
            ),
            yaxis=dict(
                gridcolor=MATLAB_GRID,
                zeroline=False,
                showline=True,
                linecolor="#777777",
                mirror=True,
            ),
            legend=dict(
                x=0.98,
                y=0.02,
                xanchor="right",
                yanchor="bottom",
                bgcolor="rgba(245,245,245,0.92)",
                bordercolor="#7f7f7f",
                borderwidth=1,
            ),
        )
    )


def register_project_templates(set_default: bool = True) -> None:
    """Register project templates once per kernel session."""
    pio.templates["matlab_compressor"] = build_matlab_compressor_template()
    if set_default:
        pio.templates.default = "matlab_compressor"


def apply_compressor_map_style(
    fig: go.Figure,
    title: str = "Compressor Map",
    x_title: str = "Corrected Mass Flow Rate (kg/s)",
    y_title: str = "Pressure Ratio",
    width: int = 1200,
    height: int = 700,
) -> go.Figure:
    """Apply a consistent compressor-map layout to any Plotly figure."""
    fig.update_layout(
        template="matlab_compressor",
        width=width,
        height=height,
        title=dict(text=title, x=0.5),
    )
    fig.update_xaxes(title_text=x_title)
    fig.update_yaxes(title_text=y_title)
    return fig
