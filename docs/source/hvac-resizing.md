# HVAC Resizing

## Introduction

The addition of thermal energy storage to a heating, ventilation, and air-conditioning (HVAC) system may allow for downsizing of the mechanical cooling equipment in the system because both the TES and mechanical cooling can operate simultaneously to provide the same capacity as the mechanical cooling equipment of an HVAC system without TES.

## Background

In this case, the mechanical cooling equipment in the HVAC system is a chiller that produces **6.7°C** chilled water to meet building cooling demands. The TES is tanks of either ice or chilled water that are “charged” during times when the building that the HVAC system serves is unoccupied and then “discharged” during times of high cooling needs or periods of high utility costs. Charging means running the chiller to store thermal energy in the tanks and discharging means extracting the stored thermal energy from the tanks.

During charging, the chiller is run at a setpoint temperature lower than **6.7°C** such that the energy can be extracted from the storage medium. For example, a possible charging temperature for ice is **-3.8°C** and a possible charging temperature for chilled water is **1.1°C**. Conversely, during discharging, the chiller is run at a setpoint temperature higher than **6.7°C** and stored thermal energy is extracted from the tanks that are at temperatures less than **6.7°C** to provide the same chilled water temperature to meet building cooling demands. In other words, the building always receives the same temperature of chilled water, but that water temperature is met with some combination of the chiller and TES.

## Methodology

Here, we’re using energy simulations to investigate the potential benefits of adding TES to HVAC systems. These energy simulations are being performed with EnergyPlus, a whole building energy simulation program that can be used to model energy consumption for, among others, HVAC systems in buildings. EnergyPlus is a console-based program that reads input from text files, including component-based HVAC. In our simulations, one of these components is the chiller.

The chiller is an empirical model that uses performance information at reference conditions along with three curves for cooling capacity and efficiency to determine chiller operation at off-reference conditions. The chiller’s capacity is determined using EnergyPlus’s built-in automatic equipment sizing features, making downsizing the chiller’s capacity less straightforward than it may appear. The chiller’s capacity is determined during a sizing step at the beginning of the simulation, so the value is not known until the simulation executes, thus making it difficult to force the chiller to be a smaller size. If we were not using the automatic equipment sizing feature, the chiller would have a known size that could be adjusted before executing the simulation.

To mimic downsizing of the chiller, we modify the maximum part load ratio (PLR) of the chiller. The PLR is the actual cooling load divided by the chiller’s available cooling capacity. Typically, the maximum PLR of the chiller is one (e.g., the chiller can operate up to its full capacity). Here, we allow the user to set this to one of five values: **0.5, 0.6, 0.7, 0.8, 0.9**. A value of **0.9** would represent a **10%** reduction in chiller capacity while a value of **0.5** would effectively halve the size of the chiller. In summary, instead of adjusting the size of the chiller, we adjust to what fraction of its total capacity it can run to.

This approach works but introduces another factor to consider. One of the chiller performance curves is the electric input to cooling energy output ratio as a function of PLR. This quadratic curve parameterizes the variation of the energy input ratio (EIR) as a function of PLR. The EIR is the inverse of the coefficient of performance (COP), and the PLR, as mentioned earlier, is the actual cooling load divided by the chiller’s available cooling capacity.

When we mimic the downsizing of the chiller by limiting the maximum PLR, we need to adjust this curve accordingly. We adjusted these curves by making sure the endpoint remains the same as a non-downsized chiller. In other words, the value that the unmodified curve takes at one must be the same as the modified curve takes at the chosen downsizing value (**0.5, 0.6, 0.7, 0.8, or 0.9**). The table below summarizes how the curve coefficients are modified for different downsized values.

| Maximum PLR | Constant Term | Linear Coefficient | Quadratic Coefficient |
|-------------|--------------:|-------------------:|----------------------:|
|     1.0     |     0.2221    |        0.5032      |         0.2569        |
|     0.9     |     0.2221    |        0.5591      |         0.3172        |
|     0.8     |     0.2221    |        0.6289      |         0.4014        |
|     0.7     |     0.2221    |        0.7188      |         0.5243        |
|     0.6     |     0.2221    |        0.8386      |         0.7136        |
|     0.5     |     0.2221    |        1.0063      |         1.0276        |

This section will describe how Stor4Build handles HVAC resizing when thermal energy storage is added to a building model.

### When resizing is required

Downsizing the chiller is not required but can be specified through the web user interface. Values available are **100%** (no downsizing), **90%**, **80%**, **70%**, **60%**, **50%**.

One of the goals of using thermal storage is to reduce HVAC equipment costs or peak power usage by downsizing. If a user of the tool wishes to explore the impacts of chiller downsizing, the above input is available. Currently this feature is only available for chiller-based systems.

### Which equipment and plant loops may be affected

The implementation has been to leave the EnergyPlus chiller object and the distribution system the same as if there were not downsizing to eliminate unintended consequences or spurious results.

The performance curve in EnergyPlus for chillers is not constant, as shown in Fig 1. The curve is assumed to be the same for any capacity of chiller. A chiller operating at a PLR of **0.8** will have the same EIR as another larger chiller operating at a PLR of **0.8**.

```{figure} ../images/hvac-resizing-eir-multiplier.png
:alt: Default control results with discharge from 11 AM to 5 PM.
:name: eir-multiplier

Chiller performance curves for three representative downsizing options based on the coefficients in the table above. The PLR calculated by EnergyPlus for the nominal-size chiller (e.g. no downsizing) is used to obtain an EIR multiplier for the appropriate downsizing curve. The curves with more downsizing are always above curves with less downsizing. Therefore, a **10%** downsized chiller will always use more energy to meet a given cooling load than the baseline chiller, etc.
```

The tool uses the maximum PLR input, along with this performance curve, to estimate the power required for a smaller chiller to provide the required amount of cooling at each timestep.

For example:

- A baseline building with no TES is autosized by EnergyPlus to have a chiller that will meet all loads during the year.
- A web tool user that is investigating TES also wants to see how the building will perform if the chiller is downsized to **80%** of its original size.
- The web tool uses the above performance curve — which is the same for both chillers — but specifies the maximum PLR to be **0.8**.
- EnergyPlus will not allow the chiller to operate at **PLR > 0.8**. If the building loads are too great, even when incorporating TES dispatch, EnergyPlus will record the cooling shortfall as unmet hours.
- The tool overwrites the EIR that EnergyPlus uses to calculate energy used during the timestep.
    - `EIR_new = EIR_baseline * EIR_multiplier`
    - `EIR_multiplier` is obtained automatically in the code by using the PLR for the nominal size chiller.
    - EnergyPlus calculates electrical power used from the `EIR_new` that is passed to the chiller object.

The tool allows users to specify chiller downsizing without regard to whether this will provide adequate cooling. Specifying too small of a chiller for the accompanying TES will result in unmet hours that the user can see in the results file, but it will not prevent the simulation from completing.
