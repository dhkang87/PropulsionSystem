library ieee;
use ieee.math_real.all;
use ieee.fluidic_systems.all;

entity compressor_map_based is
    generic (
        pressureRatio_nom : real := 8.0;
        eta_comp_peak     : real := 0.87;
        wcorr_des         : real := 235.0;
        pr_des            : real := 8.0;
        k_wcorr           : real := 8.0;
        k_pr              : real := 0.5;
        eta_min           : real := 0.50;
        eta_max           : real := 0.92;
        t_ref             : real := 288.15;
        p_ref             : real := 101325.0
    );
    port (
        quantity t_in     : in real;
        quantity temp_diff: out real;
        quantity power    : out real;
        quantity t_out    : out real;
        terminal cfluid_a, cfluid_b : compressible_fluidic
    );
begin
    assert pressureRatio_nom > 0.0 report "pressureRatio_nom must be positive" severity error;
    assert eta_comp_peak > 0.0 and eta_comp_peak <= 1.0 report "eta_comp_peak out of range" severity error;
    assert t_ref > 0.0 and p_ref > 0.0 report "map references must be positive" severity error;
    assert wcorr_des > 0.0 report "wcorr_des must be positive" severity error;
end entity compressor_map_based;

architecture behav of compressor_map_based is
    constant gamma : real := 1.4;
    constant r     : real := 287.04;
    constant cp    : real := gamma * r / (gamma - 1.0);

    quantity pressure across mflow through cfluid_a to cfluid_b;
    quantity p_in across cfluid_a to compressible_fluidic_ref;
    quantity p_out_temp : real;
    quantity t_out_temp : real;
    quantity w_corr     : real;
    quantity w_corr_norm: real;

    subtype real_vector2 is real_vector(0 to 1);

    function clamp_real(x, lo, hi : real) return real is
    begin
        if x < lo then return lo; end if;
        if x > hi then return hi; end if;
        return x;
    end function;

    function safe_pos(x, lo : real) return real is
    begin
        if x < lo then return lo; end if;
        return x;
    end function;

    function eta_c_map(eta_peak, wc_norm, pr_ratio : real) return real is
        variable eta_local : real;
        variable pr_norm   : real;
    begin
        pr_norm := pr_ratio / pr_des;
        eta_local := eta_peak
                     - k_wcorr * (wc_norm - 1.0) * (wc_norm - 1.0)
                     - k_pr    * (pr_norm - 1.0) * (pr_norm - 1.0);
        return clamp_real(eta_local, eta_min, eta_max);
    end function;

    function temp_pre_calculation(efficiency, pressure_ratio, t1, p1: real)
    return real_vector2 is
        variable temperature2, pressure2 : real;
    begin
        temperature2 := (1.0 + (pressure_ratio ** ((gamma - 1.0) / gamma) - 1.0) / efficiency) * t1;
        pressure2 := pressure_ratio * p1;
        return (temperature2, pressure2);
    end function;

begin
    w_corr == mflow * sqrt(safe_pos(t_in, 1.0) / t_ref) / (safe_pos(p_in, 1.0) / p_ref);
    w_corr_norm == w_corr / wcorr_des;
    (t_out_temp, p_out_temp) == temp_pre_calculation(
        eta_c_map(eta_comp_peak, w_corr_norm, pressureRatio_nom),
        pressureRatio_nom,
        t_in,
        p_in
    );
    temp_diff == t_in - t_out_temp;
    pressure == p_in - p_out_temp;
    t_out == t_out_temp;
    power == mflow * cp * (t_out_temp - t_in);
end architecture behav;
