library ieee;
use ieee.math_real.all;
use ieee.fluidic_systems.all;

entity combustor is
    generic (
                eff         : real := 0.95     -- combustor pressure loss efficiency.
            );
    port    (
                -- to simplify the model, the combustor input temperature is selected as the control signal.
                quantity comb_ref               : in real := 1800.0;      -- combustor input temperature from controller [K].
                quantity t_in                   : in real;                -- combustor inlet temperature [K].
                quantity fa_ratio               : out real;               -- fuel air ratio.
                quantity t_out                  : out real;               -- combustor outlet temperature [K].
                terminal cfluid_a, cfluid_b, fuel : compressible_fluidic  -- fluidic terminal.
            );
begin
    assert eff >= 0.0 and eff <= 1.0
        report "Error : eff must be in the range of [0, 1]."
        severity error;

end entity combustor;

architecture behav of combustor is
    constant gamma : real := 1.31;                          -- specific heats ratio.
    constant r : real := 287.04;                            -- universal gas constant. [J/kg*K]
    constant cp : real := gamma * r / (gamma - 1.0);
    constant fuel_calorific : real := 42075500.0;           -- fuel low calorific value [J/kg].

    quantity pressure across mflow through cfluid_a to cfluid_b;

    quantity p_in across cfluid_a to compressible_fluidic_ref;

    quantity mflow_fuel through fuel;                       -- fuel consumption.
    quantity p_out_temp : real;
    quantity t_out_temp : real;
    quantity fuel_air_ratio : real;

begin
    -- outlet conditions.
    t_out_temp == comb_ref;
    p_out_temp == eff * p_in;

    -- calculate needed fuel/air ratio to provide the demand output temperature.
    fuel_air_ratio == ((t_out_temp / t_in) - 1.0) / (fuel_calorific / (cp * t_in) - t_out_temp / t_in);

    -- fuel consumption.
    mflow_fuel == fuel_air_ratio * mflow;

    pressure == p_in - p_out_temp;
    t_out == t_out_temp;
    fa_ratio == fuel_air_ratio;

end architecture behav;
