# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import stor4build as s4b
import os
import io
import pandas as pd
from dataclasses import dataclass
import datetime
import json

# Make some assumptions
this_dir = os.path.abspath(os.path.dirname(__file__))
results_dir = os.path.join(this_dir, '..', 'resources', 'LargeOfficeCSV')

int_schedule = [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 2, 2, 1, 1, 1, 1, 1]
too_early_int_schedule = [3, 3, 3, 3, 3, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2]
too_late_int_schedule = [2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3]

def test_process_int_schedule():
    results = s4b.process_energy_schedule(int_schedule)
    assert len(results) == 4
    assert results[0] == '18:00'
    assert results[1] == '11:00'
    assert results[2] == '12:00'
    assert results[3] == '17:00'
    results = s4b.process_energy_schedule(too_early_int_schedule)
    assert len(results) == 4
    assert results[0] == '07:00'
    assert results[1] == '24:00'
    assert results[2] == '01:00'
    assert results[3] == '06:00'
    results = s4b.process_energy_schedule(too_late_int_schedule)
    assert len(results) == 4
    assert results[0] == '01:00'
    assert results[1] == '18:00'
    assert results[2] == '19:00'
    assert results[3] == '24:00'

def test_intervals():
    vec = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    
    start = '12:00'
    end = '18:00'
    i0, i1 = s4b.convert_string_time_interval(start, end)
    assert i0 == 12
    assert i1 == 18
    assert vec[i0:i1] == [12, 13, 14, 15, 16, 17]
    
    start = '18:00'
    end = '24:00'
    i0, i1 = s4b.convert_string_time_interval(start, end)
    assert i0 == 18
    assert i1 == 24
    assert vec[i0:i1] == [18, 19, 20, 21, 22, 23]
    
def test_combine_csvs():
    baseline_path = os.path.join(results_dir, 'cooling-baseline.csv')
    with open(baseline_path, 'r') as fp:
        baseline_df = pd.read_csv(fp)
    assert len(baseline_df) == 4392
    icetank_path = os.path.join(results_dir, 'cooling-icetank.csv')
    with open(icetank_path, 'r') as fp:
        icetank_df = pd.read_csv(fp)
    assert len(icetank_df) == 4392
    combined_txt = s4b.combine_csvs(baseline_path, icetank_path)
    combined_df = pd.read_csv(io.StringIO(combined_txt))
    assert len(combined_df) == 4392
    assert len(combined_df.columns) == len(baseline_df.columns) + len(icetank_df.columns) - 1

def test_combine_hourly_dfs():
    utility_string = '''
{
    "costs": [
        {
            "rate": 0.2,
            "unit": "$/kWh",
            "period": 3
        },
        {
            "rate": 0.1,
            "unit": "$/kWh",
            "period": 2
        },
        {
            "rate": 0.01,
            "unit": "$/kWh",
            "period": 1
        }
    ],
    "schedule": {
        "months": [
            {
                "unit": "hour",
                "month": "All",
                "periods": [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 3, 3, 2, 2, 1, 1, 1, 1, 1]
            }
        ]
    }
}
'''
    baseline_path = os.path.join(this_dir, 'baseline_ice_4A_2011.csv')
    with open(baseline_path, 'r') as fp:
        baseline_df = pd.read_csv(fp)
    assert len(baseline_df) == 4392
    baseline_d1 = s4b.get_first_day(baseline_df)
    assert baseline_d1 == datetime.date(2006, 4, 1)
    baseline_dn = s4b.get_last_day(baseline_df)
    assert baseline_dn == datetime.date(2006, 9, 30)
    icetank_path = os.path.join(this_dir, 'tes_ice_4A_2011.csv')
    with open(icetank_path, 'r') as fp:
        icetank_df = pd.read_csv(fp)
    assert len(icetank_df) == 4392
    icetank_d1 = s4b.get_first_day(icetank_df)
    assert icetank_d1 == baseline_d1
    icetank_dn = s4b.get_last_day(icetank_df)
    assert icetank_dn == baseline_dn
    
    combined_df = s4b.combine_single_frequency_df(baseline_path, icetank_path, 'Hourly', energy_data=None)
    assert len(combined_df) == 4392
    assert len(combined_df.columns) == len(baseline_df.columns) + len(icetank_df.columns) - 1
    
    energy_data = s4b.schema.UtilityDataSchema().load(json.loads(utility_string))
    assert len(energy_data.costs) == 3
    combined_df = s4b.combine_single_frequency_df(baseline_path, icetank_path, 'Hourly', energy_data=energy_data)
    assert len(combined_df) == 4392
    assert len(combined_df.columns) == len(baseline_df.columns) + len(icetank_df.columns)
    assert (combined_df['energy rate [$/kWh]'].iloc[:24] == [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.1, 0.1, 0.01, 0.01, 0.01, 0.01, 0.01]).all()
    assert (combined_df['energy rate [$/kWh]'].iloc[24:48] == [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.1, 0.1, 0.01, 0.01, 0.01, 0.01, 0.01]).all()
    
    # Pretend that the data is demand, doesn't really matter
    periods = energy_data.demand_schedule(baseline_d1, baseline_d1) # + datetime.timedelta(days=1))
    assert len(periods) == 24
    assert periods == [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 0, 0, 0, 0, 0]

def test_combine_hourly_csvs():
    baseline_path = os.path.join(this_dir, 'baseline_ice_4A_2011.csv')
    with open(baseline_path, 'r') as fp:
        baseline_df = pd.read_csv(fp)
    assert len(baseline_df) == 4392
    baseline_d1 = s4b.get_first_day(baseline_df)
    assert baseline_d1 == datetime.date(2006, 4, 1)
    baseline_dn = s4b.get_last_day(baseline_df)
    assert baseline_dn == datetime.date(2006, 9, 30)
    icetank_path = os.path.join(this_dir, 'tes_ice_4A_2011.csv')
    with open(icetank_path, 'r') as fp:
        icetank_df = pd.read_csv(fp)
    assert len(icetank_df) == 4392
    icetank_d1 = s4b.get_first_day(icetank_df)
    assert icetank_d1 == baseline_d1
    icetank_dn = s4b.get_last_day(icetank_df)
    assert icetank_dn == baseline_dn
    
    combined_csv = s4b.combine_single_frequency_csv(baseline_path, icetank_path, 'Hourly', energy_data=None)
    combined_df = pd.read_csv(io.StringIO(combined_csv))
    assert len(combined_df) == 4392
    assert len(combined_df.columns) == len(baseline_df.columns) + len(icetank_df.columns) - 1

def test_rates():
    @dataclass
    class LocalCost:
        rate:float
        unit:str
    costs = {1: LocalCost(rate=0.01, unit='$/kWh'), 2: LocalCost(rate=0.1, unit='$/kWh'), 3: LocalCost(rate=0.2, unit='$/kWh')}
    costs = {1: 0.01, 2: 0.1, 3: 0.2}
    rate_array = s4b.rate_array(int_schedule, costs)
    assert len(rate_array) == 24
    assert rate_array == [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.1, 0.1, 0.01, 0.01, 0.01, 0.01, 0.01]
    
    
