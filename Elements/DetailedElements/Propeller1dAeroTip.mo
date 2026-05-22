within PropulsionSystem.Elements.DetailedElements;

model Propeller1dAeroTip
  /********************************************************
          imports
      ********************************************************/
  import Modelica.Constants;
  import PropulsionSystem.Types.switches;
  /********************************************************
          Declaration
      ********************************************************/
  //********** Package **********
  replaceable package Medium = Modelica.Media.Interfaces.PartialMedium annotation(
    choicesAllMatching = true);
  //********** Type definitions, only valid in this class **********
  //##### none #####
  //********** Parameters **********
  parameter Modelica.Units.SI.Length rTip_1_def = 1.0 "tip radius of blade, LE" annotation(
    Dialog(group = "Geometry"));
  parameter Modelica.Units.SI.Length rHub_1_def = 0.2 "tip radius of blade, LE" annotation(
    Dialog(group = "Geometry"));
  parameter Modelica.Units.SI.Length rTip_2_def = 1.0 "tip radius of blade, TE" annotation(
    Dialog(group = "Geometry"));
  parameter Modelica.Units.SI.Length rHub_2_def = 0.2 "tip radius of blade, TE" annotation(
    Dialog(group = "Geometry"));
  parameter Modelica.Units.SI.Length lAxial_def = 0.1 "axial length of blade" annotation(
    Dialog(group = "Geometry"));
  parameter Modelica.Units.SI.Area Sblade_def = (rTip_1_def - rHub_1_def + rTip_2_def - rHub_2_def) * lAxial_def * 1 / 2 "surface area of single blade" annotation(
    Dialog(group = "Geometry"));
  parameter Real numBlade_def = 4 "number of blades" annotation(
    Dialog(group = "Geometry"));
  //--- inner-connected, to AirfoilSimple ---
  inner parameter Real ClmaxDes = 1.5 "" annotation(
    Dialog(group = "Characteristics, airfoil"));
  inner parameter Modelica.Units.SI.Angle alpha4Cl0des(displayUnit = "deg") = 0.0 "" annotation(
    Dialog(group = "Characteristics, airfoil"));
  inner parameter Modelica.Units.SI.Angle alpha4ClmaxDes(displayUnit = "deg") = 15.0 * Modelica.Constants.pi / 180 "" annotation(
    Dialog(group = "Characteristics, airfoil"));
  inner parameter Modelica.Units.SI.Angle alpha4ClminDes(displayUnit = "deg") = -15.0 * Modelica.Constants.pi / 180 "" annotation(
    Dialog(group = "Characteristics, airfoil"));
  inner parameter Real CdfDes = 0.01 "" annotation(
    Dialog(group = "Characteristics, airfoil"));
  inner parameter Real alpha_CdpMinDes(displayUnit = "deg") = 0.0 * Modelica.Constants.pi / 180 "" annotation(
    Dialog(group = "Characteristics, airfoil"));
  inner parameter Real kCdpDes = 0.2 "" annotation(
    Dialog(group = "Characteristics, airfoil"));
  inner parameter Real pwrCdpDes = 4.0 "" annotation(
    Dialog(group = "Characteristics, airfoil"));
  inner parameter Real kCdp_1_des = 0.5 "" annotation(
    Dialog(group = "Characteristics, airfoil"));
  inner parameter Real pwrCdp_1_des = 4.0 "" annotation(
    Dialog(group = "Characteristics, airfoil"));
  //********** Initialization Parameters **********
  //--- fluid_amb, port_1 ---
  parameter Modelica.Units.SI.MassFlowRate m_flow1_init(displayUnit = "kg/s") = 1.0 "" annotation(
    Dialog(tab = "Initialization", group = "fluid_amb"));
  parameter Modelica.Units.SI.Pressure pAmb_init(displayUnit = "Pa") = 101.3 * 1000 "" annotation(
    Dialog(tab = "Initialization", group = "fluid_amb"));
  parameter Modelica.Units.SI.Temperature Tamb_init(displayUnit = "K") = 288.15 "" annotation(
    Dialog(tab = "Initialization", group = "fluid_amb"));
  parameter Modelica.Units.SI.SpecificEnthalpy hAmb_init(displayUnit = "J/kg") = 1.004 * 1000 * 288.15 "" annotation(
    Dialog(tab = "Initialization", group = "fluid_amb"));
  //********** Internal variables **********
  Modelica.Units.SI.Length rMean "mean radius of blade";
  Modelica.Units.SI.Length rTip_1 "tip radius, LE";
  Modelica.Units.SI.Length rHub_1 "hub radius, LE";
  Modelica.Units.SI.Length rTip_2 "tip radius, TE";
  Modelica.Units.SI.Length rHub_2 "hub radius, TE";
  Modelica.Units.SI.Length diamDisk_1;
  Modelica.Units.SI.Length diamDisk_2;
  Modelica.Units.SI.Length diamEffTip_1;
  Modelica.Units.SI.Length rEffTip_1;
  Modelica.Units.SI.Length lAxial "axial length of blade";
  Modelica.Units.SI.Length height_1 "blade height, LE";
  Modelica.Units.SI.Length height_2 "blade height, TE";
  Modelica.Units.SI.Length hBlade "blade height, avg";
  Modelica.Units.SI.Area Sblade "surface area of single blade";
  Real AR "aspect ratio";
  Real BR_1 "boss ratio, leading";
  Real BR_2 "boss ratio, trailing edge";
  Real numBlade "num. of blades";
  Modelica.Units.SI.Area AmechAx_1 "";
  Modelica.Units.SI.Area AmechAbs_1 "";
  Modelica.Units.SI.Area AeffAx_1 "eff. rep. area, flow cross section, axial, LE, NOT mech area";
  Modelica.Units.SI.Area AeffAbs_1 "eff. rep. area, flow cross section, abs, LE, NOT mech area";
  Modelica.Units.SI.Velocity c1 "abs-V, LE";
  Modelica.Units.SI.Velocity cx1 "axial-V, LE";
  Modelica.Units.SI.Velocity cTheta1 "tangential component, abs-V, LE";
  Modelica.Units.SI.Velocity w1(start = 100.0) "rel-V, LE";
  Modelica.Units.SI.Velocity wTheta1 "tangential component, rel-V, LE";
  Modelica.Units.SI.Velocity c2 "abs-V, TE";
  Modelica.Units.SI.Velocity cx2(start = 100.0) "axial-V, TE";
  Modelica.Units.SI.Velocity cTheta2 "tangential component, abs-V, TE";
  Modelica.Units.SI.Velocity w2(start = 100.0) "rel-V, TE";
  Modelica.Units.SI.Velocity wTheta2 "tangential component, rel-V, TE";
  Modelica.Units.SI.Velocity Utip_1 "tangential velocity, tip, LE";
  Modelica.Units.SI.Velocity Utip_2 "tangential velocity, tip, TE";
  Modelica.Units.SI.Velocity Umean "tangential velocity, mean r";
  Modelica.Units.SI.Angle alpha1 "flow angle, abs, LE";
  Modelica.Units.SI.Angle beta1 "flow angle, rel, LE";
  Modelica.Units.SI.Angle phi1 "angle btwn rel-V and disk plane, LE";
  Modelica.Units.SI.Angle alpha2 "flow angle, abs, TE";
  Modelica.Units.SI.Angle beta2 "flow angle, rel, TE";
  Modelica.Units.SI.Angle phi2 "angle btwn rel-V and disk plane, TE";
  Modelica.Units.SI.Angle inci1 "incident angle(AoA for airfoil), LE";
  Modelica.Units.SI.Angle xi "angle of blade chord line";
  Modelica.Units.SI.Angle epsiron2 "downwash angle, TE";
  Modelica.Units.SI.MassFlowRate m_flow_single(min = 0.0, start = m_flow1_init / numBlade_def) "m_flow, single blade";
  Modelica.Units.SI.MassFlowRate m_flow(min = 0.0, start = m_flow1_init) "m_flow, entire disk";
  Real CL(start = 1.0) "lift coefficient";
  Real CD(start = 0.01) "drag coefficient";
  Modelica.Units.SI.Force FthetaSingle "aero-force, tangential direction, single blade";
  Modelica.Units.SI.Force FaxSingle "aero-force, axial direction, single blade";
  Modelica.Units.SI.Force FliftSingle "lift, single blade";
  Modelica.Units.SI.Force FdragSingle "drag, single blade";
  Modelica.Units.SI.Force FresultantSingle "resultant force, single blade";
  Modelica.Units.SI.Force Ftheta "aero-force, tangential direction, total of blades";
  Modelica.Units.SI.Force Fax "aero-force, axial direction, total of blades";
  Modelica.Units.SI.Force Flift "lift, total of blades";
  Modelica.Units.SI.Force Fdrag "drag, total of blades";
  Modelica.Units.SI.Force Fresultant "resulttant force, total of blades";
  Modelica.Units.SI.Torque trqSingle "torque, by single blade";
  Modelica.Units.SI.Power pwrSingle "power, by single blade";
  Modelica.Units.SI.Power pwrPropulsive "power of propulsion, =thrust*flowSpeed";
  Real FliftqFdrag "lift/drag of mean line blade";
  Real FaxqFtheta "axial-force/tangential force";
  Real effPropeller "propeller efficiency, =pwrPropulsive/pwr";
  Modelica.Units.SI.SpecificEnthalpy dht "rise in specific enthalpy across rotor";
  Real aeroLoading "dht/U^2";
  Real ratioAdv "propeller advance ratio";
  Real cThrust "";
  Real cTorque "";
  Real cPower "";
  Modelica.Units.SI.SpecificEnthalpy h_1 "enthalpy, total state";
  Modelica.Units.SI.SpecificEnthalpy h_1rel "enthalpy, total state, relative";
  Modelica.Units.SI.SpecificEnthalpy h_2 "enthalpy, total state";
  Modelica.Units.SI.SpecificEnthalpy h_2rel "enthalpy, total state, relative";
  Modelica.Units.SI.SpecificEnthalpy h_1stat(start = hAmb_init) "enthalpy, static state";
  Modelica.Units.SI.SpecificEnthalpy h_2stat(start = hAmb_init) "enthalpy, static state";
  Modelica.Units.SI.Power pwr(start = 100) "power via shaft, positive if fluid generates power";
  Modelica.Units.SI.Torque trq(start = 1.0) "trq via shaft";
  Modelica.Units.SI.AngularVelocity omega(start = 100.0) "mechanical rotation speed, rad/sec";
  Modelica.Units.SI.Angle phi(start = 0.0) "mechanical rotation displacement, rad";
  Modelica.Units.NonSI.AngularVelocity_rpm Nmech(start = 1000) "mechanical rotation speed, rpm";
  Boolean flagBladeStall(start = false) "flag, prop. blade is stalled or not";
  Modelica.Units.SI.SpecificEnthalpy rothalpy1 "";
  Modelica.Units.SI.SpecificEnthalpy rothalpy2 "";
  //Modelica.Units.SI.Pressure p1rel "";
  //Modelica.Units.SI.Pressure p2rel "";
  //Modelica.Units.SI.Pressure dpLoss "";
  //********** Interfaces **********
  Modelica.Blocks.Interfaces.RealInput u_flowSpeed "" annotation(
    Placement(visible = true, transformation(origin = {-120, 20}, extent = {{-20, -20}, {20, 20}}, rotation = 0), iconTransformation(origin = {-110, 30}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Blocks.Interfaces.RealInput u_flowAngle "incoming flow swirl angle" annotation(
    Placement(visible = true, transformation(origin = {-120, 50}, extent = {{-20, -20}, {20, 20}}, rotation = 0), iconTransformation(origin = {-110, 60}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Blocks.Interfaces.RealInput u_bladeAngle "0 deg: chord alines with center line, 90 deg: chord alines with disk plane" annotation(
    Placement(visible = true, transformation(origin = {-30, 120}, extent = {{-20, -20}, {20, 20}}, rotation = -90), iconTransformation(origin = {50, 110}, extent = {{-10, -10}, {10, 10}}, rotation = -90)));
  Modelica.Blocks.Interfaces.RealOutput y_Fg "thrust by propeller" annotation(
    Placement(visible = true, transformation(origin = {110, -50}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {110, -50}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Fluid.Interfaces.FluidPort_a port_amb(redeclare package Medium = Medium, h_outflow.start = hAmb_init) "" annotation(
    Placement(visible = true, transformation(origin = {-100, 80}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {-100, 80}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Rotational.Interfaces.Flange_a flange_1 "" annotation(
    Placement(visible = true, transformation(origin = {-100, 0}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {-98, 0}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Mechanics.Rotational.Interfaces.Flange_b flange_2 "" annotation(
    Placement(visible = true, transformation(origin = {100, 0}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {100, 0}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Blocks.Interfaces.RealOutput y_flowAngle "outgoing flow swirl angle" annotation(
    Placement(visible = true, transformation(origin = {110, 50}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {110, 60}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Blocks.Interfaces.RealOutput y_flowSpeed annotation(
    Placement(visible = true, transformation(origin = {110, 20}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {110, 30}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Types.ElementBus elementBus1 annotation(
    Placement(visible = true, transformation(origin = {70, -90}, extent = {{-10, -10}, {10, 10}}, rotation = 0), iconTransformation(origin = {70, -90}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  //********** internal objects **********
  Medium.BaseProperties fluid_amb(p.start = pAmb_init, T.start = Tamb_init, state.p.start = pAmb_init, state.T.start = Tamb_init, h.start = hAmb_init) "flow station of inlet";
  AircraftDynamics.Aerodynamics.BaseClasses.AirfoilSimple00 airfoilSimple001 annotation(
    Placement(visible = true, transformation(origin = {-30.25, 40.2}, extent = {{-49.75, -39.8}, {49.75, 39.8}}, rotation = 0)));
initial algorithm
// NONE
algorithm
//********** Geometries, defined by parameter **********
  rTip_1 := rTip_1_def;
  rHub_1 := rHub_1_def;
  rTip_2 := rTip_2_def;
  rHub_2 := rHub_2_def;
  lAxial := lAxial_def;
  Sblade := Sblade_def;
  numBlade := numBlade_def;
//********** interface, input **********
  alpha1 := u_flowAngle;
  xi := u_bladeAngle;
  c1 := u_flowSpeed;
//********** geometry **********
  rMean := (rTip_1 + rHub_1 + rTip_2 + rHub_2) / 4.0;
  BR_1 := rHub_1 / rTip_1;
  BR_2 := rHub_2 / rTip_2;
  height_1 := rTip_1 - rHub_1;
  height_2 := rTip_2 - rHub_2;
  hBlade := (height_1 + height_2) / 2;
  AR := 2 * hBlade / lAxial;
  diamDisk_1 := 2 * rTip_1;
  diamDisk_2 := 2 * rTip_2;
  AmechAx_1 := Modelica.Constants.pi * (rTip_1 ^ 2.0 - rHub_1 ^ 2.0);
  AmechAbs_1 := AmechAx_1 / cos(alpha1);
//********** velocities **********
  Umean := rMean * omega;
  Utip_1 := rTip_1 * omega;
  Utip_2 := rTip_2 * omega;
  cx1 := cos(alpha1) * c1;
  cTheta1 := sqrt(c1 ^ 2.0 - cx1 ^ 2.0);
  wTheta1 := Utip_1 - cTheta1;
  w1 := sqrt(cx1 ^ 2.0 + wTheta1 ^ 2.0);
  beta1 := acos(cx1 / w1);
  inci1 := beta1 - xi;
  phi1 := Modelica.Constants.pi / 2.0 - beta1;
//********** Forces **********
  FliftSingle := CL * Sblade * 1.0 / 2.0 * fluid_amb.d * w1 ^ 2.0;
  FdragSingle := CD * Sblade * 1.0 / 2.0 * fluid_amb.d * w1 ^ 2.0;
  FthetaSingle := FliftSingle * sin(phi1) + FdragSingle * cos(phi1);
  FaxSingle := FliftSingle * cos(phi1) - FdragSingle * sin(phi1);
  FresultantSingle := sign(FliftSingle) * sqrt(FliftSingle ^ 2.0 + FdragSingle ^ 2.0);
  Flift := FliftSingle * numBlade;
  Fdrag := FdragSingle * numBlade;
  Ftheta := FthetaSingle * numBlade;
  Fax := FaxSingle * numBlade;
  Fresultant := FresultantSingle * numBlade;
//********** velocities **********
  wTheta2 := Utip_1 - cTheta2;
  w2 := sqrt(cx2 ^ 2.0 + wTheta2 ^ 2.0);
  beta2 := atan(wTheta2 / cx2);
  c2 := sqrt(cx2 ^ 2.0 + cTheta2 ^ 2.0);
  alpha2 := acos(cx2 / c2);
  phi2 := Modelica.Constants.pi / 2.0 - beta2;
  epsiron2 := beta1 - beta2;
//********** energy and momentum **********
  trq := m_flow * (rTip_2 * cTheta2 - rTip_1 * cTheta1);
// euler equation
  trqSingle := trq / numBlade;
  pwrSingle := trqSingle * omega;
  pwr := pwrSingle * numBlade;
//dpLoss:= Fdrag/(AmechAx_1*cos(beta1));
//h_1 := fluid_amb.h + 1.0 / 2.0 * c1 ^ 2.0;
  h_1 := h_1stat + 1.0 / 2.0 * c1 ^ 2.0;
  h_1rel := h_1stat + 1.0 / 2.0 * w1 ^ 2.0;
  rothalpy1 := h_1 - Utip_1 * cTheta1;
  rothalpy2 := rothalpy1;
  h_2 := rothalpy2 + Utip_2 * cTheta2;
  h_2stat := h_2 - 1.0 / 2.0 * c2 ^ 2.0;
  h_2rel := h_2stat + 1.0 / 2.0 * w2 ^ 2.0;
//h_2 := fluid_amb.h + 1.0 / 2.0 * c2 ^ 2;
  dht := h_2 - h_1;
//********** component characteristics, etc **********
  pwrPropulsive := Fax * c1;
  Nmech := Modelica.Units.NonSI.to_rpm(omega);
  FliftqFdrag := Flift / Fdrag;
  FaxqFtheta := Fax / Ftheta;
  effPropeller := pwrPropulsive / pwr;
  if Utip_1 <> 0.0 then
    aeroLoading := dht / Utip_1 ^ 2.0;
  else
    aeroLoading := 0.0;
  end if;
  ratioAdv := cx1 / (diamDisk_1 * (Nmech / 60.0));
  cThrust := Fax / (fluid_amb.d * (Nmech / 60.0) ^ 2.0 * diamDisk_1 ^ 4.0);
  cTorque := trq / (fluid_amb.d * (Nmech / 60.0) ^ 2.0 * diamDisk_1 ^ 5.0);
  cPower := 2.0 * Modelica.Constants.pi * cTorque;
//********** interface, output **********
  y_Fg := Fax;
  y_flowAngle := alpha2;
  y_flowSpeed := c2;
initial equation
// NONE
equation
//********** reinit invalid state variables **********
  when m_flow < 0.0 then
    reinit(m_flow, -1.0 * m_flow);
  end when;
//********** interface **********
//-- fluidPort_1 --
  fluid_amb.p = port_amb.p;
  port_amb.h_outflow = fluid_amb.h;
  fluid_amb.h = actualStream(port_amb.h_outflow);
  fluid_amb.Xi = actualStream(port_amb.Xi_outflow);
  port_amb.m_flow = 1;
  h_1stat = fluid_amb.h;
//p1=fluid_amb.p;
//-- shaft-front, flange_a --
  flange_1.phi = phi;
//-- shaft-front, flange_b --
  flange_2.phi = phi;
//-- internal components --
  connect(inci1, airfoilSimple001.signalBus1.alpha) annotation(
    Line);
  CL = airfoilSimple001.signalBus2.Cl;
//CD = airfoilSimple001.signalBus2.Cd;
  CD = airfoilSimple001.signalBus2.Cd;
//********** physical equations **********
//-- energy conservation --
  trq = flange_1.tau + flange_2.tau;
  der(phi) = omega;
//pwr= m_flow*(1.0/2.0*sign(c2)*c2^2.0 - 1.0/2.0*sign(c1)*c1^2.0);
  pwr = m_flow * (h_2 - h_1);
//----- momentum conservation -----
  Fax = 1.0 * m_flow * (cx2 - cx1);
//cx2=cx1;
  Ftheta = 1.0 * m_flow * (cTheta2 - cTheta1);
  m_flow = m_flow_single * numBlade;
//-----  component characteristics, etc -----
  if c1 == 0 then
    AeffAbs_1 = 0.0;
  else
    AeffAbs_1 * (fluid_amb.d * c1) = m_flow;
  end if;
  AeffAx_1 = AeffAbs_1 * cos(alpha1);
  AeffAx_1 = Modelica.Constants.pi / 4.0 * (diamEffTip_1 ^ 2.0 - (2.0 * rHub_1) ^ 2.0);
  rEffTip_1 = diamEffTip_1 / 2.0;
//********** flag variables **********
  if alpha4ClmaxDes < airfoilSimple001.signalBus1.alpha then
    flagBladeStall = true;
  elseif airfoilSimple001.signalBus1.alpha < alpha4ClminDes then
    flagBladeStall = true;
  else
    flagBladeStall = false;
  end if;
  annotation(
    Icon(graphics = {Rectangle(origin = {40, -4}, fillPattern = FillPattern.Solid, extent = {{-66, 10}, {52, -2}}), Polygon(origin = {-13, 46}, fillColor = {0, 0, 127}, fillPattern = FillPattern.Solid, points = {{-3, 54}, {-7, -40}, {13, -40}, {9, 54}, {-3, 54}}), Line(origin = {-39.77, -9.94}, points = {{26, 10}, {-60, 10}}, pattern = LinePattern.Dot, thickness = 1.5), Line(origin = {98.77, -10.2247}, points = {{0, 10}, {-104, 10}}, pattern = LinePattern.Dot, thickness = 1.5), Polygon(origin = {-13, -58}, fillColor = {0, 0, 127}, fillPattern = FillPattern.Solid, points = {{-7, 52}, {-3, -42}, {9, -42}, {13, 52}, {-7, 52}}), Ellipse(origin = {-22, 20}, pattern = LinePattern.DashDot, lineThickness = 0.5, extent = {{-28, 80}, {42, -120}}, endAngle = 360), Line(origin = {45.8, 56.5356}, points = {{4.1963, 45.1963}, {4.1963, -34.8037}, {-45.8036, -50.8037}}, pattern = LinePattern.Dash, thickness = 1.5), Text(origin = {-70, 92}, extent = {{-20, 8}, {20, -12}}, textString = "Amb"), Text(origin = {74, 97}, extent = {{-14, 3}, {16, -17}}, textString = "pitch")}, coordinateSystem(initialScale = 0.1)),
    __OpenModelica_commandLineOptions = "");
end Propeller1dAeroTip;
