library ieee;
use ieee.math_real.all;
use ieee.fluidic_systems.all;
use ieee.mechanical_systems.all;

entity compressor is
    generic (
                pressureRatio   : real := 8.0;     -- outlet pressure / inlet pressure of compressor.
                eta_comp        : real := 0.85     -- isentropic efficiency of compressor.
            );

    port    (
                quantity t_in       : in real;     -- compressor inlet temperature [K].
                quantity temp_diff  : out real;    -- compressor temperature difference [K].
                quantity power      : out real;
                quantity t_out      : out real;    -- compressor outlet temperature [K].
                terminal cfluid_a, cfluid_b : compressible_fluidic
            );
begin

    assert pressureRatio > 0.0
        report "Error: pressureRatio must be positive."
        severity error;

    assert eta_comp >= 0.0 and eta_comp <= 1.0
        report "Error : eta_comp must be in the range of [0, 1]."
        severity error;

end entity compressor;

architecture behav of compressor is
    constant gamma : real := 1.4;                     -- ratio of specific heats in compressor.
    constant r : real := 287.04;                      -- universal gas constant. [J/kg*K]
    constant cp : real := gamma * r / (gamma - 1.0);

    quantity pressure across mflow through cfluid_a to cfluid_b;
    quantity p_in across cfluid_a to compressible_fluidic_ref;
    quantity p_out_temp : real;
    quantity t_out_temp : real;

    subtype real_vector2 is real_vector(0 to 1);

    -- function to calculate temperature and pressure in compressor.
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

    -- calculate temperature and pressure in compressor.
    (t_out_temp, p_out_temp) == temp_pre_calculation(eta_comp, pressureRatio, t_in, p_in);

    temp_diff == t_in - t_out_temp;

    pressure == p_in - p_out_temp;
    t_out == t_out_temp;

    power == mflow * cp * (t_out_temp - t_in);

end architecture behav;
