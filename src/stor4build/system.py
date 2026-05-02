# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import dataclasses
from typing import Dict, Union

@dataclasses.dataclass
class ModelMeasure:
    name: str
    measure_dir_name: str
    arguments: Dict[str, Union[str, float, int]] = dataclasses.field(default_factory=dict)
    
    def to_dict(self):
        return dataclasses.asdict(self)

@dataclasses.dataclass
class EnergyPlusMeasure:
    name: str
    measure_dir_name: str
    arguments: Dict[str, Union[str, float, int]] = dataclasses.field(default_factory=dict)
    
    def to_dict(self):
        return dataclasses.asdict(self)

@dataclasses.dataclass
class ReportingMeasure:
    name: str
    measure_dir_name: str
    arguments: Dict[str, Union[str, float, int]] = dataclasses.field(default_factory=dict)
    
    def to_dict(self):
        return dataclasses.asdict(self)

class BadSizing(Exception):
    pass

class Simulation:
    def __init__(self, name, pre_steps=None, post_steps=None):
        self.name = name
        self.steps = []
        if pre_steps:
            self.steps = pre_steps
        self.steps.extend(self.required_steps())
        if post_steps:
            self.steps.extend(post_steps)
    def tag(self):
        return self.name
    def required_steps(self):
        return []
    def osw(self, seed_file, measures_directory, epw_file):
        # This one is an OpenStudio measure, so it should be good to go
        first_step = {
            "measure_dir_name" : "add_csv_output",
            "name" : "Add CSV Output",
            "arguments" : {}
        }
        output_steps = [first_step]
        energyplus_measures = []
        reporting_measures = []
        for step in self.steps:
            if isinstance(step, ModelMeasure):
                #print(step)
                output_steps.append(step.to_dict())
            elif isinstance(step, EnergyPlusMeasure):
                energyplus_measures.append(step.to_dict())
            else:
                reporting_measures.append(step.to_dict())
        #print(output_steps)
        #print(energyplus_measures)
        #print(reporting_measures)
        output_steps.extend(energyplus_measures)
        output_steps.extend(reporting_measures)
        osw = {
            'measure_paths': [measures_directory],
            'seed_file': seed_file,
            'steps': output_steps,
            'weather_file': epw_file,
            'run_options': {
                'skip_expand_objects': True
                #'skip_energyplus_preprocess': True
            }
        }
        return osw
    def run(self, runner, seed_file, measures_directory, **kwargs):
        return None
