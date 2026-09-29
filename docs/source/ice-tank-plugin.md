# Ice-Tank Python Plugin

Stor4Build models central ice storage as a user-defined component on the supply side
of an EnergyPlus chilled-water loop. A PythonPlugin supplies the component setup,
control logic, bypass calculation, thermophysical properties, and tank energy
balance that EnergyPlus does not provide through a native ice-tank plant object.

The same framework can run sensible chilled-water storage and the included PCM
property model. Packaged DX ice storage follows a separate, native EnergyPlus path
and is not covered on this page.

```{figure} images/ice-tank-plant-loop.png
:alt: Chilled-water loop with pump, chiller, Python-controlled ice tank and bypass, and chilled-water coils.
:name: fig-ice-tank-plant-loop
:width: 100%

The tank and bypass form a `PlantComponent:UserDefined` between the chiller and the
demand-side coils. EnergyPlus solves the surrounding plant loop while Python solves
the storage branch.
```

## Construction at a Glance

```{figure} images/plugin-lifecycle.*
:alt: Ice tank plugin build-time and EnergyPlus runtime lifecycle.
:name: fig-plugin-lifecycle
:width: 100%

The OpenStudio measure constructs the EnergyPlus objects before the simulation.
EnergyPlus then calls two plugin instances during initialization and each timestep.
```

The implementation has four layers:

| Layer | File | Role |
| --- | --- | --- |
| Stor4Build configuration | `src/stor4build/icetank.py` | Holds user options, sizes tanks from baseline results, and creates the `add_pytank` workflow step |
| OpenStudio measure | `measures/add_pytank/measure.rb` | Rewrites the plant loop and creates plugin, schedule, actuator, output, and search-path objects |
| EnergyPlus adapter | `plugins/thermaltank/icetes_schctrl.py` | Acquires API handles, selects operating mode, actuates the plant component, and publishes outputs |
| Component model | `tank_bypass_branch.py`, `simple_ice_tank.py`, and `fluid.py` | Solves the bypass split, tank heat transfer and phase change, and fluid properties |

## From Stor4Build Inputs to an EnergyPlus Model

`IceTank.required_steps()` packages the charge and discharge windows, charge
temperature, number of tanks, trim temperature, chiller size fraction, storage type,
storage medium, and Python site-packages path as arguments to `add_pytank`.

The measure then modifies the translated EnergyPlus workspace. Its main actions are:

1. Create charge, discharge, setpoint, and parameter schedules from the arguments.
2. Resize the chiller when a size fraction below 1.0 is requested.
3. Insert an `Ice Tank` `PlantComponent:UserDefined` on the chilled-water supply side.
4. Connect initialization and simulation program names to that component.
5. Register two `PythonPlugin:Instance` objects from `icetes_schctrl`:
   `UsrDefPlntCmpSet` and `UsrDefPlntCmpSim`.
6. Add plugin search paths for the thermal-tank code, optional controls, and external
   packages such as NumPy, SciPy, and SecondaryCoolantProps.
7. Declare Python global and output variables so tank state and heat transfer appear
   in EnergyPlus output.

The measure also configures a user-defined loop fluid and plant equipment records
needed to place the component in EnergyPlus's plant topology. These object names are
part of the current plugin contract; changing names in the measure requires matching
changes in the callback code.

## The Two Plugin Instances

EnergyPlus associates separate Python classes with component setup and simulation.

### `UsrDefPlntCmpSet`

The setup class runs at the user-defined component model callback to initialize
plant-side limits. It reads the chilled-water loop design volume flow and actuates
the component minimum and maximum mass flow, design volume flow, and loading
capacity fields. This tells the plant solver what the custom component can accept.

### `UsrDefPlntCmpSim`

The simulation class owns the runtime exchange with EnergyPlus. It waits for API data
to become available and acquires handles once. The handles cover:

- charge, tank, chiller, and trim schedules;
- inlet temperature and mass flow internal variables;
- outlet temperature and mass flow actuators;
- loop flow and component setup values;
- Python global variables used for configuration and reporting.

Its `on_begin_timestep_before_predictor` callback reads schedules and selects charge,
discharge, or float operation. It also sets the chiller and tank-side setpoints. Its
`on_user_defined_component_model` callback reads the current inlet conditions, runs
the tank branch model, and writes outlet mass flow and temperature back to
EnergyPlus.

