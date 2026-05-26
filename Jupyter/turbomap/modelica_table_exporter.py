"""
modelica_table_exporter.py
Export scaled turbomap data to Modelica CombiTable2D text format.

Format (PropulsionSystem convention):
    #1
    double Wc_NcRline(16,12)   # Wc=f(Nc, Rline)
    0    rline[0]    rline[1]    ...
    nc[0]    data[0,0]    data[0,1]    ...
    nc[1]    data[1,0]    data[1,1]    ...
    ...

Usage:
    from modelica_table_exporter import (
        export_compressor_tables,
        export_turbine_tables,
        export_turbine_tables_from_rline,
        compute_mo_params,
    )
"""

import numpy as np
from pathlib import Path


def _format_table_block(
    name: str,
    row_axis: np.ndarray,
    col_axis: np.ndarray,
    data: np.ndarray,
    comment: str = "",
) -> str:
    """
    Format a single table block in Modelica CombiTable2D text format.

    Parameters
    ----------
    name : str
        Table name (e.g. "Wc_NcRline").
    row_axis : 1-D array
        Row labels (Nc values for compressor, Nc for turbine).
    col_axis : 1-D array
        Column labels (Rline for compressor, PR for turbine).
    data : 2-D array, shape (len(row_axis), len(col_axis))
        Table data values.
    comment : str
        Optional comment after the dimension descriptor.

    Returns
    -------
    str
        Formatted text block (without the `#1` header).
    """
    n_rows = len(row_axis) + 1  # +1 for header row
    n_cols = len(col_axis) + 1  # +1 for label column
    comment_str = f"   # {comment}" if comment else ""
    lines = [f"double {name}({n_rows},{n_cols}){comment_str}"]

    # Header row: 0 followed by column labels
    header_vals = [0.0] + col_axis.tolist()
    lines.append("\t".join(f"{v:.9g}" for v in header_vals))

    # Data rows: row label followed by values
    for i, row_label in enumerate(row_axis):
        row_vals = [float(row_label)] + data[i, :].tolist()
        lines.append("\t".join(f"{v:.9g}" for v in row_vals))

    return "\n".join(lines)


