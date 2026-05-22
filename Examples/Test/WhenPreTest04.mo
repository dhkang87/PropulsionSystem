within PropulsionSystem.Examples.Test;

model WhenPreTest04
  "Test: equation section for discrete variables (current approach)"
  extends Modelica.Icons.Example;
  
  // continuous variables
  Real x(start=5.0);
  Real y(start=10.0);
  
  // variables as plain Real (no discrete)
  Real x_des;
  Real y_des;
  
equation
  // continuous equations
  x = 5.0 + time * 2.0;
  y = 10.0 - time * 3.0;
  
  // direct assignment in equation (always equal)
  x_des = 5.0;   // parameter value
  y_des = 10.0;  // parameter value

  annotation(
    experiment(StartTime = 0, StopTime = 1, Tolerance = 1e-06, Interval = 0.01)
  );
end WhenPreTest04;
