--------------------------------------------------------------------------
--                                                                      --
-- Copyright (c) 2014 by ANSYS Inc.  All rights reserved.             	--
--                                                                      --
-- This source file may be used and distributed without restriction     --
-- provided that this copyright statement is not removed from the file  --
-- and that any derivative work contains this copyright notice.         --
--                                                                      --
-- Model name: nozzle          	                      			       	--
-- Library: Aircraft Electrical VHDLAMS                                	--
-- @reference                                                           --
-- S. Yarlagadda, "Performance Analysis of J85 Turbojet Engine Matching --
-- Thrust with Reduced Inlet Pressure to the Compressor", Master Thesis,--
-- 2010.                                                                --
-- A.F. El-Sayed, "Aircraft Propulsion and Gas Turbine Engines", CRC    --
-- Press, July, 2011.                                                   --
-- -----------------------------------------------------------------------
--                 Warranty                                             --
-- -----------------------------------------------------------------------
-- ANSYS Incorporation makes no warranty of any kind with regard to the --
-- use of this Software, either expressed or implied, including, but not--
-- limited to the fitness for a particular purpose.						--
-- 																		--
-- -----------------------------------------------------------------------
-- Modification History :                                               --
-- -----------------------------------------------------------------------
-- Version No:|Auth:| Mod.Date:| Changes Made:                          --
-- -----------------------------------------------------------------------
library ieee;
use ieee.math_real.all;
use ieee.fluidic_systems.all;

entity nozzle is
	generic (
                area      : real  := 0.3                                    -- nozzle area [m^2].
            );		
    port    ( 
                quantity pressure_in            : in real;                  -- pressure input from inlet.
                quantity t_in                   : in real;                  -- nozzle inlet temperature [K].
                quantity air_vel                : out real;                 -- nozzle output gas velocity [m/s].
                quantity mdot_nozzle            : out real;                 -- nozzle output mass flow rate [kg/s].
                quantity thrust                 : out real;
                terminal cfluid_a               : compressible_fluidic      -- fluidic terminal.  
            );

end entity nozzle;

architecture behav of nozzle is
    constant gamma : real := 1.31;
    constant r : real := 287.04;                            -- universal gas constant. [J/kg*K]
    constant cp : real := gamma * r / (gamma - 1.0);
    constant cv : real := cp / gamma;
    quantity p_in across mflow through cfluid_a to compressible_fluidic_ref;

    quantity p_cr : real;           -- nozzle exit critical pressure [Pa].
    quantity p_back : real;         -- nozzle back pressure [Pa].
    quantity p_exit : real;         -- nozzle exit pressure [Pa].

    subtype real_vector2 is real_vector(0 to 3);

    function calculation(p_in, t_in, gamma, area, p_cr, p_back: real)
    return real_vector2 is
    variable mdot, thrust_n, a_v, p_e : real;
    constant r : real := 287.04;                            -- universal gas constant. [J/kg*K]
    constant cp : real := gamma * r / (gamma - 1.0);
    constant cv : real := cp / gamma;
    begin
        if p_back > p_cr then
            p_e := p_back;
            mdot := p_in / sqrt(r * t_in) * area * ((p_e / p_in) ** (1.0 / gamma)) * sqrt(2.0 * gamma / (gamma - 1.0) * (1.0 - ((p_e / p_in) ** ((gamma - 1.0) / gamma))));
            thrust_n := mdot * sqrt(2.0 * cp * t_in * (1.0 - ((p_e / p_in) ** ((gamma - 1.0) / gamma))));
            a_v := sqrt(r * t_in * 2.0 * gamma / (gamma - 1.0) * (1.0 - ((p_e / p_in) ** ((gamma - 1.0) / gamma))));
        else
            p_e := p_cr;
            mdot := p_in / sqrt(r * t_in) * area * sqrt(gamma * ((2.0 / (gamma + 1.0)) ** ((gamma + 1.0) / (gamma - 1.0))));
            thrust_n := mdot * sqrt(2.0 * cp * t_in * (1.0 - ((p_cr / p_in) ** ((gamma - 1.0) / gamma)))) + area * (p_cr - p_e);
            a_v := sqrt(r * t_in * 2.0 * gamma / (gamma - 1.0) * (1.0 - ((p_e / p_in) ** ((gamma - 1.0) / gamma))));
        end if;
    return (mdot, thrust_n, a_v, p_e);
    end function calculation;
 
begin
    p_cr == ((2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))) * p_in;
    p_back == pressure_in;

    (mdot_nozzle, thrust, air_vel, p_exit) == calculation(p_in, t_in, gamma, area, p_cr, p_back);
    mflow == mdot_nozzle;

end architecture behav;
