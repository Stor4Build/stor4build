# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os

class Simulation:
    def __init__(self, name):
    	self.name = name
    def needs_baseline(self):
        return True
    def tag(self):
        return self.name
    def osw(self, seed_file, measures_directory, epw_file, **kwargs):
        osw = {
            'measure_paths': [ measures_directory ],
            'seed_file': seed_file,
            'steps': [
                {
                    "measure_dir_name" : "add_csv_output",
                    "name" : "Add CSV Output",
                    "arguments" : {}
                }
            ],
            'weather_file': epw_file
        }
        return osw
    def run(self, runner, seed_file, measures_directory, **kwargs):
        return None
