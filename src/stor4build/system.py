# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause

class BadSizing(Exception):
    pass

class Simulation:
    def __init__(self, name, pre_steps=None, post_steps=None, added_steps=None):
        self.name = name
        self.added_steps = None
        if added_steps is not None:
            self.added_steps = added_steps
        pre = []
        if pre_steps:
            pre = pre_steps
        post = []
        if post_steps:
            post = post_steps
        self.steps = self.assemble_steps(pre, post)
    def tag(self):
        return self.name
    def assemble_steps(self, pre_steps, post_steps):
        return pre_steps + post_steps
    def osw(self, seed_file, measures_directory, epw_file, **kwargs):
        first_step = {
            "measure_dir_name" : "add_csv_output",
            "name" : "Add CSV Output",
            "arguments" : {}
        }
        output_steps = [first_step]
        output_steps.extend([el.to_dict() for el in self.steps])
        if self.added_steps is not None:
            output_steps.extend(self.added_steps)
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
