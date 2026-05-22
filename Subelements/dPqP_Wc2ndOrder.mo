within PropulsionSystem.Subelements;

model dPqP_Wc2ndOrder
  extends PropulsionSystem.Interfaces.SubelementFrames.SubelementFrame;
  import Modelica.Constants;
  
  /********************************************************
   Declaration
  ********************************************************/
  //********** Package **********
  outer replaceable package Medium= Modelica.Media.Interfaces.PartialMedium;
  
  
  //********** Parameters **********
  //##### none #####
  
  
  //********** Internal variables **********
  Modelica.Units.SI.MassFlowRate Wc;
  Real dPqP_internal;
  
  outer Real k_dPqP;
  outer Modelica.Units.SI.MassFlowRate dm;
  outer Medium.BaseProperties fluid_I "flow station of inlet";
  
  constant Modelica.Units.SI.Temperature Tstd= 288.15;
  constant Modelica.Units.SI.AbsolutePressure pStd= 101.315*1000;
  
  
  //********** Interfaces **********
  //##### none #####
  
  
  //********** Initialization **********
  //##### none #####
  
  
//********** Protected objects **********
//##### none #####

algorithm
  //##### none #####
  
equation
  //********** Geometries **********
  //##### none #####
  
  
  //********** Connections, interface <-> internal variables **********
  //##### none #####
  
  //********** Eqns describing physics **********
  Wc= dm* sqrt(fluid_I.T/Tstd) / (fluid_I.p/pStd);
  dPqP_internal= k_dPqP* Wc^2.0;
  
  
/********************************************************
  Graphics
********************************************************/
  
  annotation(
    Diagram,
    Icon(graphics={
    
    Rectangle(lineColor = {255, 0, 0}, fillColor = {255, 0, 0}, lineThickness = 4, extent = {{-100, 100}, {100, -100}}), Line(points = {{-100, 100}, {100, -100}}, color = {255, 0, 0}, thickness = 4)
    
    },
    coordinateSystem(initialScale = 0.1))
    );
  
end dPqP_Wc2ndOrder;
