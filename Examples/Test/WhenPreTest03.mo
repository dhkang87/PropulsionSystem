within PropulsionSystem.Examples.Test;

model WhenPreTest03
  "Test: initial equation for discrete variables (our workaround)"
  extends Modelica.Icons.Example;
  
  // continuous variables
  Real x(start=5.0);
  Real y(start=10.0);
  
  // discrete variables - using initial equation instead of when/pre()
  discrete Real x_des(start=0.0, fixed=false);
  discrete Real y_des(start=0.0, fixed=false);
  
initial equation
  x_des = x;
  y_des = y;
  
equation
  // continuous equations
  x = 5.0 + time * 2.0;
  y = 10.0 - time * 3.0;

  annotation(
    experiment(StartTime = 0, StopTime = 1, Tolerance = 1e-06, Interval = 0.01)
  );
end WhenPreTest03;
