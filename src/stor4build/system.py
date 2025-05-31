# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause

class BadSizing(Exception):
    pass

class Simulation:
    def __init__(self, name, pre_steps=None, post_steps=None):
        self.name = name
        self.steps = []
        if pre_steps:
            self.steps.extend(pre_steps)
        self.steps.extend(self.required_steps())
        if post_steps:
            self.steps.extend(post_steps)
    def tag(self):
        return self.name
    def required_steps(self):
        return []
    def osw(self, seed_file, measures_directory, epw_file):
        first_step = {
            "measure_dir_name" : "add_csv_output",
            "name" : "Add CSV Output",
            "arguments" : {}
        }
        output_steps = [first_step]
        output_steps.extend([el.to_dict() for el in self.steps])
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
