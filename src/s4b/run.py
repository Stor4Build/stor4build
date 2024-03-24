# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import json

def run_workflow(openstudio_exe, run_dir, osw_json, measures_only=False):
    cur_dir = os.getcwd()
    os.chdir(run_dir)
    with open('s4b.osw', 'w') as fp:
        json.dump(osw_json, fp, indent=4)
    if measures_only:
        os.system('%s run -m -w s4b.osw' % (openstudio_exe, ))
    else:
        os.system('%s run -w s4b.osw' % (openstudio_exe, ))
    os.chdir(cur_dir)
    
class Runner:
    def __init__(self, openstudio, run_dir, output_dir, measures_dir):
        self.openstudio = openstudio
        self.run_dir = os.path.abspath(run_dir)
        self.output_dir = os.path.join(self.run_dir, output_dir)
        self.measures_dir = os.path.abspath(measures_dir)
    def osw(self, seed, epw):
        return {
            'measure_paths': [ self.measures_dir ],
            'run_directory': self.output_dir,
            'seed_file': os.path.abspath(seed),
            'steps': [
                {
                    "measure_dir_name" : "add_csv_output",
                    "name" : "Add CSV Output",
                    "arguments" : {}
                }
            ],
            'weather_file': os.path.abspath(epw)
        }
    def run(self, osw_json, measures_only=False):
        run_workflow(self.openstudio, self.run_dir, osw_json, measures_only=measures_only)
        
class PrototypeBuilder:
    def __init__(self, openstudio, run_dir, output_dir, measures_dir):
        self.openstudio = openstudio
        self.run_dir = os.path.abspath(run_dir)
        self.output_dir = os.path.join(self.run_dir, output_dir)
        self.measures_dir = os.path.abspath(measures_dir)
    def osw(self, type, cz, vintage, epw):
        return {
            'measure_paths': [ self.measures_dir ],
            'run_directory': self.output_dir,
            'steps': [
                {
                    'arguments' : {
                        'building_type': type,
                        'climate_zone': cz,
                        'template': vintage
                        },
                    'measure_dir_name' : 'create_doe_prototype_building',
                    'name' : 'Create DOE Prototype Building'
                }
            ],
            'weather_file': os.path.abspath(epw)
        }
    def run(self, osw_json, measures_only=False):
        run_workflow(self.openstudio, self.run_dir, osw_json, measures_only=True)
