library ieee;
use ieee.math_real.all;
use ieee.fluidic_systems.all;

entity compressor_map_based is
    port (
        quantity t_in       : in real;        -- [K] compressor inlet temperature
        quantity eta_in     : in real;        -- [-] isentropic efficiency (from external 2D LUT)
        quantity pr_in      : in real;        -- [-] pressure ratio (from external 2D LUT)
        quantity temp_diff  : out real;       -- [K] temperature difference (T_in - T_out)
        quantity power      : out real;       -- [W] compressor power
        quantity t_out      : out real;       -- [K] compressor outlet temperature
        terminal cfluid_a, cfluid_b : compressible_fluidic
    );
begin
end entity compressor_map_based;

architecture behav of compressor_map_based is
    constant gamma : real := 1.4;                        -- [-] ratio of specific heats
    constant r : real := 287.04;                         -- [J/(kg*K)] gas constant
    constant cp : real := gamma * r / (gamma - 1.0);    -- [J/(kg*K)] specific heat
    constant eta_floor : real := 0.50;                   -- [-] minimum efficiency

    quantity pressure across mflow through cfluid_a to cfluid_b;  -- [Pa], [kg/s]
    quantity p_in across cfluid_a to compressible_fluidic_ref;    -- [Pa]
    quantity p_out_temp : real;  -- [Pa]
    quantity t_out_temp : real;  -- [K]
    quantity eta_safe : real;    -- [-] clamped efficiency

    subtype real_vector2 is real_vector(0 to 1);

    function temp_pre_calculation(efficiency, pressure_ratio, t_in, p_in: real)
    return real_vector2 is
        variable temperature, pressure : real;
        constant gamma : real := 1.4;
    begin
        temperature := (1.0 + 1.0 / efficiency * (pressure_ratio ** ((gamma - 1.0) / gamma) - 1.0)) * t_in;
        pressure := pressure_ratio * p_in;
        return (temperature, pressure);
    end function temp_pre_calculation;

begin
    -- smooth clamp: ensures eta never drops below eta_floor
    eta_safe == eta_floor + (eta_in - eta_floor) * eta_in / sqrt(eta_in * eta_in + 0.01);

    (t_out_temp, p_out_temp) == temp_pre_calculation(
        eta_safe,
        pr_in,
        t_in,
        p_in
    );

    temp_diff == t_in - t_out_temp;            -- [K]
    pressure == p_in - p_out_temp;             -- [Pa]
    t_out == t_out_temp;                       -- [K]
    power == mflow * cp * (t_out_temp - t_in); -- [W]
end architecture behav;
