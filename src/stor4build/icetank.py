# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os
from .system import Simulation

class IceTank(Simulation):
    default_charge_start = '21:00'
    default_charge_end = '07:00'
    default_discharge_start = '12:00'
    default_discharge_end = '18:00'
    default_charge_temp = -3.8
    default_num_tanks = 1
    default_trim_temp = 10.0
    def __init__(self, name, **kwargs):
        super().__init__(name)
        self.charge_start = kwargs.get('charge_start', self.default_charge_start)
        self.charge_end = kwargs.get('charge_end', self.default_charge_end)
        self.discharge_start = kwargs.get('discharge_start', self.default_discharge_start)
        self.discharge_end = kwargs.get('discharge_end', self.default_discharge_end)
        self.charge_temp = kwargs.get('charge_temp', self.default_charge_temp)
        self.num_tanks = kwargs.get('num_tanks', self.default_num_tanks)
        self.trim_temp = kwargs.get('trim_temp', self.default_trim_temp)
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
        osw['steps'].append({
            "measure_dir_name" : "add_pytank",
            "name" : "Add Python Tank",
            "description" : "This measure will add the Python tank model.",
            "modeler_description" : "This measure will add the Python tank model.",
            "arguments" : {
                "chrg_start": self.charge_start,
                "chrg_end": self.charge_end,
                "dchrg_start": self.discharge_start,
                "dchrg_end": self.discharge_end,
                "chrg_temp": self.charge_temp,
                "num_tanks": self.num_tanks,
                "trim_temp": self.trim_temp
            }
        })
        osw['steps'].append({
                    "measure_dir_name" : "add_output_variables",
                    "name" : "Add Output Variables",
                    "arguments" : {}
                })
        return osw