## Operating Modes and the Bypass Branch

`TankBypassBranch` represents parallel flow through the tank and around it. The
branch uses three modes:

| Mode | Branch behavior | Plant intent |
| --- | --- | --- |
| Charge (`1`) | Send all available flow through the tank | Freeze the storage medium using the lower chiller setpoint |
| Float (`0`) | Bypass the tank | Preserve stored energy while the tank still exchanges heat with its environment |
| Discharge (`-1`) | Solve for a tank/bypass split | Meet the tank-branch outlet setpoint without overcooling the loop |

During discharge, the branch first checks the all-bypass and all-tank limits. When
the target lies between them, SciPy minimizes the outlet-temperature error over a
bypass fraction from 0 to 1. The mixed outlet temperature follows the mass-weighted
tank and bypass streams.

## Tank Physics

`simple_ice_tank.IceTank` is a lumped storage model. Its state variables are tank
temperature and solid mass. The model calculates:

- heat transfer from the plant fluid through a state-of-charge-dependent heat
  exchanger effectiveness;
- heat gain or loss through the tank envelope;
- sensible heating and cooling of liquid and solid storage media;
- latent freezing and melting at the storage-medium freeze point;
- outlet fluid temperature from effectiveness and the inlet-to-tank temperature
  difference.

The heat balance is evaluated with EnergyPlus inlet conditions and timestep length.
EnergyPlus may call a component more than once while converging a plant timestep, so
the model stores the previous accepted tank state. It advances that state only when
simulation time moves forward; repeated calls at the same time restore the previous
state before recalculation. This prevents solver iterations from charging or
discharging the tank multiple times.

`fluid.py` separates thermophysical properties from the energy balance. The default
water model uses SecondaryCoolantProps for temperature-dependent liquid properties
and adds fusion and solid specific-heat values. `SimpleWater` provides fixed
properties for testing, and `PCM2X2A` supplies the included phase-change material
properties.

## Sizing Before Simulation

`IceTank.size()` uses a completed baseline EnergyPlus CSV rather than the plugin to
choose tank count. It:

1. Selects chiller evaporator cooling energy and mass-flow columns.
2. Restricts data to the requested discharge window.
3. Finds the day with the largest cooling energy in that window.
4. Applies the requested peak-reduction percentage.
5. Divides by the nominal single-tank capacity and rounds up to a whole tank.
6. Computes a trim temperature from available capacity, baseline flow, discharge
   duration, and storage-medium specific heat.

The sized count and trim temperature become inputs to the same construction and
runtime path described above. The sizing method therefore remains outside the
timestep plugin and can evolve independently from the component physics.

## Controls and Outputs

The default schedules created by `add_pytank` select mode by time of day. Optional
control measures can add another PythonPlugin that actuates the mode schedule. This
keeps supervisory control separate from the component model: a control chooses the
mode, while `UsrDefPlntCmpSim` and `TankBypassBranch` determine physically consistent
plant conditions.

The plugin publishes values used to diagnose the storage calculation, including
tank temperature, state of charge, heat transfer, bypass fraction, tank flow, and
operating mode. The `add_thermaltank_outputs` measure requests the surrounding
chiller and plant variables needed for baseline/TES comparisons.

See {doc}`reference/controls` for the control-plugin pattern.

## Developing or Debugging the Plugin

Keep changes aligned across the layers:

- A new user option needs a Stor4Build argument, an OpenStudio measure argument and
  object value, and a runtime handle or configuration value if the plugin uses it.
- A renamed EnergyPlus object, schedule, global, or output variable must be updated
  in both `measure.rb` and `icetes_schctrl.py`.
- A new storage medium should implement the property methods used by
  `simple_ice_tank.py` and be added to the factory in `fluid.py`.
- A new control should actuate the mode schedule instead of duplicating the tank
  physics.

Use a measures-only run to inspect the generated `s4b.osw` and EnergyPlus objects
before running the annual simulation. During a full run, verify plugin handle errors,
the three operating modes, state-of-charge bounds, outlet-temperature continuity,
and the expected energy shift in the combined CSV. Unit tests cover workflow
construction and baseline-based sizing; regression cases provide end-to-end output
comparisons.
