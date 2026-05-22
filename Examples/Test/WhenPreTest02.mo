within PropulsionSystem.Examples.Test;

model WhenPreTest02
  "Test: when with time condition that stays true (like the library pattern)"
  extends Modelica.Icons.Example;
  
  // continuous variables
  Real x(start=5.0);
  Real y(start=10.0);
  
  // discrete variables - library pattern: capture and hold
  discrete Real x_des(start=0.0);
  discrete Real y_des(start=0.0);
  
  // time boundary (like environment.timeRemoveDesConstraint)
  parameter Real timeFreeze = 0.0;
  
equation
  // continuous equations
  x = 5.0 + time * 2.0;
  y = 10.0 - time * 3.0;
  
  // Pattern from the library: when (time <= timeFreeze)
  when (time <= timeFreeze) then
    x_des = pre(x_des);
    y_des = pre(y_des);
  end when;

  annotation(
    experiment(StartTime = 0, StopTime = 1, Tolerance = 1e-06, Interval = 0.01)
  );
end WhenPreTest02;
