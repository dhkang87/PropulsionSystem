library ieee;
use ieee.math_real.all;
use ieee.fluidic_systems.all;

entity inlet is
    generic (
                t_amb0      : real  := 288.15;      -- ambient air temperature at sea level [K].
                p_amb0      : real  := 101325.0;    -- ambient air pressure at sea level [Pa].
                gamma       : real  := 1.4          -- ratio of specific heats.
            );

    port    (
                quantity altitude     : in real;                 -- flight altitude [m].
                quantity mach         : in real;                 -- mach number.
                quantity t_out        : out real;                -- output temperature for inlet [K].
                quantity p_out        : out real;                -- output pressure for inlet [Pa].
                quantity p_amb        : out real;                -- ambient pressure [Pa].
                quantity t_amb        : out real;                -- ambient temperature [K].
                terminal cfluid_a     : compressible_fluidic
            );
begin
    assert t_amb0 > 0.0
        report "WARNING: t_amb0 must be greater than 0.0."
        severity warning;

    assert p_amb0 > 0.0
        report "WARNING: p_amb0 must be greater than 0.0."
        severity warning;

    assert gamma > 0.0
        report "WARNING: gamma must be greater than 0.0."
        severity warning;

end entity inlet;

architecture behav of inlet is

    constant a1          : real := 0.0065;      -- coefficient to calculate air condition.
    constant a2          : real := 5.2561;      -- coefficient to calculate air condition.
    constant t_amb_c     : real := 216.69;      -- ambient temperature when altitude between 11000m and 25000m.
    constant a3          : real := 22632.0;     -- coefficient to calculate air condition.
    constant a4          : real := 1.733;       -- coefficient to calculate air condition.
    constant a5          : real := 0.000157;    -- coefficient to calculate air condition.

    quantity t_amb_t : real := t_amb0;
    quantity p_amb_t : real := p_amb0;
    quantity test : real;
    quantity t_temp : real;
    quantity p_temp : real;
    quantity p_out_t : real;

    quantity pressure across mflow through cfluid_a to compressible_fluidic_ref;

    function eta_cal(mach: real)
    return real is
    variable eta : real;
    constant a6  : real := 0.075;       -- coefficient to calculate air condition.
    constant a7  : real := 1.35;        -- coefficient to calculate air condition.
    begin
        if mach <= 1.0 then
            eta := 1.0;
        else
            eta := 1.0 - a6 * ((mach - 1.0) ** a7);
        end if;
    return eta;
    end function eta_cal;

begin
    assert not altitude'above(25000.0) -- altitude'above(25000.0) is not supported
        report "ERROR: altitude above 25000.0 is not supported."
        severity error;

    if not altitude'above(11000.0) use
        t_amb_t == t_amb0 - (a1 * altitude);
        p_amb_t == p_amb0 * ((t_amb_t / t_amb0) ** a2);
    else
        t_amb_t == t_amb_c;
        p_amb_t == a3 * exp(a4 - a5 * altitude);
    end use;

    t_temp == t_amb_t * (1.0 + ((gamma - 1.0) / 2.0) * (mach ** 2.0));
    p_temp == p_amb_t * ((1.0 + ((gamma - 1.0) / 2.0) * (mach ** 2.0)) ** (gamma / (gamma - 1.0)));

    t_out == t_temp;
    p_out_t == p_temp * eta_cal(mach);
    pressure == p_out_t;
    p_out == p_out_t;

    t_amb == t_amb_t;
    p_amb == p_amb_t;

end architecture behav;
