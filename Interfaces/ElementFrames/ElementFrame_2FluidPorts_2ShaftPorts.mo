within PropulsionSystem.Interfaces.ElementFrames;

partial model ElementFrame_2FluidPorts_2ShaftPorts
  /********************************************************
        imports
      ********************************************************/
  import Modelica.Constants;
  /********************************************************
        Declaration
      ********************************************************/
  //********** Package **********
  replaceable package Medium = Modelica.Media.Interfaces.PartialMedium annotation(
    choicesAllMatching = true);
  //********** Parameters **********
  parameter Boolean allowFlowReversal = true "= true to allow flow reversal, false restricts to design direction (port_a -> port_b)" annotation(
    Dialog(tab = "Assumptions"),
    Evaluate = true);
  //----- inner-connected parameters -----
  //-----
  inner parameter Modelica.Units.SI.MassFlowRate dmDes_1 = 10.0 "design point dm at st.1, refered in subelement" annotation(
    Dialog(group = "Design Point Definition"));
  inner parameter Modelica.Units.SI.AbsolutePressure pDes_1(displayUnit = "Pa") = 101.3 * 1000 "design point p at st.1, refered in subelement" annotation(
    Dialog(group = "Design Point Definition"));
  inner parameter Modelica.Units.SI.Temperature Tdes_1 = 288.15 "design point T at st.1, refered in subelement" annotation(
    Dialog(group = "Design Point Definition"));
  inner parameter Modelica.Units.NonSI.AngularVelocity_rpm NmechDes = 3000.0 "" annotation(
    Dialog(group = "Characteristics"));
  
  
  //********** Initialization Parameters **********
  //--- fluid_1, port_1 ---
  parameter Modelica.Units.SI.MassFlowRate m_flow1_init(displayUnit = "kg/s") = 1.0 "" annotation(
    Dialog(tab = "Initialization", group = "fluid_1"));
  parameter Modelica.Units.SI.Pressure p1_init(displayUnit = "Pa") = 101.3 * 1000 "" annotation(
    Dialog(tab = "Initialization", group = "fluid_1"));
  parameter Modelica.Units.SI.Temperature T1_init(displayUnit = "K") = 288.15 "" annotation(
    Dialog(tab = "Initialization", group = "fluid_1"));
  parameter Modelica.Units.SI.SpecificEnthalpy h1_init(displayUnit = "J/kg") = 1.004 * 1000 * 288.15 "" annotation(
    Dialog(tab = "Initialization", group = "fluid_1"));
  //--- fluid_2, port_2 ---
  parameter Modelica.Units.SI.MassFlowRate m_flow2_init(displayUnit = "kg/s") = -1.0 * m_flow1_init "" annotation(
    Dialog(tab = "Initialization", group = "fluid_2"));
  parameter Modelica.Units.SI.Pressure p2_init(displayUnit = "Pa") = 101.3 * 1000 "" annotation(
    Dialog(tab = "Initialization", group = "fluid_2"));
  parameter Modelica.Units.SI.Temperature T2_init(displayUnit = "K") = 288.15 "" annotation(
    Dialog(tab = "Initialization", group = "fluid_2"));
  parameter Modelica.Units.SI.SpecificEnthalpy h2_init(displayUnit = "J/kg") = 1.004 * 1000 * 288.15 "" annotation(
    Dialog(tab = "Initialization", group = "fluid_2"));
  
  
  //********** Internal variables **********
  Medium.BaseProperties fluid_1(p.start = p1_init, T.start = T1_init, state.p.start = p1_init, state.T.start = T1_init, h.start = h1_init) "flow station of inlet";
  Medium.BaseProperties fluid_2(p.start = p2_init, T.start = T2_init, state.p.start = p2_init, state.T.start = T2_init, h.start = h2_init) "flow station of outlet";
  Modelica.Units.SI.Power pwr "power via shaft, positive if fluid generates power";
  Modelica.Units.SI.Torque trq(start = 1.0) "trq via shaft";

  Modelica.Units.SI.Power pwr_inv "power via shaft";
  Modelica.Units.SI.Torque trq_inv(start = 1.0) "trq via shaft";

  Modelica.Units.SI.AngularVelocity omega(start = 1.0) "mechanical rotation speed, rad/sec";
  Modelica.Units.SI.Angle phi(start = 0.0) "mechanical rotation displacement, rad";
  Modelica.Units.NonSI.AngularVelocity_rpm Nmech(start = NmechDes) "mechanical rotation speed, rpm";
  Real NqNdes(start = 1.0) "ratio of mech. rotational speed with respect to design pt. speed";
  //----- inner-connected variables -----
  //##### none #####
  //----- inner-outer-connected variables -----
  //##### none #####
  //********** Interfaces **********
  Modelica.Fluid.Interfaces.FluidPort_a port_1(redeclare package Medium = Medium, m_flow(min = if allowFlowReversal then -Constants.inf else 0.0, start = m_flow1_init), h_outflow.start = h1_init) "" annotation(
    Placement(visible = true, transformation(origin = {-100, 80}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {-100, 80}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Fluid.Interfaces.FluidPort_b port_2(redeclare package Medium = Medium, m_flow(max = if allowFlowReversal then +Constants.inf else 0.0, start = m_flow2_init), h_outflow.start = h2_init) "" annotation(
    Placement(visible = true, transformation(origin = {100, 80}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {100, 80}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Rotational.Interfaces.Flange_a flange_1 "" annotation(
    Placement(visible = true, transformation(origin = {-100, 0}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {-98, 0}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Rotational.Interfaces.Flange_b flange_2 "" annotation(
    Placement(visible = true, transformation(origin = {100, 0}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {100, 0}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
    Types.ElementBus elementBus1 annotation(
    Placement(visible = true, transformation(origin = {70, -90}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {70, -90}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  //********** Protected objects **********
protected
  parameter Boolean port_a_exposesState = false "= true if port_a exposes the state of a fluid volume";
  parameter Boolean port_b_exposesState = false "= true if port_b.p exposes the state of a fluid volume";
  parameter Boolean showDesignFlowDirection = false "= false to hide the arrow in the model icon";
  /********************************************************
      Model coding
    ********************************************************/
initial algorithm
//***** debug-print *****
/*
  // // Modelica.Utilities.Streams.print("\n");
  // // Modelica.Utilities.Streams.print("At initialization"+"\n");
  // // Modelica.Utilities.Streams.print(String(getInstanceName()) +"\n");
  // // Modelica.Utilities.Streams.print("fluid_1.state.p= "+String(fluid_1.state.p) +"\n");
  // // Modelica.Utilities.Streams.print("fluid_2.p= "+String(fluid_2.p) +"\n");
  */
algorithm
//***** debug-print *****
  /*
  // // Modelica.Utilities.Streams.print("time= " + String(time) + " [s]" + "\n");
  // // Modelica.Utilities.Streams.print(String(getInstanceName()) + "\n");
  // // Modelica.Utilities.Streams.print("fluid_1.state.p= " + String(fluid_1.state.p) + "\n");
  // // Modelica.Utilities.Streams.print("fluid_2.p= " + String(fluid_2.p) + "\n");
  */
  
  assert(fluid_1.p < 0.0, getInstanceName() + ", fluid_1.p got less than 0", AssertionLevel.warning);
  assert(fluid_1.T < 0.0, getInstanceName() + ", fluid_1.T got less than 0", AssertionLevel.warning);
  assert(fluid_1.h < 0.0, getInstanceName() + ", fluid_1.h got less than 0", AssertionLevel.warning);
  assert(fluid_1.state.p < 0.0, getInstanceName() + ", fluid_1.state.p got less than 0", AssertionLevel.warning);
  assert(fluid_1.state.T < 0.0, getInstanceName() + ", fluid_1.state.T got less than 0", AssertionLevel.warning);
//----------
  assert(fluid_2.p < 0.0, getInstanceName() + ", fluid_2.p got less than 0", AssertionLevel.warning);
  assert(fluid_2.T < 0.0, getInstanceName() + ", fluid_2.T got less than 0", AssertionLevel.warning);
  assert(fluid_2.h < 0.0, getInstanceName() + ", fluid_2.h got less than 0", AssertionLevel.warning);
  assert(fluid_2.state.p < 0.0, getInstanceName() + ", fluid_2.state.p got less than 0", AssertionLevel.warning);
  assert(fluid_2.state.T < 0.0, getInstanceName() + ", fluid_2.state.T got less than 0", AssertionLevel.warning);
equation
//********** Geometries **********
//##### none #####
//********** Connections, interface <-> internal variables **********
//-- fluidPort_1 --
  fluid_1.p = port_1.p;
  port_1.h_outflow = fluid_1.h;
  fluid_1.h = actualStream(port_1.h_outflow);
  fluid_1.Xi = actualStream(port_1.Xi_outflow);
//-- fluidPort_2 --
  fluid_2.p = port_2.p;
  fluid_2.h = actualStream(port_2.h_outflow);
  fluid_2.Xi = actualStream(port_2.Xi_outflow);
//-- shaft-front, flange_a --
  flange_1.phi = phi;
//-- shaft-front, flange_b --
  flange_2.phi = phi;
//********** Eqns describing physics **********
  NqNdes = Nmech / NmechDes;
//********** reinit invalid state variables **********
  // removed: reinit on fluid_X.p / fluid_X.state.p
  // OCT cannot select algebraic pressure as state
  

  pwr_inv= -1*pwr;
  trq_inv= -1*trq;
  
/********************************************************
  Graphics
********************************************************/
//##### none #####
end ElementFrame_2FluidPorts_2ShaftPorts;
