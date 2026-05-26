within PropulsionSystem.Examples.Engines.Transient;

model TurboProp_TPE331_ex01a
  "TPE331 Gas Generator only (single-spool turbojet config) — map scaling verification"
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
  //  Gas Generator Turbine (GGT) — drives compressor
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
  //  Exhaust nozzle (directly after GGT — no FPT)
  //========================================================================
  PropulsionSystem.Elements.BasicElements.NzlDefAeByFlowCharFixed00 Nzl(
    redeclare package Medium = engineAir,
    m_flow_1_des_paramInput = 8.2,
    printCmd = false) annotation(
    Placement(visible = true, transformation(origin = {180, -80}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
  //========================================================================
  //  GG Shaft (single spool: Cmp + GGT)
  //========================================================================
  Modelica.Mechanics.Rotational.Components.Inertia ShaftGG(
    J = 0.5,
    phi(fixed = true, start = 0),
    w(fixed = true, start = 41730.0 * 2 * Modelica.Constants.pi / 60)) annotation(
    Placement(visible = true, transformation(origin = {20, -80}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  //========================================================================
  //  Fuel flow command (constant then ramp)
  //========================================================================
  Modelica.Blocks.Sources.Ramp ramp_m_flow_fuel(
    height = 0.02,
    duration = 5,
    offset = 0.15,
    startTime = 10) "Fuel flow ramp: 0.15 -> 0.17 kg/s" annotation(
    Placement(visible = true, transformation(origin = {-60, 20}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  //========================================================================
  //  Sensors
  //========================================================================
  Modelica.Fluid.Sensors.Temperature T4_sensor(
    redeclare package Medium = engineAir) "Turbine inlet temperature" annotation(
    Placement(visible = true, transformation(origin = {60, -30}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
equation
  //--- Fuel command ---
  connect(ramp_m_flow_fuel.y, FuelSrc.m_flow_in) annotation(
    Line(points = {{-49, 20}, {-40, 20}, {-40, -2}, {-30, -2}}, color = {0, 0, 127}));
  //--- Flight condition -> Inlet ---
  connect(Flt2Fluid.port_inlet, Inlt.port_1) annotation(
    Line(points = {{-160, -64}, {-140, -64}}, color = {0, 127, 255}));
  connect(Flt2Fluid.y_V_inf, Inlt.u_V_infini) annotation(
    Line(points = {{-158, -76}, {-150, -76}, {-150, -88}, {-134, -88}}, color = {0, 0, 127}));
  //--- Inlet -> Compressor ---
  connect(Inlt.port_2, Cmp.port_1) annotation(
    Line(points = {{-100, -64}, {-80, -64}}, color = {0, 127, 255}));
  //--- Compressor -> Combustor ---
  connect(Cmp.port_2, Comb.port_1) annotation(
    Line(points = {{-40, -64}, {-40, -40}, {0, -40}}, color = {0, 127, 255}));
  //--- Fuel -> Combustor ---
  connect(FuelSrc.ports[1], Comb.port_fuel) annotation(
    Line(points = {{-10, -10}, {4, -10}, {4, -24}}, color = {0, 127, 255}));
  //--- Combustor -> TIT sensor -> GGT ---
  connect(Comb.port_2, T4_sensor.port) annotation(
    Line(points = {{40, -40}, {60, -40}}, color = {0, 127, 255}));
  connect(T4_sensor.port, GGT.port_1) annotation(
    Line(points = {{60, -40}, {80, -40}, {80, -64}}, color = {0, 127, 255}));
  //--- GGT -> Nozzle (direct, no FPT) ---
  connect(GGT.port_2, Nzl.port_1) annotation(
    Line(points = {{120, -64}, {160, -64}}, color = {0, 127, 255}));
  //--- Nozzle exhaust -> ambient ---
  connect(Flt2Fluid.port_amb, Nzl.port_2) annotation(
    Line(points = {{-180, -40}, {-180, 60}, {200, 60}, {200, -64}}, color = {0, 127, 255}));
  //--- GG Shaft: Cmp <-> GGT ---
  connect(Cmp.flange_2, ShaftGG.flange_a) annotation(
    Line(points = {{-40, -80}, {10, -80}}));
  connect(ShaftGG.flange_b, GGT.flange_1) annotation(
    Line(points = {{30, -80}, {80, -80}}));
  annotation(
    experiment(StartTime = 0, StopTime = 30, Tolerance = 1e-06, Interval = 0.02),
    Diagram(coordinateSystem(extent = {{-220, -120}, {220, 100}})),
    Documentation(info = "<html>
<h4>TPE331 Gas Generator — Single Spool (Turbojet Config)</h4>
<p>Purpose: Verify map scaling and thermodynamic cycle balance without FPT complexity.</p>
<ul>
<li>Single spool: Compressor + GGT on shared shaft with inertia (J=0.5 kg.m2)</li>
<li>GGT exhaust goes directly to convergent nozzle</li>
<li>Input: fuel flow ramp (0.15 -> 0.17 kg/s at t=10s)</li>
<li>Observe: shaft speed response, TIT, compressor PR</li>
</ul>
<p>If this initializes and runs, the GG maps are verified. Next step: add FPT (ex01b).</p>
</html>"));
end TurboProp_TPE331_ex01a;
