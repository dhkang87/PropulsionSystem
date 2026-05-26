"""
tb_postproc.py
Twin Builder Modelica simulation post-processing: signal discovery, collection, and verification.

Usage:
    from tb_postproc import TBPostProcessor

    pp = TBPostProcessor(
        project=r"E:\\KDH\\simTemp\\TB\\Turbo.aedt",
        design="TPE331_ex1a",
    )
    pp.connect()
    pp.discover_signals()
    mdf = pp.collect_signals()
    pp.plot_transient()
    pp.verify_power_balance(J_shaft=0.5)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ═══════════════════════════════════════════════════════════════════════════
# Signal filter configuration
# ═══════════════════════════════════════════════════════════════════════════

EXCLUDE_PATTERNS = [
    r"combiTable", r"table_\d", r"tableOnFile", r"interpol",
    r"_iderState", r"_tableID", r"smoothness", r"extrapolation",
    r"columns\[", r"fileName", r"verboseRead", r"tableName",
]

KEY_SUFFIXES: dict[str, str] = {
    # ── Modelica (PropulsionSystem / NPSS-style) ──
    "pwr": "Power [W]",
    "trq": "Torque [N.m]",
    "w": "Angular velocity [rad/s]",
    "Nmech": "Mech speed [rpm]",
    "omega": "Omega [rad/s]",
    "PR": "Pressure Ratio [-]",
    "eff": "Efficiency [-]",
    "Wc_1": "Corrected flow [kg/s]",
    "Nc_1": "Corrected speed [rpm]",
    "Fg": "Gross thrust [N]",
    "y_Fg": "Gross thrust (output) [N]",
    "Fn": "Net thrust [N]",
    "y_Fn": "Net thrust (output) [N]",
    "TSFC": "TSFC [kg/(N.s)]",
    "y_TSFC": "TSFC (output)",
    "y_FdRam": "Ram drag [N]",
    "V_2": "Nozzle exit velocity [m/s]",
    "y_m_flow_fuel": "Fuel flow [kg/s]",
    "m_flow": "Mass flow [kg/s]",
    "fluid_1_T": "Inlet temp [K]",
    "fluid_2_T": "Outlet temp [K]",
    "port_1_p": "Inlet pressure [Pa]",
    "port_2_p": "Outlet pressure [Pa]",
    "effComb": "Combustion eff [-]",
    "NcqNcDes_1": "Nc/Nc_des [-]",
    "NqNdes": "N/N_des [-]",
    "Rline": "R-line [-]",
    # ── VHDL-AMS (Twin Builder GT components) ──
    "t_out": "Outlet temp [K]",
    "t_in": "Inlet temp [K]",
    "p_out": "Outlet pressure [Pa]",
    "p_in": "Inlet pressure [Pa]",
    "power": "Power [W]",
    "torque": "Torque [N.m]",
    "temp_diff": "Temperature diff [K]",
    "fa_ratio": "Fuel-air ratio [-]",
    "mflow": "Mass flow [kg/s]",
    "mflow_fuel": "Fuel flow [kg/s]",
    "thrust": "Thrust [N]",
    "eta": "Efficiency [-]",
    "eta_comp": "Compressor isentropic efficiency [-]",
    "eta_t": "Turbine isentropic efficiency [-]",
    "eta_m": "Mechanical efficiency [-]",
}


@dataclass
class VerificationResult:
    """Quantitative verification output."""
    steady_state: dict[str, float] = field(default_factory=dict)
    power_balance_pct: float | None = None
    thrust_residual_max: float | None = None
    passed: bool = False
    notes: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# Signal mapping configuration
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SignalMap:
    """
    Maps physical quantities to platform-specific column name patterns.

    Each field is a list of candidate patterns passed to ``find_col()``.
    Use classmethods for platform presets.
    """

    omega: list[str] = field(default_factory=list)
    Nmech: list[str] = field(default_factory=list)
    P_cmp: list[str] = field(default_factory=list)
    P_trb: list[str] = field(default_factory=list)
    PR_cmp: list[str] = field(default_factory=list)
    PR_trb: list[str] = field(default_factory=list)
    eff_cmp: list[str] = field(default_factory=list)
    eff_trb: list[str] = field(default_factory=list)
    Fg: list[str] = field(default_factory=list)
    T_trb_in: list[str] = field(default_factory=list)
    T_trb_out: list[str] = field(default_factory=list)
    T_cmp_out: list[str] = field(default_factory=list)
    Wc_cmp: list[str] = field(default_factory=list)
    Nc_cmp: list[str] = field(default_factory=list)
    stations: dict[str, dict[str, list[str]]] = field(default_factory=dict)

    @classmethod
    def modelica(cls) -> "SignalMap":
        """Modelica (PropulsionSystem / NPSS-style) naming."""
        return cls(
            omega=["inertia1_w", "ShaftGG_w", "Shaft_w", "inertia_w"],
            Nmech=["Cmp_Nmech", "Cmp.Nmech"],
            P_cmp=["Cmp_pwr", "Cmp.pwr"],
            P_trb=["GGT_pwr", "Trb_pwr", "Trb.pwr"],
            PR_cmp=["Cmp_PR"],
            PR_trb=["GGT_PR", "Trb_PR"],
            eff_cmp=["Cmp_eff"],
            eff_trb=["GGT_eff", "Trb_eff"],
            Fg=["Nzl_y_Fg", "Nzl_Fg"],
            T_trb_in=["GGT_fluid_1_T", "Trb_fluid_1_T"],
            T_trb_out=["GGT_fluid_2_T", "Trb_fluid_2_T"],
            T_cmp_out=["Cmp_fluid_2_T"],
            Wc_cmp=["Cmp_Wc_1", "Cmp_Wc"],
            Nc_cmp=["Cmp_Nc_1", "Cmp_Nc"],
            stations={
                "1 (Inlet)": {
                    "T_patterns": ["Cmp_fluid_1_T", "Inlt_fluid_2_T"],
                    "p_patterns": ["Cmp_port_1_p", "Inlt_port_2_p"],
                },
                "2 (Cmp exit)": {
                    "T_patterns": ["Cmp_fluid_2_T"],
                    "p_patterns": ["Cmp_port_2_p"],
                },
                "3 (TIT)": {
                    "T_patterns": ["GGT_fluid_1_T", "Trb_fluid_1_T"],
                    "p_patterns": ["GGT_port_1_p", "Trb_port_1_p"],
                },
                "4 (Trb exit)": {
                    "T_patterns": ["GGT_fluid_2_T", "Trb_fluid_2_T", "FPT_fluid_2_T"],
                    "p_patterns": ["GGT_port_2_p", "Trb_port_2_p", "FPT_port_2_p", "Nzl_port_1_p"],
                },
                "5 (Nzl exit)": {
                    "T_patterns": ["Nzl_fluid_2_T"],
                    "p_patterns": ["Nzl_port_2_p"],
                },
            },
        )

    @classmethod
    def vhdl_ams(cls) -> "SignalMap":
        """VHDL-AMS (Twin Builder GT components) naming."""
        return cls(
            omega=["mass_rot1.omega"],
            Nmech=[],
            P_cmp=["compressor1.power"],
            P_trb=["turbine1.power"],
            PR_cmp=[],
            PR_trb=[],
            eff_cmp=["compressor1.eta_comp"],
            eff_trb=["turbine1.eta_t", "turbine1.eta_m"],
            Fg=["nozzle1.thrust"],
            T_trb_in=["combustor1.t_out"],
            T_trb_out=["turbine1.t_out"],
            T_cmp_out=["compressor1.t_out"],
            Wc_cmp=[],
            Nc_cmp=[],
            stations={
                "1 (Inlet)": {
                    "T_patterns": ["inlet1.t_out"],
                    "p_patterns": ["inlet1.p_out"],
                },
                "2 (Cmp exit)": {
                    "T_patterns": ["compressor1.t_out"],
                    "p_patterns": ["compressor1.p_out"],
                },
                "3 (TIT)": {
                    "T_patterns": ["combustor1.t_out"],
                    "p_patterns": ["combustor1.p_out"],
                },
                "4 (Trb exit)": {
                    "T_patterns": ["turbine1.t_out"],
                    "p_patterns": ["turbine1.p_out"],
                },
            },
        )

    @classmethod
    def merged(cls) -> "SignalMap":
        """Combined Modelica + VHDL-AMS patterns (default)."""
        m = cls.modelica()
        v = cls.vhdl_ams()
        return cls(
            omega=m.omega + v.omega,
            Nmech=m.Nmech + v.Nmech,
            P_cmp=m.P_cmp + v.P_cmp,
            P_trb=m.P_trb + v.P_trb,
            PR_cmp=m.PR_cmp + v.PR_cmp,
            PR_trb=m.PR_trb + v.PR_trb,
            eff_cmp=m.eff_cmp + v.eff_cmp,
            eff_trb=m.eff_trb + v.eff_trb,
            Fg=m.Fg + v.Fg,
            T_trb_in=m.T_trb_in + v.T_trb_in,
            T_trb_out=m.T_trb_out + v.T_trb_out,
            T_cmp_out=m.T_cmp_out + v.T_cmp_out,
            Wc_cmp=m.Wc_cmp + v.Wc_cmp,
            Nc_cmp=m.Nc_cmp + v.Nc_cmp,
            stations={k: {
                "T_patterns": m.stations.get(k, {}).get("T_patterns", []) + v.stations.get(k, {}).get("T_patterns", []),
                "p_patterns": m.stations.get(k, {}).get("p_patterns", []) + v.stations.get(k, {}).get("p_patterns", []),
            } for k in dict.fromkeys(list(m.stations) + list(v.stations))},
        )


# ═══════════════════════════════════════════════════════════════════════════
# Main class
# ═══════════════════════════════════════════════════════════════════════════

class TBPostProcessor:
    """Twin Builder Modelica result post-processor."""

    def __init__(
        self,
        project: str | Path,
        design: str,
        *,
        aedt_version: str = "2026.1",
        non_graphical: bool = False,
        signal_map: SignalMap | None = None,
    ):
        self.project = str(Path(project).resolve())
        self.design = design
        self.aedt_version = aedt_version
        self.non_graphical = non_graphical
        self.signal_map = signal_map or SignalMap.merged()

        self._tb: Any = None
        self._all_exprs: list[str] = []
        self._selected: dict[str, tuple[str, str]] = {}  # expr → (suffix, desc)
        self._setup_name: str = "TR"
        self.mdf: pd.DataFrame | None = None

    # ── Connection ──────────────────────────────────────────────────────

    def connect(self, new_desktop: bool = False) -> "TBPostProcessor":
        """Connect to an open AEDT project."""
        try:
            from ansys.aedt.core import TwinBuilder
        except ImportError:
            from pyaedt import TwinBuilder

        self._tb = TwinBuilder(
            project=self.project,
            design=self.design,
            non_graphical=self.non_graphical,
            new_desktop=new_desktop,
            version=self.aedt_version,
        )
        print(f"Connected: {self._tb.project_name} / {self._tb.design_name}")
        return self

    def attach(self, tb_obj: Any) -> "TBPostProcessor":
        """Attach an already-connected TwinBuilder object."""
        self._tb = tb_obj
        return self

    # ── Signal discovery ────────────────────────────────────────────────

    def discover_signals(self) -> list[str]:
        """Discover available signals and filter to key physics quantities."""
        post = self._tb.post
        solutions = self._read_attr(post, "available_report_solutions")
        self._setup_name = solutions[0] if solutions else "TR"

        # Collect all expressions
        self._all_exprs = self._collect_all_expressions(post, solutions)
        print(f"Total expressions: {len(self._all_exprs)}")

        # Filter
        exclude_re = re.compile("|".join(EXCLUDE_PATTERNS), re.IGNORECASE)
        filtered = [e for e in self._all_exprs if not exclude_re.search(e)]
        print(f"After exclusion: {len(filtered)} (removed {len(self._all_exprs)-len(filtered)} internal)")

        # Match key suffixes
        self._selected = {}
        for expr in filtered:
            suffix, desc = self._match_key(expr)
            if suffix:
                self._selected[expr] = (suffix, desc)

        print(f"Selected key signals: {len(self._selected)}")
        return list(self._selected.keys())

    # ── Data collection ─────────────────────────────────────────────────

    def collect_signals(self, expressions: list[str] | None = None) -> pd.DataFrame:
        """Collect time-domain data for selected signals into a DataFrame."""
        exprs = expressions or list(self._selected.keys())
        if not exprs:
            raise ValueError("No signals to collect. Run discover_signals() first.")

        merged = None
        found, missing = [], []

        for expr in exprs:
            t, y = self._get_signal(expr)
            if t is None:
                missing.append(expr)
                continue
            found.append(expr)
            df_sig = pd.DataFrame({"time": t, expr: y}).dropna()
            if merged is None:
                merged = df_sig
            else:
                merged = merged.merge(df_sig, on="time", how="outer")

        if merged is not None:
            merged = merged.sort_values("time").drop_duplicates(subset=["time"]).reset_index(drop=True)
            # Time scale correction: TB/AEDT returns time in nanoseconds (ns)
            t_arr = merged["time"].to_numpy(dtype=float)
            t_span = float(np.nanmax(t_arr) - np.nanmin(t_arr))
            if t_span > 1e6:
                merged["time"] = merged["time"] * 1e-9  # ns → s
                t_span_s = t_span * 1e-9
                print(f"Time axis: ns -> s (raw span={t_span:.2e} ns = {t_span_s:.2f} s)")
            print(f"Collected: {len(merged)} steps, {len(found)} signals ({len(missing)} missing)")
        else:
            print("No time-domain data retrieved!")
            merged = pd.DataFrame()

        self.mdf = merged
        return merged

    # ── Column finder ───────────────────────────────────────────────────

    def find_col(self, patterns: list[str]) -> str | None:
        """Find a column in mdf matching any of the patterns (. and _ equivalent)."""
        if self.mdf is None:
            return None
        cols = [c for c in self.mdf.columns if c != "time"]
        for p in patterns:
            p_norm = p.lower().replace(".", "_")
            for c in cols:
                c_norm = c.lower().replace(".", "_")
                if p_norm in c_norm:
                    return c
        return None

    # ── Plotting ────────────────────────────────────────────────────────

    def plot_transient(self, J_shaft: float = 0.5, title: str | None = None):
        """Plot 4x2 transient analysis dashboard."""
        import matplotlib.pyplot as plt

        if self.mdf is None or self.mdf.empty:
            raise ValueError("No data. Run collect_signals() first.")

        mdf = self.mdf
        t = mdf["time"].to_numpy()
        fc = self.find_col

        sm = self.signal_map
        col_omega = fc(sm.omega)
        col_Nmech = fc(sm.Nmech)
        col_P_cmp = fc(sm.P_cmp)
        col_P_trb = fc(sm.P_trb)
        col_PR_cmp = fc(sm.PR_cmp)
        col_PR_trb = fc(sm.PR_trb)
        col_eff_cmp = fc(sm.eff_cmp)
        col_eff_trb = fc(sm.eff_trb)
        col_Fg = fc(sm.Fg)
        col_T_trb_in = fc(sm.T_trb_in)
        col_T_trb_out = fc(sm.T_trb_out)
        col_T_cmp_out = fc(sm.T_cmp_out)
        col_Wc_cmp = fc(sm.Wc_cmp)
        col_Nc_cmp = fc(sm.Nc_cmp)

        fig_title = title or f"{self.design} — Transient Analysis"
        fig, axes = plt.subplots(4, 2, figsize=(16, 18))
        fig.suptitle(fig_title, fontsize=14, y=0.995)

        # (a) Shaft speed
        ax = axes[0, 0]
        if col_omega:
            omega_arr = mdf[col_omega].to_numpy(dtype=float)
            ax.plot(t, omega_arr * 60 / (2 * np.pi), "b-", lw=1.5)
        elif col_Nmech:
            ax.plot(t, mdf[col_Nmech], "b-", lw=1.5)
        ax.set_ylabel("Shaft Speed [rpm]")
        ax.set_title("(a) Shaft Speed")
        ax.grid(True, alpha=0.3)

        # (b) Power
        ax = axes[0, 1]
        if col_P_trb:
            ax.plot(t, mdf[col_P_trb] / 1e3, "r-", lw=1.5, label="Turbine")
        if col_P_cmp:
            ax.plot(t, mdf[col_P_cmp] / 1e3, "b-", lw=1.5, label="Compressor")
        ax.axhline(0, color="k", lw=0.5, ls=":")
        ax.set_ylabel("Power [kW]")
        ax.set_title("(b) Power")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # (c) Pressure ratio
        ax = axes[1, 0]
        if col_PR_cmp:
            ax.plot(t, mdf[col_PR_cmp], "b-", lw=1.5, label="Cmp PR")
        if col_PR_trb:
            ax.plot(t, mdf[col_PR_trb], "r-", lw=1.5, label="Trb PR")
        ax.set_ylabel("Pressure Ratio [-]")
        ax.set_title("(c) Pressure Ratio")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # (d) Thrust
        ax = axes[1, 1]
        if col_Fg:
            ax.plot(t, mdf[col_Fg], "g-", lw=1.5, label="Fg")
        ax.set_ylabel("Force [N]")
        ax.set_title("(d) Thrust / Gross")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # (e) Temperature
        ax = axes[2, 0]
        for col, lbl in [(col_T_cmp_out, "Cmp exit"), (col_T_trb_in, "TIT"), (col_T_trb_out, "Trb exit")]:
            if col:
                ax.plot(t, mdf[col], lw=1.5, label=lbl)
        ax.set_ylabel("Temperature [K]")
        ax.set_title("(e) Gas Path Temperatures")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # (f) Efficiency
        ax = axes[2, 1]
        if col_eff_cmp:
            ax.plot(t, mdf[col_eff_cmp], "b-", lw=1.5, label="eta_cmp")
        if col_eff_trb:
            ax.plot(t, mdf[col_eff_trb], "r-", lw=1.5, label="eta_trb")
        ax.set_ylabel("Efficiency [-]")
        ax.set_title("(f) Isentropic Efficiency")
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

        # (g) Corrected quantities
        ax = axes[3, 0]
        if col_Wc_cmp:
            ax.plot(t, mdf[col_Wc_cmp], "b-", lw=1.5, label="Wc_cmp")
        if col_Nc_cmp:
            ax2 = ax.twinx()
            ax2.plot(t, mdf[col_Nc_cmp], "r--", lw=1, label="Nc_cmp")
            ax2.set_ylabel("Nc [rpm]")
            ax2.legend(loc="upper right", fontsize=8)
        ax.set_ylabel("Wc [kg/s]")
        ax.set_title("(g) Corrected Quantities")
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)

        # (h) Power balance
        ax = axes[3, 1]
        omega_src = col_omega or col_Nmech
        if col_P_trb and col_P_cmp and omega_src:
            omega_arr = mdf[omega_src].to_numpy(dtype=float)
            if omega_src == col_Nmech:
                omega_arr = omega_arr * 2 * np.pi / 60
            E_kin = 0.5 * J_shaft * omega_arr**2
            dEdt = np.gradient(E_kin, t, edge_order=1)
            P_t = mdf[col_P_trb].to_numpy(dtype=float)
            P_c = mdf[col_P_cmp].to_numpy(dtype=float)
            eps = P_t + P_c - dEdt
            ax.plot(t, eps, "r-", lw=1.2, label="P_trb+P_cmp-dE/dt")
            ax.axhline(0, color="k", lw=0.5, ls=":")
            ax.set_ylabel("Residual [W]")
            ax.set_title(f"(h) Power Balance (J={J_shaft})")
            ax.legend(fontsize=8)
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, "Insufficient signals", transform=ax.transAxes, ha="center")

        for a in axes[-1, :]:
            a.set_xlabel("time [s]")
        plt.tight_layout()
        plt.show()
        return fig

    # ── Thermodynamic cycle diagram ────────────────────────────────────

    def plot_cycle_diagram(
        self,
        ss_fraction: float = 0.1,
        cp: float = 1004.0,
        R_gas: float = 287.0,
        T_ref: float = 288.15,
        p_ref: float = 101325.0,
        stations: dict[str, dict] | None = None,
    ):
        """
        Plot T-s and p-v diagrams from steady-state station data.

        Parameters
        ----------
        ss_fraction : float
            Fraction of time series end used for steady-state averaging.
        cp, R_gas : float
            Ideal gas properties [J/(kg·K)].
        T_ref, p_ref : float
            Reference state for entropy calculation.
        stations : dict or None
            Override station definitions. Keys are station names,
            values are dicts with 'T_patterns' and 'p_patterns' (lists of column patterns).
            If None, auto-detects for single-spool (Cmp+GGT+Nzl) or twin-spool.
        """
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyArrowPatch

        if self.mdf is None or self.mdf.empty:
            raise ValueError("No data. Run collect_signals() first.")

        mdf = self.mdf
        t = mdf["time"].to_numpy()
        n_ss = max(1, int(len(t) * ss_fraction))
        fc = self.find_col

        def _ss(col):
            if col and col in mdf.columns:
                arr = mdf[col].to_numpy(dtype=float)[-n_ss:]
                return float(np.nanmean(arr))
            return None

        # Station definitions (auto-detect from signal_map)
        if stations is None:
            stations = self.signal_map.stations

        # Extract station data
        cycle_T, cycle_p = [], []
        labels = []
        for name, cfg in stations.items():
            T_col = fc(cfg["T_patterns"])
            p_col = fc(cfg["p_patterns"])
            T_val = _ss(T_col)
            p_val = _ss(p_col)
            if T_val is not None and p_val is not None:
                cycle_T.append(T_val)
                cycle_p.append(p_val)
                labels.append(name)

        if len(cycle_T) < 3:
            print(f"Only {len(cycle_T)} stations found — need at least 3 for cycle diagram.")
            print("Available columns:")
            for c in sorted(mdf.columns):
                if "fluid" in c.lower() or "port" in c.lower():
                    print(f"  {c}")
            return None

        cycle_T = np.array(cycle_T)
        cycle_p = np.array(cycle_p)

        # Compute thermodynamic properties
        # Entropy: s - s_ref = cp * ln(T/T_ref) - R * ln(p/p_ref)
        cycle_s = cp * np.log(cycle_T / T_ref) - R_gas * np.log(cycle_p / p_ref)
        # Specific volume: v = R*T / p
        cycle_v = R_gas * cycle_T / cycle_p

        # Close the cycle for plotting
        T_closed = np.append(cycle_T, cycle_T[0])
        p_closed = np.append(cycle_p, cycle_p[0])
        s_closed = np.append(cycle_s, cycle_s[0])
        v_closed = np.append(cycle_v, cycle_v[0])

        # Plot
        fig, (ax_ts, ax_pv) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f"{self.design} — Brayton Cycle Diagram (SS avg)", fontsize=13)

        # T-s diagram
        ax_ts.plot(s_closed, T_closed, "b-o", lw=2, markersize=8, zorder=3)
        for i, lbl in enumerate(labels):
            ax_ts.annotate(
                lbl, (cycle_s[i], cycle_T[i]),
                textcoords="offset points", xytext=(8, 8),
                fontsize=9, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", alpha=0.8),
            )
        ax_ts.set_xlabel("Specific Entropy  s [J/(kg·K)]")
        ax_ts.set_ylabel("Temperature  T [K]")
        ax_ts.set_title("T-s Diagram")
        ax_ts.grid(True, alpha=0.3)
        ax_ts.fill(s_closed, T_closed, alpha=0.1, color="blue")

        # p-v diagram
        ax_pv.plot(v_closed, p_closed / 1e3, "r-o", lw=2, markersize=8, zorder=3)
        for i, lbl in enumerate(labels):
            ax_pv.annotate(
                lbl, (cycle_v[i], cycle_p[i] / 1e3),
                textcoords="offset points", xytext=(8, 8),
                fontsize=9, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", alpha=0.8),
            )
        ax_pv.set_xlabel("Specific Volume  v [m³/kg]")
        ax_pv.set_ylabel("Pressure  p [kPa]")
        ax_pv.set_title("p-v Diagram")
        ax_pv.grid(True, alpha=0.3)
        ax_pv.fill(v_closed, p_closed / 1e3, alpha=0.1, color="red")

        plt.tight_layout()
        plt.show()

        # Print station table
        print("\n" + "=" * 65)
        print(f"  {'Station':<14s} {'T [K]':>8s} {'p [kPa]':>9s} {'s [J/kgK]':>10s} {'v [m³/kg]':>10s}")
        print("-" * 65)
        for i, lbl in enumerate(labels):
            print(f"  {lbl:<14s} {cycle_T[i]:8.1f} {cycle_p[i]/1e3:9.2f} {cycle_s[i]:10.1f} {cycle_v[i]:10.5f}")
        print("=" * 65)

        return fig

    # ── Verification ────────────────────────────────────────────────────

    def verify_power_balance(self, J_shaft: float = 0.5, ss_fraction: float = 0.1) -> VerificationResult:
        """Quantitative verification: power balance and steady-state values."""
        if self.mdf is None or self.mdf.empty:
            return VerificationResult(notes=["No data"])

        mdf = self.mdf
        t = mdf["time"].to_numpy()
        n_ss = max(1, int(len(t) * ss_fraction))
        fc = self.find_col
        result = VerificationResult()

        # Steady-state extraction
        def _ss(col):
            if col and col in mdf.columns:
                arr = mdf[col].to_numpy(dtype=float)[-n_ss:]
                return float(np.nanmean(arr))
            return None

        sm = self.signal_map
        col_omega = fc(sm.omega)
        col_Nmech = fc(sm.Nmech)
        col_P_cmp = fc(sm.P_cmp)
        col_P_trb = fc(sm.P_trb)
        col_PR_cmp = fc(sm.PR_cmp)
        col_eff_cmp = fc(sm.eff_cmp)
        col_T_trb_in = fc(sm.T_trb_in)
        col_Fg = fc(sm.Fg)

        omega_src = col_omega or col_Nmech
        if omega_src:
            v = _ss(omega_src)
            if v is not None:
                rpm = v * 60 / (2 * np.pi) if "nmech" not in omega_src.lower() else v
                result.steady_state["shaft_rpm"] = rpm

        for label, col, conv in [
            ("PR_cmp", col_PR_cmp, 1.0),
            ("eff_cmp", col_eff_cmp, 1.0),
            ("TIT_K", col_T_trb_in, 1.0),
            ("Fg_N", col_Fg, 1.0),
            ("P_cmp_kW", col_P_cmp, 1e-3),
            ("P_trb_kW", col_P_trb, 1e-3),
        ]:
            v = _ss(col)
            if v is not None:
                result.steady_state[label] = v * conv

        # Power balance
        if col_P_trb and col_P_cmp and omega_src:
            omega_arr = mdf[omega_src].to_numpy(dtype=float)
            if omega_src == col_Nmech:
                omega_arr = omega_arr * 2 * np.pi / 60
            E_kin = 0.5 * J_shaft * omega_arr**2
            dEdt = np.gradient(E_kin, t, edge_order=1)
            P_t = mdf[col_P_trb].to_numpy(dtype=float)
            P_c = mdf[col_P_cmp].to_numpy(dtype=float)
            eps = P_t + P_c - dEdt
            P_scale = max(np.nanmax(np.abs(P_t)), 1.0)
            eps_ss = eps[-n_ss:]
            result.power_balance_pct = float(np.nanmean(np.abs(eps_ss)) / P_scale * 100)
            result.notes.append(f"|eps_ss| = {result.power_balance_pct:.4f}%")

        # Pass/fail
        if result.power_balance_pct is not None:
            result.passed = result.power_balance_pct < 1.0
        else:
            result.notes.append("Cannot verify — insufficient signals")

        # Print summary
        print("=" * 60)
        print(f"  {self.design} — Verification Summary")
        print("=" * 60)
        print(f"  Time: {t[0]:.3f} ~ {t[-1]:.3f} s ({len(t)} steps)")
        print(f"  SS window: last {n_ss} steps")
        print(f"\n  Steady-state values:")
        for k, v in result.steady_state.items():
            print(f"    {k:14s}: {v:.4f}")
        if result.power_balance_pct is not None:
            status = "PASS" if result.passed else "FAIL"
            print(f"\n  Power balance: {result.power_balance_pct:.4f}% [{status}]")
        for note in result.notes:
            print(f"  Note: {note}")
        print("=" * 60)

        return result

    # ── Internal helpers ────────────────────────────────────────────────

    @staticmethod
    def _read_attr(obj, name):
        if not hasattr(obj, name):
            return []
        v = getattr(obj, name)
        try:
            r = v() if callable(v) else v
        except Exception:
            return []
        if r is None:
            return []
        return list(r) if isinstance(r, (list, tuple, set)) else [r]

    def _collect_all_expressions(self, post, solutions):
        exprs = []
        fn = getattr(post, "available_report_quantities", None)
        if not callable(fn):
            return []
        categories = self._read_attr(post, "available_quantities_categories")
        for sol in (solutions or [None]):
            for cat in (categories or [None]):
                for rpt in ["Standard", "Transient", None]:
                    kwargs = {}
                    if sol is not None:
                        kwargs["solution"] = sol
                    if cat is not None:
                        kwargs["quantities_category"] = cat
                    if rpt is not None:
                        kwargs["report_category"] = rpt
                    try:
                        got = fn(**kwargs)
                        if got:
                            exprs.extend(list(got))
                    except Exception:
                        continue
        return sorted(set(exprs))

    @staticmethod
    def _match_key(expr: str) -> tuple[str | None, str | None]:
        parts = expr.split(".", 1)
        varpath = parts[1] if len(parts) > 1 else parts[0]
        tokens = varpath.split("_")
        for n in range(1, min(4, len(tokens) + 1)):
            suffix = "_".join(tokens[-n:])
            if suffix in KEY_SUFFIXES:
                return suffix, KEY_SUFFIXES[suffix]
        last = tokens[-1] if tokens else ""
        if last in KEY_SUFFIXES:
            return last, KEY_SUFFIXES[last]
        return None, None

    def _get_signal(self, expr: str) -> tuple[np.ndarray | None, np.ndarray | None]:
        post = self._tb.post
        attempts = [
            {"expressions": [expr], "domain": "Time", "setup_sweep_name": self._setup_name},
            {"expressions": [expr], "domain": "Time"},
        ]
        for kwargs in attempts:
            try:
                sol_data = post.get_solution_data(**kwargs)
                if sol_data is None:
                    continue
                t = np.asarray(sol_data.primary_sweep_values, dtype=float)
                y = np.asarray(sol_data.data_real(expr), dtype=float)
                if len(t) > 0 and len(y) > 0:
                    return t, y
            except Exception:
                continue
        return None, None
