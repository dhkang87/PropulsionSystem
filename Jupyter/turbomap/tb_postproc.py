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
        self._suffix_to_expr: dict[str, str] = {}  # suffix → current full expr
        self._exp_prefix: str = ""
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

        # Detect experiment prefix (e.g. "ExpTurboProp_TPE331_ex1a1")
        self._exp_prefix = self._detect_prefix(self._all_exprs)
        if self._exp_prefix:
            print(f"Experiment prefix: '{self._exp_prefix}'")

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

        # Build suffix → expr lookup for fallback resolution
        self._suffix_to_expr: dict[str, str] = {}
        for expr, (suffix, _) in self._selected.items():
            # Keep first match per suffix (avoid overwrites for duplicates)
            if suffix not in self._suffix_to_expr:
                self._suffix_to_expr[suffix] = expr

        print(f"Selected key signals: {len(self._selected)}")
        return list(self._selected.keys())

    @staticmethod
    def _detect_prefix(exprs: list[str]) -> str:
        """Extract common experiment prefix (text before first '.')."""
        prefixes: dict[str, int] = {}
        for e in exprs:
            dot = e.find(".")
            if dot > 0:
                pfx = e[:dot]
                prefixes[pfx] = prefixes.get(pfx, 0) + 1
        if not prefixes:
            return ""
        # Return the most common prefix
        return max(prefixes, key=prefixes.get)

    # ── Data collection ─────────────────────────────────────────────────

    def collect_signals(self, expressions: list[str] | None = None) -> pd.DataFrame:
        """Collect time-domain data for selected signals into a DataFrame."""
        exprs = expressions or list(self._selected.keys())
        if not exprs:
            raise ValueError("No signals to collect. Run discover_signals() first.")

        # ── Pre-check: test first 3 signals to see if data is actually available ──
        n_probe = min(3, len(exprs))
        probe_ok = 0
        for i in range(n_probe):
            t, _ = self._get_signal(exprs[i], verbose=True)
            if t is not None:
                probe_ok += 1

        if probe_ok == 0:
            # ── Stale detection: expression names may have changed ──
            print(f"⚠ Pre-check failed: first {n_probe} signals returned no data.")
            print(f"  → Re-discovering signals (model/experiment name may have changed)...")
            old_prefix = getattr(self, "_exp_prefix", "")
            self.discover_signals()
            new_prefix = getattr(self, "_exp_prefix", "")
            if new_prefix != old_prefix:
                print(f"  ✓ Prefix changed: '{old_prefix}' → '{new_prefix}'")
            exprs = list(self._selected.keys())
            if not exprs:
                print("  ✗ Still no signals after re-discovery.")
                self.mdf = pd.DataFrame()
                return self.mdf
            # Re-probe after re-discovery
            probe_ok = 0
            for i in range(min(3, len(exprs))):
                t, _ = self._get_signal(exprs[i], verbose=True)
                if t is not None:
                    probe_ok += 1
            if probe_ok == 0:
                print(f"  ✗ Still no data after re-discovery.")
                print(f"  → Run pp._tb.analyze() or re-simulate in Twin Builder.")
                self.mdf = pd.DataFrame()
                return self.mdf

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

    # ── Operating trajectory on map plane ──────────────────────────────

    def plot_operating_trajectory(
        self,
        T_ref: float = 288.15,
        p_ref: float = 101325.0,
        title: str | None = None,
        cmp_map: dict | None = None,
        trb_map: dict | None = None,
        NmechDes: float = 41730.0,
        cmp_design: dict | None = None,
        trb_design: dict | None = None,
    ):
        """
        Plot compressor and turbine operating trajectories on map-style planes.

        If cmp_map / trb_map are provided, draws background map contours
        (surge/choke lines, Nc iso-lines, efficiency) with trajectory overlay.
        Otherwise draws trajectory only.

        Parameters
        ----------
        T_ref, p_ref : float
            ISA reference conditions for correcting quantities.
        title : str or None
            Overall figure title.
        cmp_map : dict or None
            Scaled compressor map dict (from scale_compressor_map) with keys:
            'wc_scaled_corr', 'pr_scaled', 'eta_scaled', 'nc', 'wc_target_corr'.
            If provided, draws compressor map background.
        trb_map : dict or None
            Scaled turbine map dict (e.g. {"Trb": {...}}) compatible with
            plot_turbine_maps_2x2. If provided, draws turbine map background.
        NmechDes : float
            Design mechanical speed [rpm] for map contour labels.
        cmp_design : dict or None
            Compressor design conditions for Wc correction, e.g.
            {"T1_des": 288.15, "p1_des": 101325, "PRdes": 10.0}.
            If actual→corrected correction is needed, these are used.
        trb_design : dict or None
            Turbine design conditions for Wc correction, e.g.
            {"T1_des": 1100, "p1_des": 400000}.
            Used for static Wc correction fallback.
        """
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
        from matplotlib.colors import Normalize

        if self.mdf is None or self.mdf.empty:
            raise ValueError("No data. Run collect_signals() first.")

        mdf = self.mdf
        t = mdf["time"].to_numpy(dtype=float)
        fc = self.find_col
        sm = self.signal_map
        stations = sm.stations

        # ── Strategy 1: Direct map outputs (Modelica) ──
        col_Wc_cmp = fc(sm.Wc_cmp)
        col_PR_cmp = fc(sm.PR_cmp)
        col_Nc_cmp = fc(sm.Nc_cmp)
        col_eff_cmp = fc(sm.eff_cmp)

        col_PR_trb = fc(sm.PR_trb)
        col_eff_trb = fc(sm.eff_trb)
        col_Wc_trb = fc(["Trb_Wc_1", "Trb_Wc", "GGT_Wc_1", "GGT_Wc", "FPT_Wc_1"])

        has_cmp_direct = bool(col_Wc_cmp and col_PR_cmp)
        has_trb_direct = bool(col_Wc_trb and col_PR_trb)

        # ── Strategy 2: Station-derived (VHDL-AMS / fallback) ──
        p_in_col = fc(stations.get("1 (Inlet)", {}).get("p_patterns", []))
        p_cmp_out_col = fc(stations.get("2 (Cmp exit)", {}).get("p_patterns", []))
        T_in_col = fc(stations.get("1 (Inlet)", {}).get("T_patterns", []))
        p_trb_in_col = fc(stations.get("3 (TIT)", {}).get("p_patterns", []))
        p_trb_out_col = fc(stations.get("4 (Trb exit)", {}).get("p_patterns", []))
        T_trb_in_col = fc(stations.get("3 (TIT)", {}).get("T_patterns", []))
        col_omega = fc(sm.omega) or fc(sm.Nmech)

        has_cmp_derived = bool(p_in_col and p_cmp_out_col and T_in_col and col_omega)
        has_trb_derived = bool(p_trb_in_col and p_trb_out_col and T_trb_in_col)

        has_cmp = has_cmp_direct or has_cmp_derived
        has_trb = has_trb_direct or has_trb_derived

        # When a specific map is requested, suppress the other component's fallback plot
        if cmp_map is not None and trb_map is None:
            has_trb = False
        if trb_map is not None and cmp_map is None:
            has_cmp = False

        if not has_cmp and not has_trb:
            print("Insufficient signals for operating trajectory.")
            print(f"  [Direct] Wc_cmp={col_Wc_cmp}, PR_cmp={col_PR_cmp}, Wc_trb={col_Wc_trb}, PR_trb={col_PR_trb}")
            print(f"  [Derived] p_in={p_in_col}, p_cmp_out={p_cmp_out_col}, T_in={T_in_col}, omega={col_omega}")
            print(f"  [Derived] p_trb_in={p_trb_in_col}, p_trb_out={p_trb_out_col}, T_trb_in={T_trb_in_col}")
            return None

        fig_title = title or f"{self.design} — Operating Trajectory"
        norm = Normalize(vmin=t[0], vmax=t[-1])

        # ── If trb_map provided with background, use plot_turbine_maps_2x2 layout ──
        # Otherwise create simple subplot layout
        use_trb_bg = has_trb and trb_map is not None

        if use_trb_bg:
            # Import plot functions
            try:
                from turbomap_plot_utils import plot_turbine_maps_2x2
            except ImportError:
                use_trb_bg = False

        # Determine which components get their own map figure
        cmp_uses_own_fig = cmp_map is not None and has_cmp_direct
        trb_uses_own_fig = use_trb_bg and has_trb_direct

        # Base figure only for components WITHOUT a dedicated map figure
        n_base_cmp = int(has_cmp and not cmp_uses_own_fig)
        n_base_trb = int(has_trb and not trb_uses_own_fig)
        ncols = n_base_cmp + n_base_trb

        if ncols > 0:
            fig, axes = plt.subplots(1, ncols, figsize=(7 * ncols, 6))
            if ncols == 1:
                axes = [axes]
            fig.suptitle(fig_title, fontsize=13)
        else:
            fig = None
            axes = []

        # ══════ COMPRESSOR ══════
        if has_cmp:
            # Get trajectory data
            if has_cmp_direct:
                Wc_sim = mdf[col_Wc_cmp].to_numpy(dtype=float)
                PR_sim = mdf[col_PR_cmp].to_numpy(dtype=float)
                # ── Wc correction: actual → corrected flow if needed ──
                if cmp_map is not None:
                    wc_target = cmp_map.get("wc_target_corr", 1.0)
                    wc_ratio = Wc_sim.mean() / wc_target if wc_target > 0 else 1.0
                    if wc_ratio > 5 and cmp_design is not None:
                        from turbomap_data_utils import T_REF, P_REF
                        corr = (np.sqrt(cmp_design["T1_des"] / T_REF)
                                / (cmp_design["p1_des"] / P_REF))
                        Wc_sim = Wc_sim * corr
                        print(f"  ⚠ Cmp Wc actual→corrected: factor={corr:.4f}")
            else:
                p_in = mdf[p_in_col].to_numpy(dtype=float)
                p_out = mdf[p_cmp_out_col].to_numpy(dtype=float)
                T_in = mdf[T_in_col].to_numpy(dtype=float)
                omega = mdf[col_omega].to_numpy(dtype=float)
                theta = np.clip(T_in / T_ref, 0.5, 3.0)
                Wc_sim = (omega * 60 / (2 * np.pi)) / np.sqrt(theta)  # Nc as x
                PR_sim = np.where(p_in > 0, p_out / p_in, 1.0)

            if cmp_map is not None and has_cmp_direct:
                # ── Background map + trajectory overlay ──
                try:
                    from turbomap_plot_utils import plot_compressor_map
                    PRdes = (cmp_design or {}).get("PRdes", cmp_map.get("pr_scaled", [[1]])[0][-1])
                    design_pt = {"Wc": cmp_map.get("wc_target_corr", 8.0), "PR": PRdes}
                    # Use PRdes from target if available
                    if "pr_scaled" in cmp_map:
                        fig_c, ax_c = plot_compressor_map(
                            cmp_map["wc_scaled_corr"],
                            cmp_map["pr_scaled"],
                            cmp_map["eta_scaled"],
                            cmp_map["nc"],
                            NmechDes=NmechDes,
                            design_point=design_pt,
                            title=f"{fig_title} — Compressor",
                        )
                    else:
                        fig_c, ax_c = plt.subplots(1, 1, figsize=(8, 6))
                        ax_c.set_title(f"{fig_title} — Compressor")
                except (ImportError, Exception):
                    fig_c, ax_c = plt.subplots(1, 1, figsize=(8, 6))
                    ax_c.set_title(f"{fig_title} — Compressor")
                    ax_c.grid(True, alpha=0.3)

                # Scatter trajectory
                sc = ax_c.scatter(Wc_sim, PR_sim, c=t, cmap="plasma", s=8,
                                  zorder=5, alpha=0.7, edgecolors="none")
                plt.colorbar(sc, ax=ax_c, shrink=0.8, pad=0.02, label="Time [s]")
                ax_c.plot(Wc_sim[0], PR_sim[0], "g^", ms=12, zorder=6,
                          label=f"t={t[0]:.1f}s (start)")
                ax_c.plot(Wc_sim[-1], PR_sim[-1], "rs", ms=12, zorder=6,
                          label=f"t={t[-1]:.1f}s (end)")
                ax_c.legend(loc="lower right", fontsize=9)

                # Auto-scale to include both map and trajectory
                all_wc = np.concatenate([cmp_map["wc_scaled_corr"].ravel(), Wc_sim])
                all_pr = np.concatenate([cmp_map["pr_scaled"].ravel(), PR_sim])
                ax_c.set_xlim(all_wc.min() * 0.9, all_wc.max() * 1.1)
                ax_c.set_ylim(max(0.5, all_pr.min() * 0.9), all_pr.max() * 1.1)

                plt.show()
                print(f"✓ Cmp trajectory: Wc={Wc_sim[0]:.2f}→{Wc_sim[-1]:.2f}, "
                      f"PR={PR_sim[0]:.2f}→{PR_sim[-1]:.2f}")
            else:
                # ── Trajectory only (no map background) ──
                ax = axes[0]
                if has_cmp_direct:
                    x_label = "Corrected Flow Wc [kg/s]"
                    y_label = "Pressure Ratio PR [-]"
                    sub_title = "Compressor: Wc vs PR"
                else:
                    x_label = "Corrected Speed Nc [rpm]"
                    y_label = "Pressure Ratio PR [-]"
                    sub_title = "Compressor: Nc vs PR (derived)"

                self._draw_colored_trajectory(
                    ax, Wc_sim, PR_sim, t, norm, x_label, y_label, sub_title)

                if col_eff_cmp and col_eff_cmp in mdf.columns:
                    eta = mdf[col_eff_cmp].to_numpy(dtype=float)
                    n_ss = max(1, int(len(eta) * 0.1))
                    eta_ss = np.mean(eta[-n_ss:])
                    ax.annotate(
                        f"η_ss={eta_ss:.3f}",
                        xy=(np.mean(Wc_sim[-n_ss:]), np.mean(PR_sim[-n_ss:])),
                        xytext=(10, 10), textcoords="offset points",
                        fontsize=9, color="purple",
                        arrowprops=dict(arrowstyle="->", color="purple"),
                    )

        # ══════ TURBINE ══════
        if has_trb:
            # Get trajectory data
            if has_trb_direct:
                Wc_trb_raw = mdf[col_Wc_trb].to_numpy(dtype=float)
                PR_trb_sim = mdf[col_PR_trb].to_numpy(dtype=float)
                Eta_trb_sim = (mdf[col_eff_trb].to_numpy(dtype=float)
                               if col_eff_trb and col_eff_trb in mdf.columns else None)

                # ── Wc correction: actual → corrected if needed ──
                trb_key = next(iter(trb_map), None) if trb_map else None
                wc_map_des = (trb_map[trb_key].get("wc_target_corr", 1.0)
                              if trb_key else 1.0)
                wc_ratio = (Wc_trb_raw.mean() / wc_map_des
                            if wc_map_des > 0 else 1.0)
                if wc_ratio > 3:
                    from turbomap_data_utils import T_REF, P_REF
                    # Try dynamic correction using turbine T1/p1 signals
                    col_Trb_T1 = fc(["Trb_port_1_T", "Trb_fluid_1_T",
                                     "Comb_port_2_T", "Trb_T_1"])
                    col_Trb_p1 = fc(["Trb_port_1_p", "Trb_fluid_1_p",
                                     "Comb_port_2_p", "Trb_p_1"])
                    if col_Trb_T1 and col_Trb_p1:
                        T1_sim = mdf[col_Trb_T1].to_numpy(dtype=float)
                        p1_sim = mdf[col_Trb_p1].to_numpy(dtype=float)
                        corr_dyn = np.sqrt(T1_sim / T_REF) / (p1_sim / P_REF)
                        Wc_trb_sim = Wc_trb_raw * corr_dyn
                        print(f"  ✓ Trb Wc dynamic correction (T1, p1)")
                    elif trb_design is not None:
                        corr_st = (np.sqrt(trb_design["T1_des"] / T_REF)
                                   / (trb_design["p1_des"] / P_REF))
                        Wc_trb_sim = Wc_trb_raw * corr_st
                        print(f"  ⚠ Trb Wc static correction: factor={corr_st:.4f}")
                    else:
                        Wc_trb_sim = Wc_trb_raw
                else:
                    Wc_trb_sim = Wc_trb_raw
            else:
                p_trb_in = mdf[p_trb_in_col].to_numpy(dtype=float)
                p_trb_out = mdf[p_trb_out_col].to_numpy(dtype=float)
                T_trb_in = mdf[T_trb_in_col].to_numpy(dtype=float)
                PR_trb_sim = np.where(p_trb_out > 0, p_trb_in / p_trb_out, 1.0)
                theta_trb = np.clip(T_trb_in / T_ref, 0.5, 8.0)
                if col_omega and col_omega in mdf.columns:
                    omega = mdf[col_omega].to_numpy(dtype=float)
                    Wc_trb_sim = (omega * 60 / (2 * np.pi)) / np.sqrt(theta_trb)
                else:
                    Wc_trb_sim = np.sqrt(theta_trb)
                Eta_trb_sim = None

            if use_trb_bg and has_trb_direct:
                # ── Background turbine map + trajectory overlay ──
                fig_t, axes_t = plot_turbine_maps_2x2(
                    trb_map,
                    suptitle=f"{fig_title} — Turbine",
                    NmechDes_dict={k: NmechDes for k in trb_map},
                )
                # Overlay on first turbine's axes (col=0)
                ax_wc = axes_t[0, 0]
                ax_eta = axes_t[1, 0]

                sc_wc = ax_wc.scatter(PR_trb_sim, Wc_trb_sim, c=t, cmap="plasma",
                                      s=10, zorder=6, alpha=0.8, edgecolors="none")
                plt.colorbar(sc_wc, ax=ax_wc, shrink=0.7, pad=0.02, label="Time [s]")
                ax_wc.plot(PR_trb_sim[0], Wc_trb_sim[0], "g^", ms=11, zorder=7,
                           label=f"t={t[0]:.1f}s (start)")
                ax_wc.plot(PR_trb_sim[-1], Wc_trb_sim[-1], "rs", ms=11, zorder=7,
                           label=f"t={t[-1]:.1f}s (end)")
                ax_wc.legend(loc="best", fontsize=8)

                if Eta_trb_sim is not None:
                    sc_eta = ax_eta.scatter(PR_trb_sim, Eta_trb_sim, c=t, cmap="plasma",
                                           s=10, zorder=6, alpha=0.8, edgecolors="none")
                    plt.colorbar(sc_eta, ax=ax_eta, shrink=0.7, pad=0.02, label="Time [s]")
                    ax_eta.plot(PR_trb_sim[0], Eta_trb_sim[0], "g^", ms=11, zorder=7)
                    ax_eta.plot(PR_trb_sim[-1], Eta_trb_sim[-1], "rs", ms=11, zorder=7)

                plt.show()
                print(f"✓ Trb trajectory: PR={PR_trb_sim[0]:.2f}→{PR_trb_sim[-1]:.2f}, "
                      f"Wc={Wc_trb_sim[0]:.3f}→{Wc_trb_sim[-1]:.3f}")
                if Eta_trb_sim is not None:
                    print(f"  Eta: {Eta_trb_sim[0]:.4f}→{Eta_trb_sim[-1]:.4f}")
            elif not use_trb_bg:
                # ── Trajectory only ──
                ax_idx = n_base_cmp  # turbine subplot follows compressor in base fig
                ax = axes[ax_idx] if ax_idx < len(axes) else axes[-1]

                if has_trb_direct:
                    x_data, y_data = PR_trb_sim, Wc_trb_sim
                    x_label = "Expansion Ratio PR [-]"
                    y_label = "Corrected Flow Wc [kg/s]"
                    sub_title = "Turbine: PR vs Wc"
                else:
                    x_data, y_data = Wc_trb_sim, PR_trb_sim
                    x_label = "Corrected Speed Nc_trb [rpm]"
                    y_label = "Expansion Ratio ER [-]"
                    sub_title = "Turbine: Nc vs ER (derived)"

                self._draw_colored_trajectory(
                    ax, x_data, y_data, t, norm, x_label, y_label, sub_title)

                if col_eff_trb and col_eff_trb in mdf.columns:
                    eta = mdf[col_eff_trb].to_numpy(dtype=float)
                    n_ss = max(1, int(len(eta) * 0.1))
                    eta_ss = np.mean(eta[-n_ss:])
                    ax.annotate(
                        f"η_ss={eta_ss:.3f}",
                        xy=(np.mean(x_data[-n_ss:]), np.mean(y_data[-n_ss:])),
                        xytext=(10, 10), textcoords="offset points",
                        fontsize=9, color="purple",
                        arrowprops=dict(arrowstyle="->", color="purple"),
                    )

        # Finalize simple layout (no map background case)
        if ncols > 0:
            sm_cbar = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
            sm_cbar.set_array([])
            cbar = fig.colorbar(sm_cbar, ax=axes, shrink=0.8, pad=0.02)
            cbar.set_label("Time [s]")
            plt.show()

        return None

    @staticmethod
    def _draw_colored_trajectory(ax, x, y, t_arr, norm, xlabel, ylabel, subtitle):
        """Draw time-colored trajectory with start/end markers."""
        from matplotlib.collections import LineCollection
        points = np.column_stack([x, y]).reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc = LineCollection(segments, cmap="viridis", norm=norm, lw=2, alpha=0.8)
        lc.set_array(t_arr[:-1])
        ax.add_collection(lc)
        ax.autoscale()
        ax.plot(x[0], y[0], "go", ms=10, zorder=5, label="Start")
        ax.plot(x[-1], y[-1], "rs", ms=10, zorder=5, label="End")
        n_ss = max(1, int(len(x) * 0.1))
        x_ss, y_ss = np.mean(x[-n_ss:]), np.mean(y[-n_ss:])
        ax.plot(x_ss, y_ss, "k*", ms=14, zorder=6, label=f"SS ({x_ss:.2f}, {y_ss:.2f})")
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(subtitle)
        ax.legend(fontsize=8, loc="best")
        ax.grid(True, alpha=0.3)
        return lc

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

    def _get_signal(self, expr: str, verbose: bool = False) -> tuple[np.ndarray | None, np.ndarray | None]:
        post = self._tb.post
        attempts = [
            {"expressions": [expr], "domain": "Time", "setup_sweep_name": self._setup_name},
            {"expressions": [expr], "domain": "Time"},
        ]
        last_error: str | None = None
        for kwargs in attempts:
            try:
                sol_data = post.get_solution_data(**kwargs)
                if sol_data is None:
                    last_error = f"get_solution_data returned None (kwargs={kwargs})"
                    continue
                # pyaedt 1.0: use get_expression_data() which returns (x, y) tuple
                # fallback to legacy data_real() for older versions
                t, y = self._extract_xy(sol_data, expr)
                if t is not None and len(t) > 0 and len(y) > 0:
                    return t, y
                last_error = f"empty arrays: len(t)={0 if t is None else len(t)}, len(y)={0 if y is None else len(y)}"
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                continue

        # ── Suffix fallback: expression name may have changed (new prefix) ──
        suffix, _ = self._match_key(expr)
        if suffix and hasattr(self, "_suffix_to_expr"):
            resolved = self._suffix_to_expr.get(suffix)
            if resolved and resolved != expr:
                if verbose:
                    print(f"  [fallback] '{expr}' → trying '{resolved}'")
                for kwargs in [
                    {"expressions": [resolved], "domain": "Time", "setup_sweep_name": self._setup_name},
                    {"expressions": [resolved], "domain": "Time"},
                ]:
                    try:
                        sol_data = post.get_solution_data(**kwargs)
                        if sol_data is None:
                            continue
                        t, y = self._extract_xy(sol_data, resolved)
                        if t is not None and len(t) > 0 and len(y) > 0:
                            return t, y
                    except Exception:
                        continue
                last_error = f"suffix fallback also failed for '{resolved}'"

        if verbose and last_error:
            print(f"  [_get_signal] '{expr}' FAILED: {last_error}")
        return None, None

    @staticmethod
    def _extract_xy(sol_data, expr: str) -> tuple[np.ndarray | None, np.ndarray | None]:
        """Extract (time, value) arrays from SolutionData using correct API version."""
        # pyaedt >= 1.0 (ansys-aedt-core): get_expression_data returns (x, y)
        if hasattr(sol_data, "get_expression_data"):
            # Check if expression key matches what SolutionData knows
            available = sol_data.expressions if hasattr(sol_data, "expressions") else []
            target = expr
            if expr not in available and available:
                # Try matching by suffix (expression may be stored without experiment prefix)
                for avail_expr in available:
                    if avail_expr.endswith(expr) or expr.endswith(avail_expr):
                        target = avail_expr
                        break
                    # Also try matching after last dot
                    expr_tail = expr.rsplit(".", 1)[-1]
                    avail_tail = avail_expr.rsplit(".", 1)[-1]
                    if expr_tail == avail_tail:
                        target = avail_expr
                        break
            x, y = sol_data.get_expression_data(expression=target, formula="real")
            if len(x) > 0 and len(y) > 0:
                return np.asarray(x, dtype=float), np.asarray(y, dtype=float)
        # Legacy pyaedt (< 1.0): data_real() method
        if hasattr(sol_data, "data_real") and callable(sol_data.data_real):
            t = np.asarray(sol_data.primary_sweep_values, dtype=float)
            y = np.asarray(sol_data.data_real(expr), dtype=float)
            if len(t) > 0 and len(y) > 0:
                return t, y
        return None, None
