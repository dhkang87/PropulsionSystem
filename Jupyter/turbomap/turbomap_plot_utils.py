"""
turbomap_plot_utils.py
Reusable compressor/turbine map visualization functions.

Style reference:
  - plot_compressor_map(): Cell-32 left-panel style (surge/choke/rpm/eff contours)
  - plot_compressor_overlay(): Cell-42 style (base vs scaled, 2-panel overlay)
  - plot_turbine_maps_2x2(): 2×2 GGT/FPT layout (top=Wc, bottom=eta)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.tri import Triangulation


def plot_compressor_map(
    Wc, PR, Eta, Nc_norm, *,
    NmechDes=41730.0,
    design_point=None,
    title="Compressor Map (Scaled)",
    figsize=(9, 7),
    x_margin_ratio=0.15,
    eff_levels=12,
    ax=None,
):
    """
    Plot a single compressor map with surge/choke lines, constant speed lines
    with RPM labels, and isentropic efficiency contours.
    """
    created_fig = ax is None
    if created_fig:
        fig, ax = plt.subplots(1, 1, figsize=figsize, constrained_layout=True)
    else:
        fig = ax.get_figure()

    rpm = np.asarray(Nc_norm) * NmechDes

    # Efficiency contour lines (goldenrod)
    wc_f = np.asarray(Wc).ravel()
    pr_f = np.asarray(PR).ravel()
    eta_f = np.asarray(Eta).ravel()
    mask = np.isfinite(wc_f) & np.isfinite(pr_f) & np.isfinite(eta_f) & (wc_f > 0) & (pr_f > 0)
    if np.count_nonzero(mask) > 10:
        tri = Triangulation(wc_f[mask], pr_f[mask])
        e_min, e_max = float(np.nanmin(eta_f[mask])), float(np.nanmax(eta_f[mask]))
        if e_max > e_min:
            levels = np.linspace(e_min, e_max, eff_levels)
            cset = ax.tricontour(tri, eta_f[mask], levels=levels, colors='goldenrod', linewidths=0.8, alpha=0.95)
            ax.clabel(cset, inline=True, fontsize=7, fmt='%.3g')

    # Constant speed lines with RPM labels
    for i in range(len(Nc_norm)):
        ax.plot(Wc[i, :], PR[i, :], color='dodgerblue', lw=0.9, alpha=0.9)
        lbl_j = min(int(0.80 * (Wc.shape[1] - 1)), Wc.shape[1] - 1)
        ax.text(Wc[i, lbl_j], PR[i, lbl_j], f"{int(round(rpm[i]))}",
                fontsize=10, color='0.2', ha='center', va='bottom')

    # Surge line (last Rline column)
    ax.plot(Wc[:, -1], PR[:, -1], 'r--', lw=1.6, alpha=0.85)
    # Choke line (first Rline column)
    ax.plot(Wc[:, 0], PR[:, 0], 'm-', lw=1.2, alpha=0.9)

    # Design point marker
    if design_point is not None:
        ax.plot(float(design_point['Wc']), float(design_point['PR']),
                marker='D', ms=8, color='tab:red', mec='k', mew=0.6, zorder=5)

    # Legend
    handles = [
        Line2D([0], [0], color='goldenrod', lw=1.0, label='Isentropic Efficiency'),
        Line2D([0], [0], color='m', lw=1.2, label='Choke Line'),
        Line2D([0], [0], color='r', lw=1.6, linestyle='--', label='Surge Line'),
        Line2D([0], [0], color='dodgerblue', lw=1.0, label='Constant Speed Lines (rpm)'),
    ]
    if design_point is not None:
        handles.append(
            Line2D([0], [0], marker='D', color='none', markerfacecolor='tab:red',
                   markeredgecolor='k', markersize=8, label='Design Point')
        )
    ax.legend(handles=handles, fontsize=9, loc='upper center',
              frameon=True, fancybox=False, framealpha=1.0, edgecolor='0.6',
              borderpad=0.3, handlelength=2.8, labelspacing=0.25, handletextpad=0.5)

    ax.set_title(title, fontsize=12)
    ax.set_xlabel('Corrected Mass Flow Wc [kg/s]')
    ax.set_ylabel('Pressure Ratio PR [-]')
    ax.grid(True, alpha=0.3)

    wc_min, wc_max = float(np.nanmin(Wc)), float(np.nanmax(Wc))
    margin = (wc_max - wc_min) * x_margin_ratio
    ax.set_xlim(max(0, wc_min - margin), wc_max + margin)

    return fig, ax


def plot_compressor_overlay(
    Wc_base, PR_base, Eta_base, Nc_base,
    Wc_scaled_actual, Wc_scaled_corr, PR_scaled, Eta_scaled, Nc_scaled,
    *,
    base_design=None, scaled_design_actual=None, scaled_design_corr=None,
    show_base=True,
    suptitle="Compressor Map Overlay: Base vs Scaled",
    figsize=(14, 5.5), eta_levels=10,
):
    """Plot 2-panel overlay: (left) actual flow, (right) corrected flow."""
    if show_base:
        eta_min = min(np.nanmin(Eta_base), np.nanmin(Eta_scaled))
        eta_max = max(np.nanmax(Eta_base), np.nanmax(Eta_scaled))
    else:
        eta_min = float(np.nanmin(Eta_scaled))
        eta_max = float(np.nanmax(Eta_scaled))
    levels = np.linspace(eta_min, eta_max, eta_levels)

    fig, axes = plt.subplots(1, 2, figsize=figsize, constrained_layout=True)

    # (A) Actual-flow overlay
    ax = axes[0]
    if show_base:
        for i in range(len(Nc_base)):
            ax.plot(Wc_base[i, :], PR_base[i, :], color="tab:blue", lw=1.3, alpha=0.95)
    for i in range(len(Nc_scaled)):
        ax.plot(Wc_scaled_actual[i, :], PR_scaled[i, :], color="tab:red", lw=1.2, ls="--", alpha=0.95)

    if show_base:
        ax.contour(Wc_base, PR_base, Eta_base, levels=levels, colors="tab:blue", linewidths=0.7, alpha=0.40)
    ax.contour(Wc_scaled_actual, PR_scaled, Eta_scaled, levels=levels, colors="tab:red", linewidths=0.7, linestyles="--", alpha=0.40)

    ax.plot(Wc_scaled_actual[:, -1], PR_scaled[:, -1], 'r--', lw=1.4, alpha=0.8)
    ax.plot(Wc_scaled_actual[:, 0], PR_scaled[:, 0], 'm-', lw=1.0, alpha=0.8)
    if show_base:
        ax.plot(Wc_base[:, -1], PR_base[:, -1], color="tab:blue", lw=1.2, ls=":", alpha=0.6)
        ax.plot(Wc_base[:, 0], PR_base[:, 0], color="tab:blue", lw=0.9, ls=":", alpha=0.6)

    if base_design:
        ax.plot(float(base_design['Wc']), float(base_design['PR']), marker="o", ms=7, color="tab:blue", mec="k", mew=0.5)
    if scaled_design_actual:
        ax.plot(float(scaled_design_actual['Wc']), float(scaled_design_actual['PR']), marker="D", ms=7, color="tab:red", mec="k", mew=0.5)

    ax.set_title("Overlay (Actual flow axis)")
    ax.set_xlabel("Flow [kg/s] (actual)")
    ax.set_ylabel("Pressure Ratio [-]")
    ax.grid(True, alpha=0.25)

    legend_a = []
    if show_base:
        legend_a.append(Line2D([0], [0], color="tab:blue", lw=1.5, label="Base map"))
    legend_a.append(Line2D([0], [0], color="tab:red", lw=1.5, ls="--", label="Scaled (actual)"))
    legend_a.append(Line2D([0], [0], color="r", lw=1.4, ls="--", label="Surge line"))
    legend_a.append(Line2D([0], [0], color="m", lw=1.0, label="Choke line"))
    if base_design:
        legend_a.append(Line2D([0], [0], marker="o", color="none", markerfacecolor="tab:blue", markeredgecolor="k", markersize=7, label="Base design point"))
    if scaled_design_actual:
        legend_a.append(Line2D([0], [0], marker="D", color="none", markerfacecolor="tab:red", markeredgecolor="k", markersize=7, label="Scaled design target"))
    ax.legend(handles=legend_a, loc="best", fontsize=9)

    # (B) Corrected-flow overlay
    ax = axes[1]
    if show_base:
        for i in range(len(Nc_base)):
            ax.plot(Wc_base[i, :], PR_base[i, :], color="tab:blue", lw=1.3, alpha=0.95)
    for i in range(len(Nc_scaled)):
        ax.plot(Wc_scaled_corr[i, :], PR_scaled[i, :], color="tab:green", lw=1.2, ls="--", alpha=0.95)

    if show_base:
        ax.contour(Wc_base, PR_base, Eta_base, levels=levels, colors="tab:blue", linewidths=0.7, alpha=0.40)
    ax.contour(Wc_scaled_corr, PR_scaled, Eta_scaled, levels=levels, colors="tab:green", linewidths=0.7, linestyles="--", alpha=0.40)

    ax.plot(Wc_scaled_corr[:, -1], PR_scaled[:, -1], 'r--', lw=1.4, alpha=0.8)
    ax.plot(Wc_scaled_corr[:, 0], PR_scaled[:, 0], 'm-', lw=1.0, alpha=0.8)
    if show_base:
        ax.plot(Wc_base[:, -1], PR_base[:, -1], color="tab:blue", lw=1.2, ls=":", alpha=0.6)
        ax.plot(Wc_base[:, 0], PR_base[:, 0], color="tab:blue", lw=0.9, ls=":", alpha=0.6)

    if base_design:
        ax.plot(float(base_design['Wc']), float(base_design['PR']), marker="o", ms=7, color="tab:blue", mec="k", mew=0.5)
    if scaled_design_corr:
        ax.plot(float(scaled_design_corr['Wc']), float(scaled_design_corr['PR']), marker="D", ms=7, color="tab:green", mec="k", mew=0.5)

    ax.set_title("Overlay (Corrected flow axis)")
    ax.set_xlabel("Flow [kg/s] (corrected)")
    ax.set_ylabel("Pressure Ratio [-]")
    ax.grid(True, alpha=0.25)

    legend_b = []
    if show_base:
        legend_b.append(Line2D([0], [0], color="tab:blue", lw=1.5, label="Base map"))
    legend_b.append(Line2D([0], [0], color="tab:green", lw=1.5, ls="--", label="Scaled (corrected)"))
    legend_b.append(Line2D([0], [0], color="r", lw=1.4, ls="--", label="Surge line"))
    legend_b.append(Line2D([0], [0], color="m", lw=1.0, label="Choke line"))
    if base_design:
        legend_b.append(Line2D([0], [0], marker="o", color="none", markerfacecolor="tab:blue", markeredgecolor="k", markersize=7, label="Base design point"))
    if scaled_design_corr:
        legend_b.append(Line2D([0], [0], marker="D", color="none", markerfacecolor="tab:green", markeredgecolor="k", markersize=7, label="Scaled design target"))
    ax.legend(handles=legend_b, loc="best", fontsize=9)

    fig.suptitle(suptitle, fontsize=13)
    return fig, axes


def plot_turbine_maps_2x2(
    scaled_maps: dict, *,
    suptitle="TPE331 Turbine Map Scaling (GGT / FPT)",
    figsize=(14, 10), colors=None, NmechDes_dict=None,
):
    """
    Plot GGT/FPT turbine maps in a 2×2 layout.
    Top row: x=PR, y=Corrected Wc.  Bottom row: x=PR, y=Efficiency.
    """
    keys = [k for k in ["GGT", "FPT"] if k in scaled_maps]
    if not keys:
        raise ValueError("scaled_maps must contain at least one of 'GGT', 'FPT'")

    if colors is None:
        colors = {"GGT": "tab:red", "FPT": "tab:purple"}
    if NmechDes_dict is None:
        NmechDes_dict = {"GGT": 40000.0, "FPT": 30000.0}

    n_cols = len(keys)
    fig, axes = plt.subplots(2, n_cols, figsize=figsize, constrained_layout=True, squeeze=False)
    title_labels = {"GGT": "Gas Generator Turbine", "FPT": "Free Power Turbine"}

    for col, key in enumerate(keys):
        d = scaled_maps[key]
        color = colors.get(key, "tab:red")
        nmech = NmechDes_dict.get(key, 40000.0)
        rpm_arr = d["nc"] * nmech

        wc_corr = d["wc_scaled_corr"]
        pr = d["pr_scaled"]
        eta = d["eta_scaled"]
        trg = d["target"]
        wc_des = d.get("wc_target_corr", trg.get("wc_target_corr", 0))

        # Top row: x=PR, y=corrected Wc
        ax_wc = axes[0, col]
        for i in range(len(d["nc"])):
            ax_wc.plot(pr[i, :], wc_corr[i, :], color=color, lw=1.25, ls="--", alpha=0.95)
            lbl_j = min(int(0.70 * (pr.shape[1] - 1)), pr.shape[1] - 1)
            ax_wc.text(pr[i, lbl_j], wc_corr[i, lbl_j],
                       f"{int(round(rpm_arr[i]))}", fontsize=8, color="0.2", ha="left", va="bottom")
        ax_wc.plot(float(trg["PRdes"]), float(wc_des), marker="D", ms=7, color=color, mec="k", mew=0.5, zorder=5)
        ax_wc.set_title(f"{key} ({title_labels.get(key, key)}) — Corrected Flow")
        ax_wc.set_xlabel("Pressure Ratio [-]")
        ax_wc.set_ylabel("Corrected Mass Flow Wc [kg/s]")
        ax_wc.grid(True, alpha=0.25)
        ax_wc.legend(handles=[
            Line2D([0], [0], color=color, lw=1.5, ls="--", label=f"{key} scaled speed lines"),
            Line2D([0], [0], marker="D", color="none", markerfacecolor=color, markeredgecolor="k", markersize=7, label="TPE331 design target"),
        ], loc="best", fontsize=8)

        # Bottom row: x=PR, y=efficiency
        ax_eta = axes[1, col]
        for i in range(len(d["nc"])):
            ax_eta.plot(pr[i, :], eta[i, :], color=color, lw=1.25, ls="--", alpha=0.95)
            lbl_j = min(int(0.55 * (pr.shape[1] - 1)), pr.shape[1] - 1)
            ax_eta.text(pr[i, lbl_j], eta[i, lbl_j],
                        f"{int(round(rpm_arr[i]))}", fontsize=8, color="0.2", ha="left", va="bottom")
        ax_eta.plot(float(trg["PRdes"]), float(trg["effDes"]), marker="D", ms=7, color=color, mec="k", mew=0.5, zorder=5)
        ax_eta.set_title(f"{key} ({title_labels.get(key, key)}) — Isentropic Efficiency")
        ax_eta.set_xlabel("Pressure Ratio [-]")
        ax_eta.set_ylabel("Isentropic Efficiency [-]")
        ax_eta.grid(True, alpha=0.25)
        ax_eta.legend(handles=[
            Line2D([0], [0], color=color, lw=1.5, ls="--", label=f"{key} efficiency (scaled)"),
            Line2D([0], [0], marker="D", color="none", markerfacecolor=color, markeredgecolor="k", markersize=7, label="TPE331 design eff"),
        ], loc="best", fontsize=8)

    fig.suptitle(suptitle, fontsize=12)
    return fig, axes
