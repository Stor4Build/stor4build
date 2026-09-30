# Packaged Ice-Storage DX Coil

Stor4Build models packaged ice storage with EnergyPlus's native
`Coil:Cooling:DX:SingleSpeed:ThermalStorage` object. This pathway represents a
packaged air-conditioning unit whose cooling coil and ice storage are integrated in
one component. It is intended for rooftop and similar direct-expansion air systems,
not central chilled-water plants.

Unlike the central ice-tank implementation, the packaged system does not use an
EnergyPlus PythonPlugin for its component physics. EnergyPlus calculates cooling,
charging, discharging, state of charge, and electric power from the native object
and its performance curves.

## Construction at a Glance

The `DxCoil` workflow changes the translated EnergyPlus model in this order:

| Stage | Action |
| --- | --- |
| Stor4Build | `DxCoil` adds the `add_packaged_ice_storage` EnergyPlus measure to the OSW |
| Resource import | The measure imports schedules, performance curves, and output requests from `TESCurves.idf` |
| Coil discovery | The measure finds selected single-speed and two-speed DX cooling coils in supported container objects |
| Replacement | It creates a `Coil:Cooling:DX:SingleSpeed:ThermalStorage`, reconnects the container to it, and removes the original coil |
| Simulation | EnergyPlus autosizes and simulates the packaged cooling and storage component |
| Reporting | Stor4Build requests comparison variables and reads the final ice capacities from the EnergyPlus SQL results |

The replacement happens after OpenStudio translates the model. The source OSM file
remains unchanged, and each run receives a newly generated EnergyPlus input model.

## Implementation Layers

| Layer | File | Role |
| --- | --- | --- |
| Stor4Build configuration | `src/stor4build/dxcoil.py` | Defines the required measure and its Stor4Build defaults |
| CLI orchestration | `src/stor4build/cli/__init__.py` | Runs baseline and technology cases, adds reports, and combines CSV results |
| EnergyPlus measure | `measures/add_packaged_ice_storage/measure.rb` | Finds eligible coils and constructs the native thermal-storage replacements |
| Curves and schedules | `measures/add_packaged_ice_storage/resources/TESCurves.idf` | Supplies packaged-TES performance curves, predefined schedules, and output requests |
| Comparison outputs | `measures/add_dx_coil_outputs/measure.py` | Requests common baseline and TES variables |
| Sizing report | `measures/get_dx_coil_sizes/measure.py` | Reads autosized ice capacity from the EnergyPlus SQL database |

## The `DxCoil` Workflow Object

`DxCoil` is a `Simulation` subclass. Its `required_steps()` method creates one
`EnergyPlusMeasure` named `Add Packaged Ice Storage`. Stor4Build currently passes
these defaults:

| Measure argument | Stor4Build value | Meaning |
| --- | --- | --- |
| `ice_cap` | `AutoSize` | Let EnergyPlus size each ice store |
| `size_mult` | `1` | Apply no manual multiplier to storage duration |
| `ctl` | `ScheduledModes` | Read the operating mode from the selected schedule |
| `sched` | `Simple User Sched` | Build a schedule from charge and discharge times |
| `wknd` | `False` | Do not discharge on weekends in the simple schedule |
| `hourly` | `False` by default | Leave detailed measure outputs at timestep frequency unless requested |

Optional `charge_start`, `charge_end`, `discharge_start`, and `discharge_end`
values are forwarded when supplied. If Stor4Build omits them, the measure defaults
to charging from 10 PM to 7 AM and discharging from noon to 6 PM.

`DxCoil.size()` currently records `{"algorithm": "autosize"}` and returns the same
workflow configuration. It does not analyze baseline loads in Python. This differs
from `IceTank.size()`, which calculates a whole-tank count and trim temperature from
the baseline CSV before constructing the technology case.

## Coil Discovery and Replacement

The EnergyPlus measure searches the translated workspace for
`Coil:Cooling:DX:SingleSpeed` and `Coil:Cooling:DX:TwoSpeed` objects. A coil is
eligible only when the measure can find it inside one of these containers:

- `CoilSystem:Cooling:DX`
- `AirLoopHVAC:UnitarySystem`

For every selected coil, the measure:

1. Records the original coil and container names for reporting.
2. Creates ambient and condenser outdoor-air nodes.
3. Creates a native packaged thermal-storage coil and assigns the original
   evaporator inlet and outlet nodes.
4. Copies the original cooling capacity, COP, and applicable performance-curve
   references. For a two-speed coil, the current implementation uses its low-speed
   data.
5. Changes the container's coil type and name to reference the new thermal-storage
   object.
6. Removes the original DX coil from the translated EnergyPlus workspace.

The measure writes an original-to-replacement object map into its report directory.
Stor4Build uses that map when it builds detailed output metadata.

## Native Component and Performance Curves

The replacement object contains both the conventional DX cooling mode and an ice
store. EnergyPlus owns the component state and applies the performance curves for
each available mode. `TESCurves.idf` supplies the thermal-storage curves and several
predefined operation schedules. The replacement retains selected baseline coil
curves for cooling-only operation.

