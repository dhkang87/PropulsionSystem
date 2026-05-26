"""
tb_runner.py
Twin Builder simulation runner with pyAEDT auto mode and CSV/MAT manual fallback.

Usage:
    from tb_runner import run_twin_builder, load_csv_results, load_mat_results
"""

import pandas as pd
import numpy as np
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class SimResult:
    """Immutable simulation result container."""
    source: str          # "pyaedt" | "csv" | "mat"
    data: pd.DataFrame   # columns: time, Wc, PR, Nmech, eta, etc.
    metadata: dict       # project path, variable mapping, etc.


# ═══════════════════════════════════════════════════════════════════════════
# Mode B: Manual CSV/MAT import (always available)
# ═══════════════════════════════════════════════════════════════════════════

def load_csv_results(
    csv_path: str | Path,
    column_map: dict | None = None,
    time_col: str = "Time",
) -> SimResult:
    """
    Load simulation results from a CSV file.

    Parameters
    ----------
    csv_path : str or Path
        Path to the CSV file exported from Twin Builder.
    column_map : dict or None
        Rename columns to standard names. Example:
        {"col_A": "Wc", "col_B": "PR", "col_C": "Nmech"}
        If None, columns are used as-is.
    time_col : str
        Name of the time column in the CSV.

    Returns
    -------
    SimResult
    """
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)

    if column_map:
        df = df.rename(columns=column_map)

    if time_col in df.columns and time_col != "time":
        df = df.rename(columns={time_col: "time"})

    return SimResult(
        source="csv",
        data=df,
        metadata={"path": str(csv_path), "column_map": column_map},
    )


def load_mat_results(
    mat_path: str | Path,
    variable_names: list[str] | None = None,
) -> SimResult:
    """
    Load simulation results from a .mat file (Modelica/Dymola format).

    Parameters
    ----------
    mat_path : str or Path
        Path to the .mat result file.
    variable_names : list of str or None
        Specific variable names to extract. If None, loads all.

    Returns
    -------
    SimResult
    """
    from scipy.io import loadmat

    mat_path = Path(mat_path)
    mat_data = loadmat(str(mat_path), squeeze_me=True)

    # Common Modelica .mat structure: 'data_2' matrix, 'name' string array
    if "data_2" in mat_data and "name" in mat_data:
        names = [n.strip() for n in mat_data["name"]]
        data_matrix = mat_data["data_2"]
        df = pd.DataFrame(data_matrix.T, columns=names)
    else:
        # Fallback: use all numeric arrays
        df_dict = {}
        for key, val in mat_data.items():
            if isinstance(val, np.ndarray) and val.ndim <= 2:
                if val.ndim == 1:
                    df_dict[key] = val
        df = pd.DataFrame(df_dict)

    if variable_names:
        available = [v for v in variable_names if v in df.columns]
        if "time" in df.columns and "time" not in available:
            available.insert(0, "time")
        df = df[available]

    return SimResult(
        source="mat",
        data=df,
        metadata={"path": str(mat_path), "variables": variable_names},
    )


# ═══════════════════════════════════════════════════════════════════════════
# Mode A: pyAEDT automation (requires AEDT installation)
# ═══════════════════════════════════════════════════════════════════════════

def run_twin_builder(
    project_path: str | Path,
    design_name: str | None = None,
    setup_name: str | None = None,
    variables: list[str] | None = None,
    *,
    close_on_exit: bool = False,
    aedt_version: str | None = None,
) -> SimResult:
    """
    Run a Twin Builder simulation via pyAEDT and extract results.

    Parameters
    ----------
    project_path : str or Path
        Path to the .aedt project file.
    design_name : str or None
        Twin Builder design name. If None, uses the active design.
    setup_name : str or None
        Analysis setup name. If None, uses the first available.
    variables : list of str or None
        Output variable names to extract. If None, extracts all.
    close_on_exit : bool
        Whether to close AEDT after extraction.
    aedt_version : str or None
        AEDT version string (e.g. "2026.1"). Auto-detected if None.

    Returns
    -------
    SimResult

    Raises
    ------
    ImportError
        If pyaedt is not installed.
    RuntimeError
        If simulation fails.
    """
    try:
        from ansys.aedt.core import TwinBuilder
    except ImportError:
        try:
            from pyaedt import TwinBuilder
        except ImportError:
            raise ImportError(
                "pyaedt is not installed. Use load_csv_results() or "
                "load_mat_results() as a manual fallback."
            )

    project_path = str(Path(project_path).resolve())
    kwargs = {"project": project_path, "non_graphical": False}
    if aedt_version:
        kwargs["version"] = aedt_version
    if design_name:
        kwargs["design"] = design_name

    tb = TwinBuilder(**kwargs)

    # Run simulation
    if setup_name:
        setup = tb.setups[setup_name] if setup_name in tb.setups else tb.setups[0]
    else:
        setup = tb.setups[0] if tb.setups else None

    if setup is None:
        raise RuntimeError("No analysis setup found in the project.")

    tb.analyze(setup_name=setup.name)

    # Extract results
    solutions = tb.post.get_solution_data(
        expressions=variables or [],
        setup_sweep_name=setup.name,
    )

    if solutions is None:
        raise RuntimeError("Failed to extract solution data.")

    # Build DataFrame
    df_dict = {"time": np.array(solutions.primary_sweep_values, dtype=float)}
    for expr in solutions.expressions:
        df_dict[expr] = np.array(solutions.data_real(expr), dtype=float)
    df = pd.DataFrame(df_dict)

    if close_on_exit:
        tb.close_project()
        tb.release_desktop()

    return SimResult(
        source="pyaedt",
        data=df,
        metadata={
            "project": project_path,
            "design": design_name,
            "setup": setup.name if setup else None,
            "variables": variables,
        },
    )
