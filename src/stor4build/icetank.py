# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import os
from .system import Simulation
import pandas as pd
import math
import datetime
from .util import convert_string_time_interval
from .osmeasures import Step

class IceTank(Simulation):
    default_charge_start = '21:00'
    default_charge_end = '07:00'
    default_discharge_start = '12:00'
    default_discharge_end = '18:00'
    default_ice_charge_temp = -3.8
    default_chw_charge_temp = 1.1
    default_num_tanks = 1
    default_trim_temp = 10.0
    default_peak_reduction = 100.0
    default_size_fraction = 1.0
    default_store_ice = True
    def __init__(self, name, pre_steps=None, post_steps=None, **kwargs):
        # Get all the data first
        self.charge_start = kwargs.get('charge_start', self.default_charge_start)
        self.charge_end = kwargs.get('charge_end', self.default_charge_end)
        self.discharge_start = kwargs.get('discharge_start', self.default_discharge_start)
        self.discharge_end = kwargs.get('discharge_end', self.default_discharge_end)
        self.num_tanks = kwargs.get('num_tanks', self.default_num_tanks)
        self.trim_temp = kwargs.get('trim_temp', self.default_trim_temp)
        self.size_fraction = kwargs.get('size_fraction', self.default_size_fraction)
        self.store_ice = kwargs.get('store_ice', self.default_store_ice)
        if 'charge_temp' in kwargs:
            self.charge_temp = kwargs['charge_temp']
        else:
            self.charge_temp = {True: self.default_ice_charge_temp, False: self.default_chw_charge_temp}[self.store_ice]
        self.sizing = kwargs.get('sizing', {})
        super().__init__(name, pre_steps=pre_steps, post_steps=post_steps)
    def required_steps(self):
        return [Step('Add Python Tank', 'add_pytank',
                     arguments={
                         "chrg_start": self.charge_start,
                         "chrg_end": self.charge_end,
                         "dchrg_start": self.discharge_start,
                         "dchrg_end": self.discharge_end,
                         "chrg_temp": {True: self.default_ice_charge_temp, False: self.default_chw_charge_temp}[self.store_ice],
                         "num_tanks": self.num_tanks,
                         "trim_temp": self.trim_temp,
                         "size_frac": self.size_fraction,
                         "strg_type": {True: "ice", False: "chw"}[self.store_ice]
                     })]
    @classmethod
    def size(cls, name, baseline_results, **kwargs):
        joules_to_kwh = 1.0e-5/36.0
        # Get the CSV file name to use
        csvfile = kwargs.get('csv', 'eplusout.csv')
        # Get the utility rate inputs
        window_start = kwargs.get('discharge_start', cls.default_discharge_start)
        window_end = kwargs.get('discharge_end', cls.default_discharge_end)
        peak_reduction = kwargs.get('peak_reduction', cls.default_peak_reduction)
        store_ice = kwargs.get('store_ice', cls.default_store_ice)
        
        # Figure out the window we're looking at
        k0, k1 = convert_string_time_interval(window_start, window_end)
        
        # Open the baseline csv and process it
        csv_path = os.path.join(baseline_results, csvfile)
        df = pd.read_csv(csv_path).dropna()
        # Figure out how much of the year is there
        jan1 = datetime.date(month=1, day=1, year=2006).toordinal()
        start_datetime = datetime.datetime.fromisoformat(df['Date/Time'][0].strip())
        start = start_datetime.date().toordinal() - jan1 + 1
        end_datetime = datetime.datetime.fromisoformat(df['Date/Time'].iat[-1].strip())
        end = end_datetime.date().toordinal() - jan1 + 1
        #start = datetime.date(month=1, day=1, year=2006).toordinal() - jan1 + 1
        #end = datetime.date(month=12, day=31, year=2006).toordinal() - jan1 + 1
        numdays = end - start + 1
        # Could perhaps just use the datetimes, will need to do that if the resolution is refined
        df['hour_of_day'] = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]*numdays
        df['ordinal_day'] = [i for i in range(start, end+1) for _ in range(24)]
        energy_cols = [el for el in df.columns.values.tolist() if 'Chiller Evaporator Cooling Energy' in el]
        flow_cols = [el for el in df.columns.values.tolist() if 'Chiller Evaporator Mass Flow Rate' in el]
        df = df.loc[(df['hour_of_day'] >= k0) & (df['hour_of_day'] < k1)]
        df['total_w'] = df[energy_cols].sum(axis=1)
        df['total_flow'] = df[flow_cols].sum(axis=1)
        dft = df.groupby('ordinal_day', as_index=False).agg({'total_w': 'sum', 'total_flow': 'mean'})

        index = dft['total_w'].idxmax()
        df_max = dft.iloc[[index]]
        # Could try to use the CSV for this, but would need to parse the date
        # The start year should be 2006 for all these simulations
        date = datetime.date.fromordinal(jan1 + start + index - 1)
        # Compute what we need
        energy_max = df_max['total_w'].iat[0]
        mass_flow = df_max['total_flow'].iat[0]
        requested_capacity = energy_max * peak_reduction * 0.01
        requested_num_tanks = joules_to_kwh*requested_capacity/668.0
        actual_num_tanks = int(math.ceil(requested_num_tanks))
        actual_capacity = actual_num_tanks*668.0/joules_to_kwh
        # Compute the trim temp from Q = mCp(Ti-To), need to add division by zero protection etc.
        Cp = 4180.0 # J/(kg K)
        m = mass_flow * (k1-k0) * 3600.0  # kg
        To = 6.7 # C
        Ti = actual_capacity/(m*Cp) + To
        
        # Package up the sizing info
        sizing = {'peak_reduction': peak_reduction,
                  'peak_window_start': window_start,
                  'peak_window_end': window_end,
                  'maximum_load': energy_max,
                  'mass_flow': mass_flow,
                  'maximum_date': str(date),
                  'requested_num_tanks': requested_num_tanks,
                  'actual_num_tanks': actual_num_tanks,
                  'interval_start': k0,
                  'interval_end': k1,
                  'requested_capacity': requested_capacity,
                  'actual_capacity': actual_capacity,
                  'computed_trim_temperature': Ti,
                  'storage_type': {True: 'ice', False:'chw'}[store_ice]
                  }
        # Remove any arguments that might intefere
        kwargs.pop('num_tanks', None)
        kwargs.pop('trim_temp', None)
        return cls(name, num_tanks=actual_num_tanks, trim_temp=Ti, sizing=sizing, **kwargs)
    def osw(self, seed_file, measures_directory, epw_file):
        if self.num_tanks is None or self.trim_temp is None:
            return None
        return super().osw(seed_file, measures_directory, epw_file)