The current object enables these modes:

| Index | Mode | Current use |
| ---: | --- | --- |
| 0 | Off | Component unavailable |
| 1 | Cooling only | Conventional DX cooling while storage remains idle |
| 4 | Charge only | Freeze the store without providing zone cooling |
| 5 | Discharge only | Provide zone cooling from storage |

The current measure disables simultaneous cooling-and-charge mode 2 and simultaneous
cooling-and-discharge mode 3 because the required performance curves are not
available in the included curve set.

## Schedule Control

The Stor4Build pathway selects EnergyPlus `ScheduledModes` control. The simple
schedule assigns charge-only mode during the charge window, discharge-only mode
during the discharge window, and cooling-only mode at other times. Outside the
configured cooling season, it requests cooling-only operation.

With Stor4Build's `wknd=False` default, weekends charge through the configured charge
end time and then remain in cooling-only mode. More complex predefined schedules can
be selected when running the measure directly, or added to `TESCurves.idf`.

The measure also contains an EMS control option. That option creates a sensor for
the intended schedule, a state-of-charge sensor, and an operating-mode actuator for
each replacement coil. The EMS logic prevents discharge below a 5% end fraction and
prevents charging above 99%. The current `DxCoil` class does not select this option;
it explicitly requests `ScheduledModes`.

## Autosizing and Capacity Reporting

When `ice_cap` is `AutoSize`, the simple discharge-window duration becomes the
EnergyPlus storage-capacity sizing factor in hours. The default noon-to-6-PM window
therefore requests six hours of storage at the component's sizing load. `size_mult`
scales this duration.

The measure can also accept hard-sized capacities in refrigeration ton-hours when
run directly. It converts those values to gigajoules before writing the EnergyPlus
object. Stor4Build's `DxCoil` class currently always requests autosizing.

After the simulation, `get_dx_coil_sizes` queries the EnergyPlus `ComponentSizes`
table for each thermal-storage coil's `Ice Storage Capacity`. It writes object names
and capacities to a CSV report. The CLI prints those values in gigajoules when
`--show-sizing` is used and includes them in detailed output metadata when an output
CSV is requested.

## Outputs and Interpretation

The baseline and packaged-storage cases both request cooling electricity. The TES
case additionally requests the simple control schedule and
`Cooling Coil Ice Thermal Storage End Fraction`. The imported resource file also
requests operating mode, cooling rate, electric power, ambient tank heat transfer,
and mechanical storage heat transfer at timestep frequency.

```{figure} images/packaged-ice-results.png
:alt: Packaged ice-storage power and state of charge over two summer days, with peak, shoulder, and off-peak periods shaded.
:name: fig-packaged-ice-results
:width: 100%

Example packaged ice-storage operation. Charging raises state of charge before the
peak period; discharging reduces grid-connected cooling power during the peak window.
```

When `stor4build run-dxcoil` receives `--output`, it forces a baseline run, adds the
sizing report, repairs both EnergyPlus CSV files, and writes an aligned hourly
baseline/TES comparison. This output is the appropriate place to compare cooling
electricity and verify that the storage schedule moved load to the intended hours.

## Supported Models and Limitations

Stor4Build assigns packaged ice storage to prototype buildings with compatible
packaged DX systems. The current support map includes:

- SecondarySchool and PrimarySchool
- SmallOffice and MediumOffice
- Warehouse
- RetailStandalone and RetailStripmall
- QuickServiceRestaurant and FullServiceRestaurant
- Outpatient and Laboratory

Laboratory prototypes are available only for 2004 and later vintages. Support is
based on the repository's prototype models and regression cases; an arbitrary OSM
must still satisfy the container requirements described above.

Important implementation limitations are:

- The replacement depends on how the original coil is wrapped. Unsupported or
  unexpected container arrangements cause the measure to fail or skip replacement.
- Two-speed replacements currently inherit low-speed cooling data.
- Simultaneous cooling-and-charge and cooling-and-discharge modes are unavailable.
- Autosizing applies the same duration multiplier pattern to each selected unit.
- The native object and bundled curves represent a particular packaged TES model;
  they are not a general-purpose interface for every packaged storage product.

## Running and Debugging

Run a packaged storage case with:

```console
stor4build run-dxcoil MODEL.osm WEATHER.epw --measures-dir measures --output output.csv --show-sizing
```

A measures-only run is useful for inspecting the translated coil replacement before
committing to a full annual simulation. Check the OpenStudio measure log for the
number of eligible containers, the original and replacement coil names, and the
replacement count.

For a completed run, verify:

- each intended cooling coil has one thermal-storage replacement;
- the simple schedule requests modes 4, 5, and 1 at the expected times;
- the state-of-charge end fraction remains between 0 and 1;
- the SQL sizing report contains every replacement coil;
- cooling energy moves out of the discharge window without unexpected unmet load.

Unit tests verify the OSW step and default arguments. The packaged-ice regression
cases exercise supported prototype types across several climates and vintages.

See {doc}`architecture` for the surrounding workflow architecture and
{doc}`ice-tank-plugin` for the central-plant PythonPlugin implementation.
