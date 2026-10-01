# Controls Reference

Stor4Build control demonstrations show how a thermal energy storage (TES) system can be operated by overriding a mode schedule during an EnergyPlus simulation. The simple noon-to-six demonstration uses an OpenStudio measure to configure the EnergyPlus Python plugin runtime and a Python plugin to actuate the storage mode schedule.

## Simple Noon-to-Six Demonstration

The demonstration discharges the TES system from noon through 6 PM on every active simulation day. Outside that window, the plugin requests charging. It is intentionally simple so the moving pieces are visible:

- The `add_demo_noon_to_six` measure adds the plugin instance and writes case-specific details.
- The `demo_noon_to_six.py` plugin actuates the TES mode schedule during the EnergyPlus timestep callback.

This control is available from the CLI through the `--control demo12to6` option on the thermal tank commands.

## Measure Setup

The measure lives in `measures/add_demo_noon_to_six/measure.py`. It takes two arguments:

- `tes_type`: the TES technology being simulated. The current demonstration is intended for thermal tank workflows, and the argument leaves room for future extension.
- `plugin_directory`: a directory that can receive generated plugin support files and is included in the EnergyPlus Python plugin search path.

During a run, Stor4Build points the plugin directory at the simulation run directory. The workflow also adds that directory to the EnergyPlus Python search path so generated support files can be imported by the plugin.

For the thermal tank workflows, the measure writes a generated `case_details.py` module:

```python
# This file is generated code, modify at your own risk.
from enum import Enum

class Mode(Enum):
    CHARGE = 1
    IDLE = 0
    DISCHARGE = -1

MODE_SCHEDULE_TYPE = 'Schedule:Compact'
MODE_SCHEDULE_NAME = 'Charge Sch'
```

The generated module tells the plugin which schedule to actuate and which integer values represent charge, idle, and discharge modes. Different TES systems may require different object names, schedule types, or mode values.

The measure then adds a `PythonPlugin_Instance` object that points EnergyPlus at the `demo_noon_to_six` module and the `NoonToSix` plugin class.

## Plugin Behavior

The plugin lives in `plugins/controls/demo_noon_to_six.py`. It imports the generated case details and uses the EnergyPlus Python plugin API to get an actuator handle for the mode schedule.

```python
from pyenergyplus.plugin import EnergyPlusPlugin
from case_details import MODE_SCHEDULE_TYPE, MODE_SCHEDULE_NAME, Mode

class NoonToSix(EnergyPlusPlugin):

    def actuate(self, state, x):
        self.api.exchange.set_actuator_value(state, self.data['mode_actuator'], x)

    def on_begin_zone_timestep_before_init_heat_balance(self, state) -> int:
        if 'mode_actuator' not in self.data:
            self.data['mode_actuator'] = self.api.exchange.get_actuator_handle(
                state, MODE_SCHEDULE_TYPE, "Schedule Value", MODE_SCHEDULE_NAME
            )
            if self.data['mode_actuator'] == -1:
                self.api.runtime.issue_severe(state, "Could not get handle to TES mode schedule")
                return 1

        hour = self.api.exchange.hour(state)
        if hour < 12:
            self.actuate(state, Mode.CHARGE.value)
        elif 12 <= hour < 18:
            self.actuate(state, Mode.DISCHARGE.value)
        else:
            self.actuate(state, Mode.CHARGE.value)
        return 0
```

The callback checks for the schedule actuator once, stores it in plugin state, and then changes the schedule value based on the current simulation hour. The demonstration uses only hour-of-day logic, but the same pattern can be extended to use other EnergyPlus variables and plugin API data.

## Results

The demonstration results use the large office model in climate zone 5A. The default control discharges between 11 AM and 5 PM.

```{figure} ../images/defaults.png
:alt: Default control results with discharge from 11 AM to 5 PM.
:name: fig-controls-default

Default control results with discharge from 11 AM to 5 PM.
```

With the noon-to-six plugin, discharge starts at noon and transitions back to charging at 6 PM.

```{figure} ../images/noon-to-six.png
:alt: Plugin-controlled results with discharge from noon to 6 PM.
:name: fig-controls-noon-to-six

Plugin-controlled results with discharge from noon to 6 PM.
```

The abrupt 6 PM transition occurs because this demonstration requests either charge or discharge. A more realistic control could request idle for a period after discharge or use additional model signals, such as state of charge, load, price, or weather conditions.

## Extending Controls

Custom controls generally follow the same pattern:

1. Add or reuse an OpenStudio measure that creates the plugin instance and writes any case-specific support data.
2. Ensure the plugin directory is available in the EnergyPlus Python plugin search path.
3. Implement an EnergyPlus Python plugin callback that reads simulation state and actuates the TES control schedule.
4. Add output variables or reports that make the resulting behavior easy to verify.

Any output variable available through the EnergyPlus runtime data exchange can be used as an input to richer control strategies.