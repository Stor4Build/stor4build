# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os

class BadSizing(Exception):
    pass

class Simulation:
    def __init__(self, name, added_steps=None):
    	self.name = name
    	self.added_steps = None
    	if added_steps is not None:
    	    self.added_steps = added_steps
    def tag(self):
        return self.name
    def osw(self, seed_file, measures_directory, epw_file, **kwargs):
        steps = [
                {
                    "measure_dir_name" : "add_csv_output",
                    "name" : "Add CSV Output",
                    "arguments" : {}
                }
            ]
        if self.added_steps is not None:
            steps.extend(self.added_steps)
        osw = {
            'measure_paths': [ measures_directory ],
            'seed_file': seed_file,
            'steps': steps,
            'weather_file': epw_file
        }
        return osw
    def run(self, runner, seed_file, measures_directory, **kwargs):
        return None
