--  --------------------------------------------------------------------------
--                                                                      --
-- Copyright (c) 2004 by ANSOFT Corp.  All rights reserved.             --
--                                                                      --
-- This source file may be used and distributed without restriction     --
-- provided that this copyright statement is not removed from the file  --
-- and that any derivative work contains this copyright notice.         --
--                                                                      --
-- Model name: Mass                                                     --
-- Library: Basic_VHDLAMS                                               --
--                                                                      --
-- ----------------------------------------------------------------------------
--                 Warranty
-- ----------------------------------------------------------------------------
-- ANSOFT Corporation makes no warranty of any kind with regard to the use of
-- this Software, either expressed or implied, including, but not limited to 
-- the fitness for a particular purpose.
-- 
-- ----------------------------------------------------------------------------
-- Modification History : 
-- ----------------------------------------------------------------------------
-- Version No:|Auth:| Mod.Date:| Changes Made:
--            |     |          | 
-- ----------------------------------------------------------------------------
LIBRARY IEEE;
USE IEEE.MECHANICAL_SYSTEMS.ALL;

ENTITY mass_rot IS
  GENERIC(
    phi0  : ANGLE := 0.0;
    omega0 : ANGULAR_VELOCITY := 0.0);
  PORT(
        QUANTITY j : MOMENT_INERTIA := 1.0;
        TERMINAL rot1 : ROTATIONAL_V );
END ENTITY mass_rot;

ARCHITECTURE behav of mass_rot IS
  QUANTITY omega ACROSS m THROUGH rot1 TO rotational_v_ref;
  QUANTITY phi : ANGLE;
  QUANTITY acc : ANGULAR_ACCELERATION;
BEGIN
  IF (domain = quiescent_domain) USE
    phi == phi0;
    omega == omega0;
  ELSE
    phi'dot == omega;
    omega'dot == acc;
  END USE;
    m == j*acc;
END ARCHITECTURE behav;
