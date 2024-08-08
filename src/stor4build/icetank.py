# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import csv
from .system import Simulation, BadSizing
import numpy as np
import math
from .util import convert_string_time_interval

class IceTank(Simulation):
    default_charge_start = '21:00'
    default_charge_end = '07:00'
    default_discharge_start = '12:00'
    default_discharge_end = '18:00'
    default_charge_temp = -3.8
    default_num_tanks = 1
    default_trim_temp = 10.0
    default_peak_reduction = 15.0
    def __init__(self, name, **kwargs):
        super().__init__(name)
        self.charge_start = kwargs.get('charge_start', self.default_charge_start)
        self.charge_end = kwargs.get('charge_end', self.default_charge_end)
        self.discharge_start = kwargs.get('discharge_start', self.default_discharge_start)
        self.discharge_end = kwargs.get('discharge_end', self.default_discharge_end)
        self.charge_temp = kwargs.get('charge_temp', self.default_charge_temp)
        self.num_tanks = kwargs.get('num_tanks', self.default_num_tanks)
        self.trim_temp = kwargs.get('trim_temp', self.default_trim_temp)
        self.sizing = kwargs.get('sizing', {})
        self.peak_reduction = kwargs.get('peak_reduction')
    @classmethod
    def size(cls, name, baseline_results, **kwargs):
        joules_to_kwh = 1.0e-5/36.0
        # Get the utility rate inputs
        window_start = kwargs.get('window_start', cls.default_discharge_start)
        window_end = kwargs.get('window_end', cls.default_discharge_end)
        peak_reduction = kwargs.get('peak_reduction', cls.default_discharge_end)
        
        # Figure out the window we're looking at
        k0, k1 = convert_string_time_interval(window_start, window_end)
        
        # Open the baseline csv and process it
        # This code is all pretty terrible and needs to be cleaned up
        with open(os.path.join(baseline_results, 'eplusout.csv'), 'r') as fp:
            reader = csv.reader(fp)
            header = next(reader)
            indices = []
            for col,title in enumerate(header):
                if 'Chiller Evaporator Cooling Energy' in title:
                    indices.append(col)
            assert len(indices) > 1
            print(indices)
            results = []
            datetime = []
            for data in reader:
                try:
                    results.append(sum([float(data[el]) for el in indices]))
                    datetime.append(data[0])
                except ValueError:
                    pass
        print(len(results))
        assert len(results) == 8760
        v = np.array(results)
        daily_sum = np.reshape(v, (365, 24))[:,k0:k1].sum(axis=1)
        print(daily_sum.shape)
        assert daily_sum.shape == (365,)
        max_sum = np.max(daily_sum)
        capacity = max_sum * peak_reduction * 0.01
        index = np.where(daily_sum == max_sum)
        print(index[0][0], joules_to_kwh*max_sum/668.0)
        num_tanks_float = joules_to_kwh*max_sum/668.0
        num_tanks = math.ceil(num_tanks_float)
        
        # Compute the trim temp
        trim_temp = 10.0
        
        # Package up the sizing info
        sizing = {'peak_reduction': peak_reduction,
                  'window_start': window_start,
                  'window_end': window_end,
                  'maximum_load': max_sum,
                  'maximum_datetime': datetime[24*index[0][0]],
                  'num_tanks': num_tanks_float,
                  'interval_start': k0,
                  'interval_end': k1,
                  'capacity': capacity}
        # Remove any arguments that might intefere
        kwargs.pop('num_tanks', None)
        kwargs.pop('trim_temp', None)
        return cls(name, num_tanks=num_tanks, trim_temp=trim_temp, sizing=sizing, **kwargs)
    def needs_baseline(self):
        return self.num_tanks is None or self.trim_temp is None
    def osw(self, seed_file, measures_directory, epw_file, **kwargs):
        if self.num_tanks is None or self.trim_temp is None:
            return None
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

