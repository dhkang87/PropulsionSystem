within PropulsionSystem.Records;

record TurbineVariables
  extends Modelica.Icons.Record;
  
  
  parameter Boolean fixed=false;
  parameter Boolean HideResult=false;
  
  Modelica.Units.SI.Power pwr(fixed=fixed) annotation(
    HideResult=false);
  Modelica.Units.SI.Torque trq(fixed=fixed) annotation(
    HideResult=false);
  Modelica.Units.SI.Power pwr_inv(fixed=fixed) annotation(
    HideResult=false);
  Modelica.Units.SI.Torque trq_inv(fixed=fixed) annotation(
    HideResult=false);
  Modelica.Units.SI.AngularVelocity omega(fixed=fixed) annotation(
    HideResult=false);
  Modelica.Units.SI.Angle phi(fixed=fixed) annotation(
    HideResult=false);
  Modelica.Units.NonSI.AngularVelocity_rpm Nmech(fixed=fixed) annotation(
    HideResult=false);
  Modelica.Units.SI.MassFlowRate Wc_1(fixed=fixed) annotation(
    HideResult=false);
  Modelica.Units.NonSI.AngularVelocity_rpm Nc_1(fixed=fixed) annotation(
    HideResult=false);
  Real PR(fixed=fixed) annotation(
    HideResult=false);
  Real eff(fixed=fixed) annotation(
    HideResult=false);
  Modelica.Units.SI.SpecificEnthalpy dht(fixed=fixed) annotation(
    HideResult=false);
  Modelica.Units.SI.SpecificEnthalpy dht_is(fixed=fixed) annotation(
    HideResult=false);
  Modelica.Units.SI.SpecificEnthalpy h_2is(fixed=fixed) annotation(
    HideResult=false);
  
  
end TurbineVariables;
