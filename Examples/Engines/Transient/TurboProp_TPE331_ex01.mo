within PropulsionSystem.Examples.Engines.Transient;

model TurboProp_TPE331_ex01
  "TPE331-like twin-spool turboprop transient simulation (no propeller — variable load torque on PT shaft)"
  extends Modelica.Icons.Example;
  //-----
  package engineAir = PropulsionSystem.Media.EngineBreathingAir.DryAirMethaneMixture00;
  //-----
  inner Modelica.Fluid.System system annotation(
    Placement(visible = true, transformation(origin = {-70, 90}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  inner PropulsionSystem.EngineSimEnvironment environment annotation(
    Placement(visible = true, transformation(origin = {-90, 90}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  //========================================================================
  //  Flight condition & Inlet
  //========================================================================
  PropulsionSystem.Sources.FlightCondition2InletFluid00 Flt2Fluid(
    redeclare package Medium = engineAir,
    printCmd = false) annotation(
    Placement(visible = true, transformation(origin = {-180, -60}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
  PropulsionSystem.Elements.BasicElements.InltCharFixed00 Inlt(
    redeclare package Medium = engineAir) annotation(
    Placement(visible = true, transformation(origin = {-120, -80}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
  //========================================================================
  //  Compressor (TPE331 scaled map)
  //========================================================================
  PropulsionSystem.Elements.BasicElements.CmpCharTable00 Cmp(
    redeclare package Medium = engineAir,
    NmechDes_paramInput = 41730.0,
    PRdes_paramInput = 10.0,
    effDes_paramInput = 0.82,
    m_flow_1_des_paramInput = 8.0,
    p1_des_paramInput = 101325.0,
    T1_des_paramInput = 288.15,
    NcTblDes_paramInput = 0.95,
    RlineTblDes_paramInput = 0.52632,
    use_tableFile_Wc = true,
    use_tableFile_PR = true,
    use_tableFile_eff = true,
    pathName_tableFileInSimExeDir = "./tableData/table_Compressor_WcPReff_NcRline_TPE331.txt",
    pathName_tableFileInLibPackage = "modelica://PropulsionSystem/tableData/table_Compressor_WcPReff_NcRline_TPE331.txt",
    printCmd = false) annotation(
    Placement(visible = true, transformation(origin = {-60, -80}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
  //========================================================================
  //  Combustor
  //========================================================================
  PropulsionSystem.Elements.BasicElements.CombCharFixed02 Comb(
    redeclare package Medium = engineAir) annotation(
    Placement(visible = true, transformation(origin = {20, -40}, extent = {{-20, -16}, {20, 16}}, rotation = 0)));
  PropulsionSystem.Sources.MassFlowSource_T FuelSrc(
    redeclare package Medium = engineAir,
    T = 400,
    X = {1, 0, 0},
    nPorts = 1,
    use_T_in = false,
    use_m_flow_in = true) annotation(
    Placement(visible = true, transformation(origin = {-20, -10}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  //========================================================================
  //  Gas Generator Turbine (GGT) — same shaft as compressor
  //========================================================================
  PropulsionSystem.Elements.BasicElements.TrbCharTable00 GGT(
    redeclare package Medium = engineAir,
    NmechDes_paramInput = 41730.0,
    PRdes_paramInput = 3.2,
    effDes_paramInput = 0.86,
    T1_des_paramInput = 1200.0,
    m_flow_1_des_paramInput = 8.2,
    p1_des_paramInput = 900000.0,
    NcTblDes_paramInput = 1.0,
    PRtblDes_paramInput = 3.327,
    use_tableFile_Wc = true,
    use_tableFile_eff = true,
    pathName_tableFileInSimExeDir = "./tableData/table_Turbine_WcEff_NcPR_TPE331_GGT.txt",
    pathName_tableFileInLibPackage = "modelica://PropulsionSystem/tableData/table_Turbine_WcEff_NcPR_TPE331_GGT.txt",
    printCmd = false) annotation(
    Placement(visible = true, transformation(origin = {100, -80}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
  //========================================================================
  //  Free Power Turbine (FPT) — separate shaft with load
  //========================================================================
  PropulsionSystem.Elements.BasicElements.TrbCharTable00 FPT(
    redeclare package Medium = engineAir,
    NmechDes_paramInput = 30000.0,
    PRdes_paramInput = 1.8,
    effDes_paramInput = 0.88,
    T1_des_paramInput = 1000.0,
    m_flow_1_des_paramInput = 8.2,
    p1_des_paramInput = 200000.0,
    NcTblDes_paramInput = 1.0,
    PRtblDes_paramInput = 1.5813,
    use_tableFile_Wc = true,
    use_tableFile_eff = true,
    pathName_tableFileInSimExeDir = "./tableData/table_Turbine_WcEff_NcPR_TPE331_FPT.txt",
    pathName_tableFileInLibPackage = "modelica://PropulsionSystem/tableData/table_Turbine_WcEff_NcPR_TPE331_FPT.txt",
    printCmd = false) annotation(
    Placement(visible = true, transformation(origin = {200, -80}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
  //========================================================================
  //  Exhaust nozzle
  //========================================================================
  PropulsionSystem.Elements.BasicElements.NzlDefAeByFlowCharFixed00 Nzl(
    redeclare package Medium = engineAir,
    m_flow_1_des_paramInput = 8.2,
    printCmd = false) annotation(
    Placement(visible = true, transformation(origin = {260, -80}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
  //========================================================================
  //  Shaft dynamics
  //========================================================================
  // Gas Generator shaft (Cmp ←→ GGT)
  Modelica.Mechanics.Rotational.Components.Inertia ShaftGG(
    J = 0.5,
    phi(fixed = true, start = 0),
    w(fixed = true, start = 41730.0 * 2 * Modelica.Constants.pi / 60)) annotation(
    Placement(visible = true, transformation(origin = {20, -80}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  // Power Turbine shaft (FPT + load)
  Modelica.Mechanics.Rotational.Components.Inertia ShaftPT(
    J = 1.0,
    phi(fixed = true, start = 0),
    w(fixed = true, start = 30000.0 * 2 * Modelica.Constants.pi / 60)) annotation(
    Placement(visible = true, transformation(origin = {200, -140}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  //========================================================================
  //  Variable load on PT shaft (simulates propeller or generator)
  //========================================================================
  Modelica.Mechanics.Rotational.Sources.Torque loadTorque annotation(
    Placement(visible = true, transformation(origin = {260, -140}, extent = {{10, -10}, {-10, 10}}, rotation = 0)));
  Modelica.Blocks.Sources.Ramp ramp_loadTorque(
    height = -500,
    duration = 5,
    offset = -200,
    startTime = 20) "Negative = resistive torque (load increasing from 200 to 700 N.m)" annotation(
    Placement(visible = true, transformation(origin = {300, -140}, extent = {{10, -10}, {-10, 10}}, rotation = 0)));
  //========================================================================
  //  Fuel flow command
  //========================================================================
  Modelica.Blocks.Sources.Ramp ramp_m_flow_fuel(
    height = 0.02,
    duration = 5,
    offset = 0.15,
    startTime = 10) "Fuel flow ramp: 0.15 → 0.17 kg/s" annotation(
    Placement(visible = true, transformation(origin = {-60, 20}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  //========================================================================
  //  Sensors
  //========================================================================
  Modelica.Fluid.Sensors.Temperature T4_sensor(
    redeclare package Medium = engineAir) "Turbine inlet temperature" annotation(
    Placement(visible = true, transformation(origin = {60, -30}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  //========================================================================
  //  Performance block
  //========================================================================
  PropulsionSystem.Elements.BasicElements.EnginePerformance00 Perf annotation(
    Placement(visible = true, transformation(origin = {300, -200}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
equation
  //--- Fuel command → fuel source ---
  connect(ramp_m_flow_fuel.y, FuelSrc.m_flow_in) annotation(
    Line(points = {{-49, 20}, {-40, 20}, {-40, -2}, {-30, -2}}, color = {0, 0, 127}));
  //--- Flight condition → Inlet ---
  connect(Flt2Fluid.port_inlet, Inlt.port_1) annotation(
    Line(points = {{-160, -64}, {-140, -64}}, color = {0, 127, 255}));
  connect(Flt2Fluid.y_V_inf, Inlt.u_V_infini) annotation(
    Line(points = {{-158, -76}, {-150, -76}, {-150, -88}, {-134, -88}}, color = {0, 0, 127}));
  //--- Inlet → Compressor ---
  connect(Inlt.port_2, Cmp.port_1) annotation(
    Line(points = {{-100, -64}, {-80, -64}}, color = {0, 127, 255}));
  //--- Compressor → Combustor ---
  connect(Cmp.port_2, Comb.port_1) annotation(
    Line(points = {{-40, -64}, {-40, -40}, {0, -40}}, color = {0, 127, 255}));
  //--- Fuel → Combustor ---
  connect(FuelSrc.ports[1], Comb.port_fuel) annotation(
    Line(points = {{-10, -10}, {4, -10}, {4, -24}}, color = {0, 127, 255}));
  //--- Combustor → TIT sensor → GGT ---
  connect(Comb.port_2, T4_sensor.port) annotation(
    Line(points = {{40, -40}, {60, -40}}, color = {0, 127, 255}));
  connect(T4_sensor.port, GGT.port_1) annotation(
    Line(points = {{60, -40}, {80, -40}, {80, -64}}, color = {0, 127, 255}));
  //--- GGT → FPT ---
  connect(GGT.port_2, FPT.port_1) annotation(
    Line(points = {{120, -64}, {180, -64}}, color = {0, 127, 255}));
  //--- FPT → Nozzle ---
  connect(FPT.port_2, Nzl.port_1) annotation(
    Line(points = {{220, -64}, {240, -64}}, color = {0, 127, 255}));
  //--- Nozzle exhaust → ambient ---
  connect(Flt2Fluid.port_amb, Nzl.port_2) annotation(
    Line(points = {{-180, -40}, {-180, 60}, {280, 60}, {280, -64}}, color = {0, 127, 255}));
  //--- GG Shaft: Cmp ←→ GGT ---
  connect(Cmp.flange_2, ShaftGG.flange_a) annotation(
    Line(points = {{-40, -80}, {10, -80}}));
  connect(ShaftGG.flange_b, GGT.flange_1) annotation(
    Line(points = {{30, -80}, {80, -80}}));
  //--- PT Shaft: FPT ←→ load ---
  connect(FPT.flange_1, ShaftPT.flange_a) annotation(
    Line(points = {{180, -80}, {170, -80}, {170, -140}, {190, -140}}));
  connect(ShaftPT.flange_b, loadTorque.flange) annotation(
    Line(points = {{210, -140}, {250, -140}}));
  connect(ramp_loadTorque.y, loadTorque.tau) annotation(
    Line(points = {{289, -140}, {272, -140}}, color = {0, 0, 127}));
  //--- Performance monitoring ---
  connect(Inlt.y_FdRam, Perf.u_Fram) annotation(
    Line(points = {{-106, -88}, {-96, -88}, {-96, -192}, {278, -192}}, color = {0, 0, 127}));
  connect(Nzl.y_Fg, Perf.u_Fg) annotation(
    Line(points = {{270, -80}, {270, -184}, {278, -184}}, color = {0, 0, 127}));
  connect(Comb.y_m_flow_fuel, Perf.u_m_flow_fuel) annotation(
    Line(points = {{36, -58}, {36, -216}, {278, -216}}, color = {0, 0, 127}));
  annotation(
    experiment(StartTime = 0, StopTime = 60, Tolerance = 1e-06, Interval = 0.02),
    Diagram(coordinateSystem(extent = {{-220, -240}, {340, 100}})),
    Documentation(info = "<html>
<h4>TPE331-like Turboprop Transient Simulation</h4>
<p>Twin-spool configuration without propeller model:</p>
<ul>
<li>Gas Generator: Compressor + GGT on shared shaft (41730 rpm design)</li>
<li>Free Power Turbine: separate shaft (30000 rpm design) with variable torque load</li>
<li>Input: fuel flow ramp (simulates throttle command)</li>
<li>Load: resistive torque ramp on PT shaft (simulates propeller or generator)</li>
</ul>
<p>Table data: TPE331-scaled maps exported from XML via turbomap_data_utils.</p>
</html>"));
end TurboProp_TPE331_ex01;
