# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import csv
from .system import Simulation, BadSizing
import numpy as np
import pandas as pd
import math
import datetime
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
    @classmethod
    def size(cls, name, baseline_results, **kwargs):
        joules_to_kwh = 1.0e-5/36.0
        # Get the utility rate inputs
        window_start = kwargs.get('discharge_start', cls.default_discharge_start)
        window_end = kwargs.get('discharge_end', cls.default_discharge_end)
        peak_reduction = kwargs.get('peak_reduction', cls.default_discharge_end)
        
        # Figure out the window we're looking at
        k0, k1 = convert_string_time_interval(window_start, window_end)
        
        # Open the baseline csv and process it
        csv_path = os.path.join(baseline_results, 'eplusout.csv')
        df = pd.read_csv(csv_path).dropna()
        assert len(df) == 8760
        df['hour_of_day'] = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]*365
        df['ordinal_day'] = [i for i in range(1,366) for _ in range(24)]
        energy_cols = [el for el in df.columns.values.tolist() if 'Chiller Evaporator Cooling Energy' in el]
        flow_cols = [el for el in df.columns.values.tolist() if 'Chiller Evaporator Mass Flow Rate' in el]
        df = df.loc[(df['hour_of_day'] >= k0) & (df['hour_of_day'] < k1)]
        df['total_w'] = df[energy_cols].sum(axis=1)
        df['total_flow'] = df[flow_cols].sum(axis=1)
        dft = df.groupby('ordinal_day', as_index=False).agg({'total_w': 'sum', 'total_flow': 'mean'})

        index = dft['total_w'].idxmax()
        #print(dft.iloc[[dft['total_w'].idxmax()]])
        df_max = dft.iloc[[index]]
        # Could try to use the CSV for this, but would need to parse the date
        # The start year should be 2006 for all these simulations
        date = datetime.date.fromordinal(datetime.date(2006, 1, 1).toordinal() + index)
        #print(date)
        energy_max = df_max['total_w'].iat[0]
        mass_flow = df_max['total_flow'].iat[0]
        requested_capacity = energy_max * peak_reduction * 0.01
        requested_num_tanks = joules_to_kwh*requested_capacity/668.0
        actual_num_tanks = int(math.ceil(requested_num_tanks))
        actual_capacity = actual_num_tanks*668.0/joules_to_kwh
        # Compute the trim temp from Q = mCp(Ti-To)
        Cp = 4180.0 # J/(kg K)
        m = mass_flow * (k1-k0) * 3600.0  # kg
        To = 6.7 # C
        Ti = actual_capacity/(m*Cp) + To
        
        # Package up the sizing info
        sizing = {'peak_reduction': peak_reduction,
                  'window_start': window_start,
                  'window_end': window_end,
                  'maximum_load': energy_max,
                  'mass_flow': mass_flow,
                  'maximum_date': str(date),
                  'requested_num_tanks': requested_num_tanks,
                  'actual_num_tanks': actual_num_tanks,
                  'interval_start': k0,
                  'interval_end': k1,
                  'requested_capacity': requested_capacity,
                  'actual_capacity': actual_capacity,
                  'computed_trim_temperature': Ti
                  }
        # Remove any arguments that might intefere
        kwargs.pop('num_tanks', None)
        kwargs.pop('trim_temp', None)
        return cls(name, num_tanks=actual_num_tanks, trim_temp=Ti, sizing=sizing, **kwargs)
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

