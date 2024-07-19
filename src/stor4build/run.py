# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import json

def run_workflow(openstudio_exe, run_dir, osw_json, measures_only=False):
    cur_dir = os.getcwd()
    if not os.path.exists(run_dir):
        os.makedirs(run_dir, exist_ok=True)
    os.chdir(run_dir)
    with open('s4b.osw', 'w') as fp:
        json.dump(osw_json, fp, indent=4)
    if measures_only:
        os.system('%s run --show-stdout --measures_only -w s4b.osw' % (openstudio_exe, ))
    else:
        os.system('%s run --show-stdout -w s4b.osw' % (openstudio_exe, ))
    os.chdir(cur_dir)
    
class Runner:
    def __init__(self, seed, epw, openstudio, run_dir, output_dir, measures_dir):
        self.openstudio = openstudio
        self.run_dir = os.path.abspath(run_dir)
        self.output_dir = output_dir
        self.measures_dir = os.path.abspath(measures_dir)
        self.seed = os.path.abspath(seed)
        self.epw = os.path.abspath(epw)
    def osw(self):
        return {
            'measure_paths': [ self.measures_dir ],
            'run_directory': self.output_dir,
            'seed_file': self.seed,
            'steps': [
                {
                    "measure_dir_name" : "add_csv_output",
                    "name" : "Add CSV Output",
                    "arguments" : {}
                }
            ],
            'weather_file': self.epw
        }
    def run(self, osw_json, ouput_relative_path, measures_only=False):
        run_workflow(self.openstudio, os.path.join(self.run_dir, ouput_relative_path),
                     osw_json, measures_only=measures_only)
    def multirun(self, osws, measures_only=False, subdirs = None):
        if subdirs is not None:
            if len(osws) != len(subdirs):
                subdirs = None
        if subdirs is None:
            subdirs = [str(el) for el in range(len(osws))]
        for osw, subdir in zip(osws, subdirs):
            run_dir = os.path.join(self.run_dir, subdir)
            if not os.path.exists(run_dir):
                os.mkdir(run_dir)
            run_workflow(self.openstudio, run_dir, osw, measures_only=measures_only)
        
class PrototypeRunner:
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
