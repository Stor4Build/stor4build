# Package Architecture

Stor4Build is an orchestration layer around OpenStudio and EnergyPlus. It does not
replace either simulation engine. The package turns a user scenario into an
OpenStudio Workflow (OSW), runs the workflow, and converts the resulting EnergyPlus
files into comparable baseline and thermal energy storage (TES) results.

```{figure} images/package-architecture.*
:alt: Stor4Build package architecture from user interfaces through workflow assembly, OpenStudio and EnergyPlus simulation, and result processing.
:name: fig-package-architecture
:width: 100%

Stor4Build separates user interfaces and scenario data from workflow construction,
simulation, and result processing.
```

## Architectural Layers

### Interfaces and scenario data

Users can start a study through the command line interface, the Python package, or
the Flask web API. These interfaces normalize the same core inputs: a building
model, weather, storage technology, capacity or sizing target, operating schedule,
and optional utility data.

The main entry points are:

- `stor4build.cli` for local commands and scripted studies.
- `stor4build.IceTank`, `stor4build.DxCoil`, and `stor4build.Simulation` for Python workflows.
- `stor4build.api` for request validation, prototype and weather lookup, simulation,
  and CSV responses.
- `stor4build.schema` for the web/API input model.

The API can retrieve prototype models, weather, and cached baseline results through
`ResultsDatabase`. The CLI normally receives model and weather paths directly.

### Workflow assembly

`Simulation` is the common workflow abstraction. A simulation contains ordered
measure steps, grouped by the stage in which OpenStudio runs them:

1. `ModelMeasure` steps modify the OpenStudio model.
2. `EnergyPlusMeasure` steps modify the translated EnergyPlus input data file (IDF).
3. `ReportingMeasure` steps read results and create reports.

`Simulation.osw()` adds the standard CSV output measure, preserves the stage order,
and writes the seed model, weather file, measure path, and run options into an OSW
dictionary. Technology classes add the measures required for their systems:

- `IceTank` adds the `add_pytank` EnergyPlus measure.
- `DxCoil` adds the `add_packaged_ice_storage` EnergyPlus measure.

Callers can add pre- and post-steps for reporting, cooling-season runs, custom
controls, or other transformations without changing the technology class.

### Simulation engines

`run_workflow()` writes `s4b.osw` into an isolated run directory and invokes the
OpenStudio CLI. OpenStudio applies the measures, translates the model, and runs
EnergyPlus.

The two currently supported storage families use different EnergyPlus integration
paths:

| Storage family | Integration | Typical building system |
| --- | --- | --- |
| Thermal tank ice, chilled water, or PCM | `PlantComponent:UserDefined` plus an EnergyPlus PythonPlugin | Central chilled-water plant |
| Packaged ice storage | Native `Coil:Cooling:DX:SingleSpeed:ThermalStorage` object | Rooftop or other direct-expansion air system |

The thermal-tank plugin participates in the EnergyPlus plant solution at each
timestep. The packaged system relies on a native EnergyPlus component and therefore
does not use the Python tank plugin.

### Results and comparison

OpenStudio and EnergyPlus write their normal run products under the case directory.
Stor4Build repairs known CSV formatting issues, selects a reporting frequency, and
can combine a baseline CSV with the TES CSV. The combined output prefixes baseline
columns and can add scenario, sizing, utility-rate, and demand-period metadata.

This baseline-versus-technology structure is central to the package:

1. Run or retrieve the unmodified baseline.
2. Use baseline loads when the TES technology requires sizing.
3. Build and run the technology case from the same seed model and weather.
4. Align the hourly results for comparison and downstream analysis.

## Repository Map

| Location | Responsibility |
| --- | --- |
| `src/stor4build/cli/` | CLI commands and local orchestration |
| `src/stor4build/api/` | HTTP interface and request-to-simulation orchestration |
| `src/stor4build/schema.py` | Scenario validation and Python data objects |
| `src/stor4build/system.py` | Measure-step types and OSW construction |
| `src/stor4build/run.py` | OpenStudio process invocation |
| `src/stor4build/icetank.py` | Thermal-tank configuration and baseline-based sizing |
| `src/stor4build/dxcoil.py` | Packaged ice-storage workflow |
| `src/stor4build/util.py` | Model lookup and CSV/result processing |
| `measures/` | OpenStudio model, EnergyPlus, and reporting measures |
| `plugins/thermaltank/` | Tank physics, bypass calculation, and EnergyPlus callbacks |
| `plugins/controls/` | Optional control plugins |
| `models/`, `weather/` | Local prototype and weather inputs |
| `tests/`, `regression_tests/` | Unit and end-to-end reference cases |

## Extension Points

The architecture keeps the interfaces separate from EnergyPlus details. New work
generally belongs at one of four boundaries:

- Add a `Simulation` subclass when a technology needs a repeatable set of measures.
- Add an OpenStudio measure when model or IDF objects must be created or changed.
- Add an EnergyPlus PythonPlugin when a custom component or controller must exchange
  data with the solver during a run.
- Add a reporting measure or result-processing function when the simulation is
  complete and no runtime actuation is required.

An extension should preserve the same seed model and weather for baseline and
technology cases, expose its assumptions as measure arguments, and request enough
output variables to verify both energy performance and control behavior.

## Design Boundaries

OpenStudio owns model transformation and workflow execution. EnergyPlus owns the
building and HVAC solution, timesteps, and plant iteration. Python plugins must act
as well-behaved EnergyPlus components: they read values through registered handles,
return physically consistent outlet conditions, and avoid advancing stored state
more than once when EnergyPlus iterates within a timestep.

See {doc}`ice-tank-plugin` for the concrete implementation of this contract in the
thermal-tank plugin.
