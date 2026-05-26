"""
turbomap_data_utils.py
XML compressor/turbine map parsing and design-point scaling utilities.

Usage:
    from turbomap_data_utils import (
        parse_compressor_xml, parse_turbine_xml,
        scale_compressor_map, scale_turbine_map,
    )
"""

import numpy as np
import xml.etree.ElementTree as ET
from scipy.interpolate import RegularGridInterpolator

T_REF = 288.15   # K
P_REF = 101325.0 # Pa


# ═══════════════════════════════════════════════════════════════════════════
# XML Parsing
# ═══════════════════════════════════════════════════════════════════════════

def _parse_matrix_text(text: str) -> np.ndarray:
    """Parse semicolon-separated matrix string → 2-D ndarray."""
    cleaned = text.strip().strip("[]")
    rows = [r.strip() for r in cleaned.split(";") if r.strip()]
    return np.array([[float(v) for v in row.replace(",", " ").split()] for row in rows], dtype=float)


def _find_matrix(root: ET.Element, tag_candidates: list) -> np.ndarray | None:
    """Find a matrix element by trying multiple tag names."""
    for tag in tag_candidates:
        node = root.find(tag)
        if node is not None and node.text and node.text.strip():
            return _parse_matrix_text(node.text)
    # Fallback: search iteratively
    keys = [k.lower() for k in tag_candidates]
    for node in root.iter():
        nm = (node.tag or "").lower()
        if any(k in nm for k in keys):
            if node.text and node.text.strip() and ";" in node.text:
                return _parse_matrix_text(node.text)
    return None


