# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause

from .system import System

class IceTank(System):
    default_charge_start = '21:00'
    default_charge_end = '07:00'
    default_discharge_start = '12:00'
    default_discharge_end = '18:00'
    default_charge_temp = -3.8
    default_ntanks = 1
    default_trim_temp = 10.0
    def run(self, runner, baseline, epw, measures_only=False, run_baseline=False, **kwargs):
        charge_start = kwargs.get('charge_start', self.default_charge_start)
        charge_end = kwargs.get('charge_end', self.default_charge_end)
        discharge_start = kwargs.get('discharge_start', self.default_discharge_start)
        discharge_end = kwargs.get('discharge_end', self.default_discharge_end)
        charge_temp = kwargs.get('charge_temp', self.default_charge_temp)
        ntanks = kwargs.get('ntanks', self.default_ntanks)
        trim_temp = kwargs.get('trim_temp', self.default_trim_temp)
        if run_baseline:
            osws = [runner.osw(baseline, epw)]
            subdirs = ['baseline']
        else:
            osws = []
            subdirs = []
        osw_tes = runner.osw(baseline, epw)
        osw_tes['steps'].append({
            "measure_dir_name" : "add_pytank",
            "name" : "Add Python Tank",
            "description" : "This measure will add the Python tank model.",
            "modeler_description" : "This measure will add the Python tank model.",
            "arguments" : {
                "chrg_start" : charge_start,
                "chrg_end" : charge_end,
                "dchrg_start" : discharge_start,
                "dchrg_end" : discharge_end,
                "chrg_temp" : charge_temp,
                "num_tanks" : ntanks,
                "trim_temp" : trim_temp
            }
        })
        osws.append(osw_tes)
        subdirs.append('tes')
        runner.multirun(osws, subdirs=subdirs, measures_only=measures_only)

