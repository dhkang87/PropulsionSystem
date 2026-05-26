within PropulsionSystem.Utilities;

block SetDependent "Mark a dependent variable with target value (input block)"
  parameter Real tgtVal = 1.0 "Target value for the dependent variable";
  Modelica.Blocks.Interfaces.RealInput dependent_in;
equation
  dependent_in = tgtVal;
  annotation(
    defaultComponentName = "setDependent",
    Icon(coordinateSystem(initialScale = 0.1), graphics = {
      Rectangle(fillColor = {255, 170, 85}, fillPattern = FillPattern.Solid, extent = {{-100, 100}, {100, -100}}),
      Text(origin = {0, 0}, lineColor = {255, 255, 255}, extent = {{-80, 30}, {80, -30}}, textString = "SetDep"),
      Text(origin = {0, -120}, extent = {{-100, 20}, {100, -20}}, textString = "%name")}));
end SetDependent;
