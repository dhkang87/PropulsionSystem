library ieee;
use ieee.math_real.all;
use ieee.fluidic_systems.all;
use ieee.mechanical_systems.all;

entity turbine is
    generic (
                eta_t       : real := 0.87;       -- turbine efficiency.
                eta_m       : real := 0.98        -- mechanical efficiency of the turbine shaft
            );
    port    (
                quantity temp_diff_comp : in real;    -- compressor temperature difference, t_in - t_out.
                quantity far_comb       : in real;    -- fuel air ratio from combustor.
                quantity t_in           : in real;    -- turbine inlet temperature [K].
                quantity power          : out real;
                quantity t_out          : out real;   -- turbine outlet temperature [K].
                terminal cfluid_a, cfluid_b : compressible_fluidic;     -- fluidic terminal.
                terminal mech_rv        : rotational_velocity
            );

end entity turbine;

architecture behav of turbine is

    constant gamma : real := 1.31;                          -- specific heats ratio.
    constant r : real := 287.04;                            -- universal gas constant. [J/kg*K]
    constant cp : real := gamma * r / (gamma - 1.0);

    quantity pressure across mflow through cfluid_a to cfluid_b;
    quantity p_in across cfluid_a to compressible_fluidic_ref;
    quantity omega across tau through mech_rv;
    quantity p_out_temp : real;
    quantity t_out_temp : real;

    subtype real_vector2 is real_vector(0 to 1);

    -- function to calculate the temperature and pressure in turbine
    function temp_pre_calculation(t_in, p_in, temp_diff_comp, far_comb, eta_t, eta_m, gamma: real)
    return real_vector2 is
    variable temperature1, pressure1 : real;
    begin
        temperature1 := t_in + temp_diff_comp * eta_m * (1.0 + far_comb);
        pressure1 := p_in * ((1.0 - (1.0 - temperature1 / t_in) / eta_t) ** (gamma / (gamma - 1.0)));
    return (temperature1, pressure1);
    end function temp_pre_calculation;

begin
    -- calculate the turbine output temperature and pressure.
    (t_out_temp, p_out_temp) == temp_pre_calculation(t_in, p_in, temp_diff_comp, far_comb, eta_t, eta_m, gamma);

    pressure == p_in - p_out_temp;
    t_out == t_out_temp;

    power == - mflow * cp * (t_in - t_out_temp);

    omega * tau == power;

end architecture behav;
