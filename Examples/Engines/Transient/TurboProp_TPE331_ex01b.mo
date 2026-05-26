within PropulsionSystem.Examples.Engines.Transient;

model TurboProp_TPE331_ex01b
  "TPE331 single-shaft turboprop: Cmp+Trb on one shaft with propeller load (gear-referred torque)"
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
    alt_paramInput = 0.0,
    MN_paramInput = 0.0,
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
  //  Turbine (single, 3-stage axial) — PR=8, eff=0.87
  //  Full expansion in single-shaft TPE331
  //========================================================================
  PropulsionSystem.Elements.BasicElements.TrbCharFixed00 Trb(
    redeclare package Medium = engineAir,
    switchDetermine_PR = PropulsionSystem.Types.switches.switchHowToDetVar.param,
    PRdes_paramInput = 8.0,
    effDes_paramInput = 0.87) annotation(
    Placement(visible = true, transformation(origin = {100, -80}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
  //========================================================================
  //  Exhaust nozzle
  //  NOTE: Turboprop exhaust is low-velocity subsonic (most energy to shaft).
  //  Nozzle area heuristic (0.0014*m_flow) is for turbojet-like choked nozzle.
  //  For turboprop, set m_flow_1_des large to ensure non-restrictive exhaust.
  //  A = 0.0014*50 ≈ 0.07 m² → passes 8+ kg/s subsonic at PR_nzl≈1.2
  //========================================================================
  PropulsionSystem.Elements.BasicElements.NzlDefAeByFlowCharFixed00 Nzl(
    redeclare package Medium = engineAir,
    m_flow_1_des_paramInput = 50.0,
    printCmd = false) annotation(
    Placement(visible = true, transformation(origin = {180, -80}, extent = {{-20, -20}, {20, 20}}, rotation = 0)));
  //========================================================================
  //  Single Shaft (Cmp + Trb + PropLoad)
  //========================================================================
  Modelica.Mechanics.Rotational.Components.Inertia Shaft(
    J = 0.5,
    phi(fixed = true, start = 0),
    w(fixed = true, start = 25000.0 * 2 * Modelica.Constants.pi / 60)) "Start at 25000 rpm (Nc=0.60), accelerate to design" annotation(
    Placement(visible = true, transformation(origin = {20, -80}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  //========================================================================
  //  Propeller load (referred to turbine shaft via gear ratio)
  //
  //  TPE331 reduction gear: GR = 20.87, eta_gear = 0.98
  //  Q_turbine = Q_prop / (GR * eta_gear)
  //  Idle: 23 N.m | Cruise: 114 N.m | Max T/O: 163 N.m
  //========================================================================
  Modelica.Mechanics.Rotational.Sources.Torque PropLoad annotation(
    Placement(visible = true, transformation(origin = {20, -120}, extent = {{-10, -10}, {10, 10}}, rotation = 90)));
  Modelica.Blocks.Sources.Ramp ramp_PropTorque(
    height = -120,
    duration = 10,
    offset = -10,
    startTime = 30) "PropLoad: -10 (start) -> -130 N.m (cruise) after shaft reaches design" annotation(
    Placement(visible = true, transformation(origin = {-20, -140}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  //========================================================================
  //  Fuel flow command (constant then ramp)
  //========================================================================
  Modelica.Blocks.Sources.Ramp ramp_m_flow_fuel(
    height = 0.045,
    duration = 25,
    offset = 0.020,
    startTime = 2) "Fuel: 0.020 -> 0.065 kg/s over 25s (start-up acceleration)" annotation(
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
  //--- Combustor -> TIT sensor -> Turbine ---
  connect(Comb.port_2, T4_sensor.port) annotation(
    Line(points = {{40, -40}, {60, -40}}, color = {0, 127, 255}));
  connect(T4_sensor.port, Trb.port_1) annotation(
    Line(points = {{60, -40}, {80, -40}, {80, -64}}, color = {0, 127, 255}));
  //--- Turbine -> Nozzle ---
  connect(Trb.port_2, Nzl.port_1) annotation(
    Line(points = {{120, -64}, {160, -64}}, color = {0, 127, 255}));
  //--- Nozzle exhaust -> ambient ---
  connect(Flt2Fluid.port_amb, Nzl.port_2) annotation(
    Line(points = {{-180, -40}, {-180, 60}, {200, 60}, {200, -64}}, color = {0, 127, 255}));
  //--- Single Shaft: Cmp <-> Shaft <-> Trb ---
  connect(Cmp.flange_2, Shaft.flange_a) annotation(
    Line(points = {{-40, -80}, {10, -80}}));
  connect(Shaft.flange_b, Trb.flange_1) annotation(
    Line(points = {{30, -80}, {80, -80}}));
  //--- Propeller load (gear-referred) -> Shaft ---
  connect(ramp_PropTorque.y, PropLoad.tau) annotation(
    Line(points = {{-9, -140}, {20, -140}, {20, -130}}, color = {0, 0, 127}));
  connect(PropLoad.flange, Shaft.flange_b) annotation(
    Line(points = {{20, -110}, {20, -100}, {40, -100}, {40, -80}, {30, -80}}));
  annotation(
    experiment(StartTime = 0, StopTime = 60, Tolerance = 1e-06, Interval = 0.02),
    Diagram(coordinateSystem(extent = {{-220, -160}, {220, 100}})),
    Documentation(info = "<html>
<h4>TPE331 Single-Shaft Turboprop with Propeller Load (ex01b)</h4>
<p>Purpose: Verify single-shaft operation with realistic propeller load.</p>
<h5>Architecture</h5>
<pre>
Flt2Fluid -> Inlet -> Cmp(PR=10) -> Comb -> Trb(PR=8) -> Nzl
                           |--- Shaft (J=0.5) ---|
                                    |
                              PropLoad (gear-referred)
</pre>
<h5>Gear Ratio and Load Conversion</h5>
<ul>
<li>TPE331 reduction gear: GR = 20.87 (N_turbine/N_prop = 41730/2000)</li>
<li>Gear efficiency: eta_gear = 0.98</li>
<li>Q_turbine = Q_prop / (GR * eta_gear)</li>
</ul>
<table border=\"1\">
<tr><th>Condition</th><th>Power [kW]</th><th>Q_prop [N.m]</th><th>Q_turbine [N.m]</th></tr>
<tr><td>Max T/O</td><td>700</td><td>3342</td><td>163</td></tr>
<tr><td>Cruise (70%)</td><td>490</td><td>2340</td><td>114</td></tr>
<tr><td>Idle</td><td>100</td><td>477</td><td>23</td></tr>
</table>
<h5>Simulation Scenario</h5>
<ol>
<li>t=0~10s: Idle prop load (-23 N.m), fuel=0.15 kg/s, shaft stabilizes</li>
<li>t=10~15s: Fuel ramp 0.15 to 0.17, shaft accelerates</li>
<li>t=20~25s: Prop load ramp -23 to -114 N.m (idle to cruise)</li>
</ol>
<p>Observe: shaft speed droop under load, TIT response, compressor operating point shift.</p>
</html>"));
end TurboProp_TPE331_ex01b;
