--------------------------------------------------------------------------
--                                                                      --
-- Copyright (c) 2014 by ANSYS Inc.  All rights reserved.             	--
--                                                                      --
-- This source file may be used and distributed without restriction     --
-- provided that this copyright statement is not removed from the file  --
-- and that any derivative work contains this copyright notice.         --
--                                                                      --
-- Model name: shaft     		                      			       	--
-- Library: Aircraft Electrical VHDLAMS                                	--
-- 																		--
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
use ieee.mechanical_systems.all;

entity shaft is
	generic (
                inertia      	: real  := 1.0;                     -- shaft inertia [kg * m^2].
                omega0          : real  := 0.0
            );   
    port    ( 
               terminal a,b     : rotational_velocity
            );

end entity shaft;

architecture behav of shaft is
    quantity omega across tau through a to b;   
begin
    if domain = quiescent_domain use
        omega == omega0;
    else
        omega'dot == tau / inertia;
    end use;
end architecture behav;
