within PropulsionSystem.Utilities;

block SetIndependent "Set an independent variable value (output block)"
  parameter Real value = 0.0 "Independent variable value";
  Modelica.Blocks.Interfaces.RealOutput independent_out;
equation
  independent_out = value;
  annotation(
    defaultComponentName = "setIndependent",
    Icon(coordinateSystem(initialScale = 0.1), graphics = {
      Rectangle(fillColor = {85, 170, 255}, fillPattern = FillPattern.Solid, extent = {{-100, 100}, {100, -100}}),
      Text(origin = {0, 0}, lineColor = {255, 255, 255}, extent = {{-80, 30}, {80, -30}}, textString = "SetIndep"),
      Text(origin = {0, -120}, extent = {{-100, 20}, {100, -20}}, textString = "%name")}));
end SetIndependent;
