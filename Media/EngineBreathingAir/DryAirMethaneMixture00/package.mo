within PropulsionSystem.Media.EngineBreathingAir;

package DryAirMethaneMixture00 "CH4, N2, O2"
  extends Modelica.Media.IdealGases.Common.MixtureGasNasa(mediumName="DryAirMethaneMixture00",
    data={Modelica.Media.IdealGases.Common.SingleGasesData.CH4, Modelica.Media.IdealGases.Common.SingleGasesData.N2, Modelica.Media.IdealGases.Common.SingleGasesData.O2},
	fluidConstants={Modelica.Media.IdealGases.Common.FluidData.CH4, Modelica.Media.IdealGases.Common.FluidData.N2, Modelica.Media.IdealGases.Common.FluidData.O2},
	substanceNames={"Methane","Nitrogen","Oxygen"},
	reference_X= {1.0e-6, 0.768, 0.232 - 1.0e-6}
    );
  
end DryAirMethaneMixture00;
