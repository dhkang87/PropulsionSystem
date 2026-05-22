within PropulsionSystem.Examples.Test;

model WhenPreTest01
  "Simple test: when/pre() pattern for OCT compatibility check"
  extends Modelica.Icons.Example;
  
  // continuous variable
  Real x(start=1.0);
  
  // discrete variable with when/pre()
  discrete Real x_captured(start=0.0);
  
  // trigger time
  parameter Real captureTime = 0.1;
  
equation
  // x increases linearly
  x = 1.0 + time * 10.0;
  
  // capture x at captureTime using when/pre()
  when time >= captureTime then
    x_captured = pre(x_captured) + x;
  end when;

  annotation(
    experiment(StartTime = 0, StopTime = 1, Tolerance = 1e-06, Interval = 0.01)
  );
end WhenPreTest01;
