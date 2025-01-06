# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import stor4build as s4b
import os
import io
import pandas as pd

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
