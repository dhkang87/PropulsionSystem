library ieee;
use ieee.math_real.all;
use ieee.fluidic_systems.all;
use ieee.mechanical_systems.all;

entity turbine_map_based is
    generic (
        eta_t_peak   : real := 0.90;
        eta_m        : real := 0.98;
        n_corr_des   : real := 9000.0;
        pr_des       : real := 2.05;
        k_ncorr      : real := 2.0e-9;
        k_pr         : real := 0.10;
        eta_t_min    : real := 0.55;
        eta_t_max    : real := 0.93;
        t_ref        : real := 288.15
    );
    port (
        quantity temp_diff_comp : in real;
        quantity far_comb       : in real;
        quantity t_in           : in real;
        quantity power          : out real;
        quantity t_out          : out real;
        terminal cfluid_a, cfluid_b : compressible_fluidic;
        terminal mech_rv            : rotational_velocity
    );
begin
    assert eta_t_peak > 0.0 and eta_t_peak <= 1.0 report "eta_t_peak out of range" severity error;
    assert t_ref > 0.0 report "t_ref must be positive" severity error;
end entity turbine_map_based;

architecture behav of turbine_map_based is
    constant gamma : real := 1.31;
    constant r     : real := 287.04;
    constant cp    : real := gamma * r / (gamma - 1.0);
    constant pi    : real := 3.141592653589793;

    quantity pressure across mflow through cfluid_a to cfluid_b;
    quantity p_in across cfluid_a to compressible_fluidic_ref;
    quantity omega across tau through mech_rv;
    quantity p_out_temp : real;
    quantity t_out_temp : real;

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

    function eta_t_map(eta_peak, n_corr, prx : real) return real is
        variable eta_local : real;
    begin
        eta_local := eta_peak
                     - k_ncorr * (n_corr - n_corr_des) * (n_corr - n_corr_des)
                     - k_pr    * (prx    - pr_des)     * (prx    - pr_des);
        return clamp_real(eta_local, eta_t_min, eta_t_max);
    end function;

    function temp_pre_calculation(t1, p1, dT_comp, far, eta_m_in, omega_in: real)
    return real_vector2 is
        variable temperature2, pressure2 : real;
        variable n_rpm, n_corr, pr_proxy, eta_eff : real;
    begin
        temperature2 := t1 + dT_comp * eta_m_in * (1.0 + far);
        n_rpm := abs(omega_in) * 30.0 / pi;
        n_corr := n_rpm / sqrt(safe_pos(t1, 1.0) / t_ref);
        pr_proxy := safe_pos(t1 / safe_pos(temperature2, 1.0), 1.0);
        eta_eff := eta_t_map(eta_t_peak, n_corr, pr_proxy);
        pressure2 := p1 * ((1.0 - (1.0 - temperature2 / safe_pos(t1, 1.0)) / eta_eff) ** (gamma / (gamma - 1.0)));
        return (temperature2, pressure2);
    end function;

begin
    (t_out_temp, p_out_temp) == temp_pre_calculation(t_in, p_in, temp_diff_comp, far_comb, eta_m, omega);
    pressure == p_in - p_out_temp;
    t_out == t_out_temp;
    power == -mflow * cp * (t_in - t_out_temp);
    omega * tau == power;
end architecture behav;