def parse_compressor_xml(xml_path: str) -> dict:
    """
    Parse a compressor XML map file (e.g. Turboprop_ggc.xml).

    Returns
    -------
    dict with keys:
        path, nc, rline, wc, pr, eta,
        nc_des, rline_des, wc_des, pr_des, eta_des
    """
    root = ET.parse(xml_path).getroot()

    cf_mat = _find_matrix(root, ["correctedFlow", "wc", "wcorr", "flow"])
    pr_mat = _find_matrix(root, ["pressureRatio", "pr"])
    ie_mat = _find_matrix(root, ["isentropicEfficiency", "efficiency", "eta"])

    if cf_mat is None or pr_mat is None or ie_mat is None:
        raise ValueError(f"Required matrix tags not found in {xml_path}")

    rline = cf_mat[0, 1:]
    nc = cf_mat[1:, 0]
    wc = cf_mat[1:, 1:]
    pr = pr_mat[1:, 1:]
    eta = ie_mat[1:, 1:]

    # Design point from XML
    nc_des_node = root.find("design/correctedSpeed")
    rl_des_node = root.find("design/rLine")
    if nc_des_node is not None and rl_des_node is not None:
        nc_des = float(nc_des_node.text)
        rline_des = float(rl_des_node.text)
    else:
        nc_des = float(nc[len(nc) // 2])
        rline_des = float(rline[len(rline) // 2])

    interp_wc = RegularGridInterpolator((nc, rline), wc)
    interp_pr = RegularGridInterpolator((nc, rline), pr)
    interp_eta = RegularGridInterpolator((nc, rline), eta)

    wc_des = float(interp_wc([[nc_des, rline_des]])[0])
    pr_des = float(interp_pr([[nc_des, rline_des]])[0])
    eta_des = float(interp_eta([[nc_des, rline_des]])[0])

    return {
        "path": xml_path,
        "nc": nc,
        "rline": rline,
        "wc": wc,
        "pr": pr,
        "eta": eta,
        "nc_des": nc_des,
        "rline_des": rline_des,
        "wc_des": wc_des,
        "pr_des": pr_des,
        "eta_des": eta_des,
    }


def parse_turbine_xml(xml_path: str) -> dict:
    """
    Parse a turbine XML map file (e.g. Turboprop_ggt_Rline.xml).

    Returns same structure as parse_compressor_xml (nc, rline, wc, pr, eta, design anchors).
    """
    root = ET.parse(xml_path).getroot()

    flow_mat = _find_matrix(root, ["correctedFlow", "wc", "wcorr", "flow"])
    pr_mat = _find_matrix(root, ["pressureRatio", "expansionRatio", "pr"])
    eta_mat = _find_matrix(root, ["isentropicEfficiency", "efficiency", "eta"])

    if flow_mat is None or pr_mat is None or eta_mat is None:
        raise ValueError(f"Matrix tags not found in {xml_path}. Check XML schema.")

    rline = flow_mat[0, 1:]
    nc = flow_mat[1:, 0]
    wc = flow_mat[1:, 1:]
    pr = pr_mat[1:, 1:]
    eta = eta_mat[1:, 1:]

    des_nc_node = root.find("design/correctedSpeed")
    des_rl_node = root.find("design/rLine")
    if des_nc_node is not None and des_rl_node is not None:
        nc_des = float(des_nc_node.text)
        rl_des = float(des_rl_node.text)
    else:
        nc_des = float(nc[len(nc) // 2])
        rl_des = float(rline[len(rline) // 2])

    interp_wc = RegularGridInterpolator((nc, rline), wc)
    interp_pr = RegularGridInterpolator((nc, rline), pr)
    interp_eta = RegularGridInterpolator((nc, rline), eta)

    wc_des = float(interp_wc([[nc_des, rl_des]])[0])
    pr_des = float(interp_pr([[nc_des, rl_des]])[0])
    eta_des = float(interp_eta([[nc_des, rl_des]])[0])

    return {
        "path": xml_path,
        "nc": nc,
        "rline": rline,
        "wc": wc,
        "pr": pr,
        "eta": eta,
        "nc_des": nc_des,
        "rline_des": rl_des,
        "wc_des": wc_des,
        "pr_des": pr_des,
        "eta_des": eta_des,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Design-Point Scaling
# ═══════════════════════════════════════════════════════════════════════════

def corrected_from_actual(mdot, Tt, Pt, t_ref=T_REF, p_ref=P_REF):
    """Convert actual mass flow → corrected mass flow."""
    return mdot * np.sqrt(Tt / t_ref) / (Pt / p_ref)


def actual_from_corrected(wc_corr, Tt, Pt, t_ref=T_REF, p_ref=P_REF):
    """Convert corrected mass flow → actual mass flow."""
    return wc_corr * (Pt / p_ref) / np.sqrt(Tt / t_ref)


def scale_compressor_map(parsed: dict, target: dict) -> dict:
    """
    Scale a parsed compressor map to a target design point.

    Parameters
    ----------
    parsed : dict
        Output of parse_compressor_xml().
    target : dict
        Must contain keys:
            m_flow_des : float — actual mass flow [kg/s]
            PRdes      : float — pressure ratio
            effDes     : float — isentropic efficiency
            T1_des     : float — inlet temperature [K]
            p1_des     : float — inlet pressure [Pa]

    Returns
    -------
    dict with keys:
        wc_scaled_actual, wc_scaled_corr, pr_scaled, eta_scaled,
        wc_target_corr,
        s_Wc_actual, s_Wc_corr, s_PR, s_eff,
        nc, rline  (copied from parsed)
    """
    wc_target_corr = corrected_from_actual(
        target["m_flow_des"], target["T1_des"], target["p1_des"]
    )

    s_Wc_actual = target["m_flow_des"] / parsed["wc_des"]
    s_Wc_corr = float(wc_target_corr) / parsed["wc_des"]
    s_PR = (target["PRdes"] - 1.0) / (parsed["pr_des"] - 1.0)
    s_eff = target["effDes"] / parsed["eta_des"]

    wc_scaled_actual = parsed["wc"] * s_Wc_actual
    wc_scaled_corr = parsed["wc"] * s_Wc_corr
    pr_scaled = (parsed["pr"] - 1.0) * s_PR + 1.0
    eta_scaled = parsed["eta"] * s_eff

    return {
        "wc_scaled_actual": wc_scaled_actual,
        "wc_scaled_corr": wc_scaled_corr,
        "pr_scaled": pr_scaled,
        "eta_scaled": eta_scaled,
        "wc_target_corr": float(wc_target_corr),
        "s_Wc_actual": float(s_Wc_actual),
        "s_Wc_corr": float(s_Wc_corr),
        "s_PR": float(s_PR),
        "s_eff": float(s_eff),
        "nc": parsed["nc"],
        "rline": parsed["rline"],
    }


def scale_turbine_map(parsed: dict, target: dict) -> dict:
    """
    Scale a parsed turbine map to a target design point.

    Parameters
    ----------
    parsed : dict
        Output of parse_turbine_xml().
    target : dict
        Same keys as scale_compressor_map target.

    Returns
    -------
    dict with same structure as scale_compressor_map output.
    """
    wc_target_corr = corrected_from_actual(
        target["m_flow_des"], target["T1_des"], target["p1_des"]
    )

    s_Wc_actual = target["m_flow_des"] / parsed["wc_des"]
    s_Wc_corr = float(wc_target_corr) / parsed["wc_des"]
    s_PR = (target["PRdes"] - 1.0) / (parsed["pr_des"] - 1.0)
    s_eff = target["effDes"] / parsed["eta_des"]

    wc_scaled_actual = parsed["wc"] * s_Wc_actual
    wc_scaled_corr = parsed["wc"] * s_Wc_corr
    pr_scaled = (parsed["pr"] - 1.0) * s_PR + 1.0
    eta_scaled = parsed["eta"] * s_eff

    return {
        "wc_scaled_actual": wc_scaled_actual,
        "wc_scaled_corr": wc_scaled_corr,
        "pr_scaled": pr_scaled,
        "eta_scaled": eta_scaled,
        "wc_target_corr": float(wc_target_corr),
        "s_Wc_actual": float(s_Wc_actual),
        "s_Wc_corr": float(s_Wc_corr),
        "s_PR": float(s_PR),
        "s_eff": float(s_eff),
        "nc": parsed["nc"],
        "rline": parsed["rline"],
    }
