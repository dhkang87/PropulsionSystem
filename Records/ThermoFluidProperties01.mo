within PropulsionSystem.Records;

record ThermoFluidProperties01
  extends Modelica.Icons.Record;
  
  parameter Boolean fixed=false;
  parameter Boolean HideResult=false;
  
  parameter Integer nX;
  parameter Integer nC;
  
  parameter Modelica.Units.SI.MassFlowRate m_flow(fixed=fixed) annotation(
    HideResult=false);
  parameter Modelica.Units.SI.Pressure p(fixed=fixed) annotation(
    HideResult=false);
  parameter Modelica.Units.SI.Temperature T(fixed=fixed) annotation(
    HideResult=false);
  parameter Modelica.Units.SI.SpecificEnthalpy h(fixed=fixed) annotation(
    HideResult=false);
  parameter Modelica.Units.SI.MassFraction X[nX](each fixed=fixed) annotation(
    HideResult=false);
  parameter Real C[nC](each fixed=fixed) annotation(
    HideResult=false);
  parameter Modelica.Units.SI.SpecificEntropy s(fixed=fixed) annotation(
    HideResult=false);
  
end ThermoFluidProperties01;
