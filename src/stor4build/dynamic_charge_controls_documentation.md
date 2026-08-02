# Dynamic Charge Controls Documentation

Documentation for the controls written by LBNL (aka. "EASY-SHIFT-lite" in the conceptualization phase, although the control logic is substantially/fundamentally different from the originally EASY-SHIFT algorithm). We have erred toward overdocumenting things that might be obvious to some, to reduce the risk of confusion/mistakes.

These controls address the challenges of:
- Optimize to reduce cost under varying TOU rates, while accounting for changes in weather/load on each day
- Charging can create new demand charges by leading to spikes in demand, not good for electric tariffs with high demand charges
- Account for changes in COP of charging/discharging

## Summary of Current Development Status (as of July 31, 2026)

The control functions are stable in that they will run for the various models, but we are aware of several bugs that are still work in progress. __The inputs, outputs, and general structure of the control functions are expected to remain the same.__ However, the processing/logic within the controls for the exact charge/discharge schedule still needs to be improved. The only file we anticipate needing to modify is `stor4build/src/stor4build/dynamic_charge_controls.py`, which is a self-contained file for the controls functions. Thus, we recommend that __others in the project team may begin integration with the GUI tool simultaneously as we finalize the control functions.__ Expect that with some building models and weather file combinations, the schedules might not be very effective and occasionally be nonsensical at this point. The schedules will improve over time as we wrap up development.

Scope: _Should_ work for any chiller-based model that can use icetank storage. Developed primarily using LargeOffice_4A_2019.osm, tested that it runs without crashing for LargeDataCenterHighITE, LargeHotel.

Command Line - Working, tested for a few cases but not extensively

GUI - not yet attempted


## Command Line Usage
Command line function has been developed, loosely adapted from `run-icetank`. Refer to `src/stor4build/cli/__init__.py`. The major steps for `run-icetank-dynamic` are as follows: 
1. Run model in OpenStudio and E+ with icetank and a charge schedule that keeps the icetanks in idle the entire time to create a baseline with the same parameters we can read when scheduling the controls. This uses the new `add_pytank_with_schedule` measure, adapted from `add_pytank`. This charge schedule is a constant in `stor4build/resources/baseline_schedule_15min.csv`. The outputs of this simulation will go into a "no_icetank" folder within the output directory specified with the `-r` parameter.
2. Using the output files of step 1, run `generate_schedule()` in `stor4build/src/stor4build/dynamic_charge_controls.py`. This will run the scheduling script, which will produce a file called `dynamic_charge_schedule.csv` with TES mode and charging temperature
3. Run the model in OpenStudio and E+ again with the `add_pytank_with_schedule` measure, this time with the optimized charging mode schedule. The result will be in the `run` subdirectory of the output directory specified with the `-r` parameter.


Run using

```bash
stor4build  run-icetank-dynamic \<path_to_osm\> \<path_to_epw\> --openstudio "C:\openstudio-3.7.0\bin\openstudio.exe" -r \<path_to_results_folder\> -m \<path_to stor4build/measures\> --ntanks \<int\>
```

## Charge Controls Functions
The scheduling algorithm is written in Python. All of the functions are  in `stor4build/src/stor4build/dynamic_charge_controls.py`

List of dependencies:
```python
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
import traceback
import os
import re
import collections
from epw import epw
import sys
```

__epw__ is a package for EnergyPlus weather files (.epw). It can be installed using
```bash
pip install git+https://github.com/building-energy/epw.git@master
```

The optimization relies on being able to obtain the baseline electric and thermal loads, chiller performance curves, chiller sizing, outdoor air temperature, and other data pulled from the various input files. This was challenging to fully automate and a common cause of bugs when trying to run with different models. We think it is working now, but if it ends in an `IndexError`, this is a probable culprit. 
- OAT: from .epw used to run the model
- baseline loads and performance: from eplusout.csv from the baseline run
- chiller parameters: from input .idf generated

The only function we call directly is `generate_schedule()`. This 

## Impacts on other files/codes in the repo
1. The OSM file needs some of the `OS:Output:Variable` outputs that were removed since the old s4b repo, as these are inputs to the dynamic charge controls. We added them back to some of the `.osm` files. See the "Add Output:Variable to osm files for dynamic charge controls" commit. 
2. The `run-icetank-dynamic` function is added to `src/stor4build/cli/__init__.py`. Appropriate entries are also added to the --help output
3. The older s4b repo would save "in.epw" with the input weather file. The current version does not. We were originally assuming we could use the in.epw file, but built another method that accepts the path to the epw file automatically rather than modifying the existing code.

To our knowledge, the additions/changes do not impact the functioning of anything else in the repo.

## Caveats/known bugs and quirks
__Timestep__: Currently, the code only works with a timestep of 15 minutes (or 4 timesteps per hour). This is enforced in the `add_pytank_with_schedule` measure

__Controls Schedule Issues:__ During testing, periods of up to 1 month in the summer led to fairly effective schedules. However, during the full integration, we observed that runperiods that include the full year often have strange results, particularly large chunks of time in "discharge" mode during the non-cooling season, with no "charge" periods to offset it. We are investigating several possible causes, all of which involve small tweaks to the controls logic. Fixing this should not impact the integration with the overall tool. 

__Python Warnings__: There are a few FutureWarnings that pop up when running the code. We fixed most of them, but a few are still lurking. We tested with Python 3.13 and 3.8. If others using newer versions get an actual error due to these, let us know and we'll figure it out. 

__Modifying/Recompiling__: if anything is changed in the Python scripts, first need to run this command to reflect the changes when running stor4build commands

```bash
pip uninstall stor4build -y && pip install . 
```