def export_compressor_tables(
    nc: np.ndarray,
    rline: np.ndarray,
    wc: np.ndarray,
    pr: np.ndarray,
    eff: np.ndarray,
    output_path: str | Path,
    *,
    table_names: dict | None = None,
) -> Path:
    """
    Export scaled compressor map data to a single Modelica table text file.

    The file contains 3 tables:
        Wc_NcRline(n_nc+1, n_rline+1)
        PR_NcRline(n_nc+1, n_rline+1)
        eff_NcRline(n_nc+1, n_rline+1)

    Parameters
    ----------
    nc : 1-D array, shape (n_nc,)
        Normalized corrected speed values (row axis).
    rline : 1-D array, shape (n_rline,)
        R-line values (column axis).
    wc : 2-D array, shape (n_nc, n_rline)
        Scaled corrected mass flow.
    pr : 2-D array, shape (n_nc, n_rline)
        Scaled pressure ratio.
    eff : 2-D array, shape (n_nc, n_rline)
        Scaled isentropic efficiency.
    output_path : str or Path
        Destination file path (.txt).
    table_names : dict or None
        Override default table names. Keys: 'wc', 'pr', 'eff'.

    Returns
    -------
    Path
        The written output file path.
    """
    nc = np.asarray(nc, dtype=float)
    rline = np.asarray(rline, dtype=float)
    wc = np.asarray(wc, dtype=float)
    pr = np.asarray(pr, dtype=float)
    eff = np.asarray(eff, dtype=float)

    if table_names is None:
        table_names = {"wc": "Wc_NcRline", "pr": "PR_NcRline", "eff": "eff_NcRline"}

    blocks = [
        _format_table_block(table_names["wc"], nc, rline, wc, "Wc=f(Nc, Rline)"),
        "",
        _format_table_block(table_names["pr"], nc, rline, pr, "PR=f(Nc, Rline)"),
        "",
        _format_table_block(table_names["eff"], nc, rline, eff, "eff=f(Nc, Rline)"),
    ]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "#1\n" + "\n".join(blocks) + "\n"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def export_turbine_tables(
    nc: np.ndarray,
    pr_axis: np.ndarray,
    wc: np.ndarray,
    eff: np.ndarray,
    output_path: str | Path,
    *,
    table_names: dict | None = None,
) -> Path:
    """
    Export scaled turbine map data to a single Modelica table text file.

    The file contains 2 tables:
        Wc_NcPR(n_nc+1, n_pr+1)
        eff_NcPR(n_nc+1, n_pr+1)

    Parameters
    ----------
    nc : 1-D array, shape (n_nc,)
        Normalized corrected speed values (row axis).
    pr_axis : 1-D array, shape (n_pr,)
        Pressure ratio values (column axis).
    wc : 2-D array, shape (n_nc, n_pr)
        Scaled corrected mass flow.
    eff : 2-D array, shape (n_nc, n_pr)
        Scaled isentropic efficiency.
    output_path : str or Path
        Destination file path (.txt).
    table_names : dict or None
        Override default table names. Keys: 'wc', 'eff'.

    Returns
    -------
    Path
        The written output file path.
    """
    nc = np.asarray(nc, dtype=float)
    pr_axis = np.asarray(pr_axis, dtype=float)
    wc = np.asarray(wc, dtype=float)
    eff = np.asarray(eff, dtype=float)

    if table_names is None:
        table_names = {"wc": "Wc_NcPR", "eff": "eff_NcPR"}

    blocks = [
        _format_table_block(table_names["wc"], nc, pr_axis, wc, "Wc=f(Nc, PR)"),
        "",
        _format_table_block(table_names["eff"], nc, pr_axis, eff, "eff=f(Nc, PR)"),
    ]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "#1\n" + "\n".join(blocks) + "\n"
    output_path.write_text(content, encoding="utf-8")
    return output_path


