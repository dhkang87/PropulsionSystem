"""
mo_param_patcher.py
Patch Modelica .mo file parameters via regex-based text substitution.

Targets (CmpCharTable00.mo / TrbCharTable00.mo):
    - NmechDes_paramInput
    - PRdes_paramInput
    - effDes_paramInput
    - m_flow_1_des_paramInput
    - p1_des_paramInput
    - T1_des_paramInput
    - NcTblDes_paramInput
    - RlineTblDes_paramInput
    - pathName_tableFileInSimExeDir
    - pathName_tableFileInLibPackage

Usage:
    from mo_param_patcher import patch_mo_file, preview_patch
"""

import re
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class PatchResult:
    """Immutable result of a .mo file patch operation."""
    original: str
    patched: str
    changes: list  # list of (param_name, old_value, new_value)


# Pattern matches: `parameter <Type> <name> = <value> "<annotation>"`
# Handles numeric values, string literals, and enum values.
_PARAM_PATTERN = re.compile(
    r"(parameter\s+\S+\s+{name}\s*(?:\([^)]*\))?\s*=\s*)([^\";\n]+|\"[^\"]*\")"
)


def _build_pattern(param_name: str) -> re.Pattern:
    """Build a regex pattern for a specific parameter name."""
    return re.compile(
        rf"((?:inner\s+)?parameter\s+\S+\s+{re.escape(param_name)}\s*"
        rf"(?:\([^)]*\))?\s*=\s*)"
        rf"([^\";\n]+|\"[^\"]*\")"
    )


def _format_value(value) -> str:
    """Format a value for Modelica source: strings get quotes, numbers stay raw."""
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, float):
        # Use enough precision but avoid trailing zeros
        if value == int(value) and abs(value) < 1e12:
            return f"{value:.1f}"
        return f"{value:.9g}"
    elif isinstance(value, int):
        return str(value)
    else:
        return str(value)


def preview_patch(mo_path: str | Path, params: dict) -> PatchResult:
    """
    Preview parameter patches without writing to disk.

    Parameters
    ----------
    mo_path : str or Path
        Path to the .mo file.
    params : dict
        Keys are parameter names, values are the new values.
        Example: {"PRdes_paramInput": 10.0, "effDes_paramInput": 0.82}

    Returns
    -------
    PatchResult
        Contains original text, patched text, and list of changes made.
    """
    mo_path = Path(mo_path)
    original = mo_path.read_text(encoding="utf-8")
    patched = original
    changes = []

    for param_name, new_value in params.items():
        pattern = _build_pattern(param_name)
        match = pattern.search(patched)
        if match is None:
            continue

        old_value_str = match.group(2).strip()
        new_value_str = _format_value(new_value)

        if old_value_str != new_value_str:
            patched = pattern.sub(
                lambda m: m.group(1) + new_value_str,
                patched,
                count=1,
            )
            changes.append((param_name, old_value_str, new_value_str))

    return PatchResult(original=original, patched=patched, changes=changes)


def patch_mo_file(mo_path: str | Path, params: dict) -> PatchResult:
    """
    Apply parameter patches to a .mo file and write to disk.

    Parameters
    ----------
    mo_path : str or Path
        Path to the .mo file.
    params : dict
        Keys are parameter names, values are the new values.

    Returns
    -------
    PatchResult
        The result with list of applied changes.
    """
    result = preview_patch(mo_path, params)
    if result.changes:
        Path(mo_path).write_text(result.patched, encoding="utf-8")
    return result


def diff_summary(result: PatchResult) -> str:
    """
    Generate a human-readable summary of parameter changes.

    Parameters
    ----------
    result : PatchResult
        Output of preview_patch() or patch_mo_file().

    Returns
    -------
    str
        Multi-line summary string.
    """
    if not result.changes:
        return "No changes detected."

    lines = [f"{'Parameter':<35} {'Old':>20} → {'New':>20}"]
    lines.append("-" * 80)
    for param, old, new in result.changes:
        lines.append(f"{param:<35} {old:>20} → {new:>20}")
    return "\n".join(lines)