def export_turbine_tables_from_rline(
    nc: np.ndarray,
    pr_scaled: np.ndarray,
    wc: np.ndarray,
    eff: np.ndarray,
    output_path: str | Path,
    *,
    n_pr_points: int = 20,
    table_names: dict | None = None,
) -> dict:
    """
    Export turbine table with proper (Nc, Rline) → (Nc, PR) coordinate transform.

    Unlike export_turbine_tables() which takes a pre-built PR axis,
    this function creates a COMMON PR axis covering ALL speed lines
    and interpolates each speed line onto it. This prevents the
    "first speed line PR range too narrow" bug.

    Parameters
    ----------
    nc : 1-D array, shape (n_nc,)
        Normalized corrected speed values.
    pr_scaled : 2-D array, shape (n_nc, n_rline)
        Scaled PR values at each (Nc, Rline) point.
        PR varies across both Nc and Rline.
    wc : 2-D array, shape (n_nc, n_rline)
        Scaled corrected mass flow at each (Nc, Rline) point.
    eff : 2-D array, shape (n_nc, n_rline)
        Scaled efficiency at each (Nc, Rline) point.
    output_path : str or Path
        Destination file path (.txt).
    n_pr_points : int
        Number of uniform PR grid points for the common axis (default 20).
    table_names : dict or None
        Override default table names. Keys: 'wc', 'eff'.

    Returns
    -------
    dict with keys:
        'path': Path to written file
        'pr_axis': the common PR axis used (1-D, shape n_pr_points)
        'pr_des_approx': PR at design Nc (Nc≈1.0) midpoint — candidate for PRtblDes
    """
    nc = np.asarray(nc, dtype=float)
    pr_scaled = np.asarray(pr_scaled, dtype=float)
    wc = np.asarray(wc, dtype=float)
    eff = np.asarray(eff, dtype=float)

    # Common PR axis: covers full range across ALL speed lines
    pr_min = pr_scaled.min()
    pr_max = pr_scaled.max()
    pr_common = np.linspace(pr_min, pr_max, n_pr_points)

    # Interpolate each speed line onto the common PR axis
    wc_interp = np.empty((len(nc), n_pr_points))
    eff_interp = np.empty((len(nc), n_pr_points))

    for i in range(len(nc)):
        pr_line = pr_scaled[i, :]
        wc_line = wc[i, :]
        eff_line = eff[i, :]

        # Sort by PR (should already be monotonic, but ensure)
        sort_idx = np.argsort(pr_line)
        pr_sorted = pr_line[sort_idx]
        wc_sorted = wc_line[sort_idx]
        eff_sorted = eff_line[sort_idx]

        # Interpolate with boundary clamping (turbines choke → flat at high PR)
        wc_interp[i, :] = np.interp(pr_common, pr_sorted, wc_sorted)
        eff_interp[i, :] = np.interp(pr_common, pr_sorted, eff_sorted)

    # Estimate design PR: at the speed line closest to Nc=1.0, midpoint of PR range
    idx_des_nc = int(np.argmin(np.abs(nc - 1.0)))
    pr_line_des = pr_scaled[idx_des_nc, :]
    pr_des_approx = float(np.median(pr_line_des))

    if table_names is None:
        table_names = {"wc": "Wc_NcPR", "eff": "eff_NcPR"}

    blocks = [
        _format_table_block(table_names["wc"], nc, pr_common, wc_interp, "Wc=f(Nc, PR)"),
        "",
        _format_table_block(table_names["eff"], nc, pr_common, eff_interp, "eff=f(Nc, PR)"),
    ]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = "#1\n" + "\n".join(blocks) + "\n"
    output_path.write_text(content, encoding="utf-8")

    return {
        "path": output_path,
        "pr_axis": pr_common,
        "pr_des_approx": pr_des_approx,
    }


def compute_mo_params(parsed: dict, target: dict, table_path: str) -> dict:
    """
    Automatically compute all .mo parameters from parsed XML + target design point.

    No manual RlineTblDes / NcTblDes guessing needed — values come directly
    from the XML design-point anchor (parsed["nc_des"], parsed["rline_des"]).

    Parameters
    ----------
    parsed : dict
        Output of parse_compressor_xml() or parse_turbine_xml().
    target : dict
        Design target. Keys: m_flow_des, PRdes, effDes, T1_des, p1_des.
        Optional: NmechDes.
    table_path : str
        Relative path for the table file (e.g. "./tableData/xxx.txt").

    Returns
    -------
    dict
        Ready-to-use .mo parameters including auto-computed NcTblDes, RlineTblDes.
    """
    params = {
        "PRdes_paramInput": target["PRdes"],
        "effDes_paramInput": target["effDes"],
        "m_flow_1_des_paramInput": target["m_flow_des"],
        "p1_des_paramInput": target["p1_des"],
        "T1_des_paramInput": target["T1_des"],
        "NcTblDes_paramInput": float(parsed["nc_des"]),
        "pathName_tableFileInSimExeDir": table_path,
        "pathName_tableFileInLibPackage": table_path.replace(
            "./tableData/", "modelica://PropulsionSystem/tableData/"
        ),
    }

    if "NmechDes" in target:
        params["NmechDes_paramInput"] = target["NmechDes"]

    # Compressor: uses Rline as 2nd table axis → auto from XML
    if "rline_des" in parsed:
        params["RlineTblDes_paramInput"] = float(parsed["rline_des"])

    # Turbine: uses PR as 2nd table axis → auto from XML
    if "pr_des" in parsed and "rline_des" not in parsed:
        params["PRtblDes_paramInput"] = float(parsed["pr_des"])

    return params
