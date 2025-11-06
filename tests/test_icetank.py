# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import stor4build as s4b
import pytest as pt

# Make some assumptions
this_dir = os.path.abspath(os.path.dirname(__file__))
results_dir = os.path.join(this_dir, '..', 'resources', 'LargeOfficeCSV')
large_office = os.path.abspath(os.path.join(this_dir, '..', 'resources', 'LargeOffice.osm'))
measures_dir = os.path.abspath(os.path.join(this_dir, '..', 'measures'))
epw = os.path.abspath(os.path.join(this_dir, '..', 'resources', 'USA_TN_Knoxville-McGhee.Tyson.AP.723260_TMY3.epw'))

def test_100pct_sizing():
    icetank = s4b.IceTank.size('icetank', results_dir, peak_reduction=100.0, csv='full-year-baseline.csv')
    assert icetank.size_fraction == 1
    assert icetank.store_ice
    assert icetank.charge_temp == s4b.IceTank.default_ice_charge_temp
    assert icetank.sizing['peak_reduction'] == 100.0
    assert icetank.sizing['actual_num_tanks'] == 18
    assert icetank.sizing['maximum_date'] == '2006-08-09'
    assert icetank.sizing['peak_window_start'] == '12:00'
    assert icetank.sizing['peak_window_end'] == '18:00'
    assert icetank.sizing['maximum_load'] == pt.approx(43054516220.4075, abs=1.0e-8)
    assert icetank.sizing['mass_flow'] == pt.approx(124.23959898908693, abs=1.0e-8)
    assert icetank.sizing['requested_num_tanks'] == pt.approx(17.903574609284558, abs=1.0e-8)
    assert icetank.sizing['interval_start'] == 12
    assert icetank.sizing['interval_end'] == 18
    assert icetank.sizing['requested_capacity'] == pt.approx(43054516220.4075, abs=1.0e-8)
    assert icetank.sizing['actual_capacity'] == pt.approx(43286399999.99999, abs=1.0e-8)
    assert icetank.sizing['computed_trim_temperature'] == pt.approx(10.558881075128763, abs=1.0e-8)
    osw = icetank.osw(large_office, measures_dir, epw)
    assert osw is not None
    assert 'seed_file' in osw
    assert osw['seed_file'] == large_office
    assert 'weather_file' in osw
    assert osw['weather_file'] == epw
    assert len(osw['steps']) == 2
    assert osw['steps'][0]['name'] == 'Add CSV Output'
    assert osw['steps'][0]['measure_dir_name'] == 'add_csv_output'
    assert osw['steps'][0]['arguments'] == {}
    assert len(osw['steps'][0]) == 3
    assert osw['steps'][1]['name'] == 'Add Python Tank'
    assert osw['steps'][1]['measure_dir_name'] == 'add_pytank'
    assert len(osw['steps'][1]['arguments']) == 9
    assert 'chrg_start' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['chrg_start'] == s4b.IceTank.default_charge_start
    assert 'chrg_end' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['chrg_end'] == s4b.IceTank.default_charge_end
    assert 'dchrg_start' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['dchrg_start'] == s4b.IceTank.default_discharge_start
    assert 'dchrg_end' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['dchrg_end'] == s4b.IceTank.default_discharge_end
    assert 'chrg_temp' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['chrg_temp'] == s4b.IceTank.default_ice_charge_temp
    assert 'num_tanks' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['num_tanks'] == 18
    assert 'trim_temp' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['trim_temp'] == 10.558881075128763
    assert 'strg_type' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['strg_type'] == 'ice'
    assert len(osw['steps'][1]) == 3
    
def test_100pct_sizing_cooling():
    icetank = s4b.IceTank.size('icetank', results_dir, peak_reduction=100.0, csv='cooling-baseline.csv')
    assert icetank.size_fraction == 1
    assert icetank.sizing['peak_reduction'] == 100.0
    assert icetank.sizing['actual_num_tanks'] == 18
    assert icetank.sizing['maximum_date'] == '2006-08-09'
    assert icetank.sizing['peak_window_start'] == '12:00'
    assert icetank.sizing['peak_window_end'] == '18:00'
    assert icetank.sizing['maximum_load'] == pt.approx(42615337308.797195, abs=1.0e-8)
    assert icetank.sizing['mass_flow'] == pt.approx(124.239598989087, abs=1.0e-8)
    assert icetank.sizing['requested_num_tanks'] == pt.approx(17.720948648036092, abs=1.0e-8)
    assert icetank.sizing['interval_start'] == 12
    assert icetank.sizing['interval_end'] == 18
    assert icetank.sizing['requested_capacity'] == pt.approx(42615337308.797195, abs=1.0e-8)
    assert icetank.sizing['actual_capacity'] == pt.approx(43286399999.99999, abs=1.0e-8)
    assert icetank.sizing['computed_trim_temperature'] == pt.approx(10.558881075128763, abs=1.0e-8)
    osw = icetank.osw(large_office, measures_dir, epw)
    assert osw is not None
    assert 'seed_file' in osw
    assert osw['seed_file'] == large_office
    assert 'weather_file' in osw
    assert osw['weather_file'] == epw
    assert len(osw['steps']) == 2
    assert osw['steps'][0]['name'] == 'Add CSV Output'
    assert osw['steps'][0]['measure_dir_name'] == 'add_csv_output'
    assert osw['steps'][0]['arguments'] == {}
    assert len(osw['steps'][0]) == 3
    assert osw['steps'][1]['name'] == 'Add Python Tank'
    assert osw['steps'][1]['measure_dir_name'] == 'add_pytank'
    assert len(osw['steps'][1]['arguments']) == 9
    assert 'chrg_start' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['chrg_start'] == s4b.IceTank.default_charge_start
    assert 'chrg_end' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['chrg_end'] == s4b.IceTank.default_charge_end
    assert 'dchrg_start' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['dchrg_start'] == s4b.IceTank.default_discharge_start
    assert 'dchrg_end' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['dchrg_end'] == s4b.IceTank.default_discharge_end
    assert 'chrg_temp' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['chrg_temp'] == s4b.IceTank.default_ice_charge_temp
    assert 'num_tanks' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['num_tanks'] == 18
    assert 'trim_temp' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['trim_temp'] == 10.558881075128763
    assert 'strg_type' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['strg_type'] == 'ice'
    assert len(osw['steps'][1]) == 3
    
def test_50pct_sizing():
    post = [s4b.Step('Run Cooling Season Only', 'run_cooling_season_only')]
    icetank = s4b.IceTank.size('icetank', results_dir, peak_reduction=50.0, post_steps=post, csv='full-year-baseline.csv')
    assert icetank.size_fraction == 1
    assert icetank.sizing['peak_reduction'] == 50.0
    assert icetank.sizing['actual_num_tanks'] == 9
    assert icetank.sizing['maximum_date'] == '2006-08-09'
    assert icetank.sizing['peak_window_start'] == '12:00'
    assert icetank.sizing['peak_window_end'] == '18:00'
    assert icetank.sizing['maximum_load'] == pt.approx(43054516220.4075, abs=1.0e-8)
    assert icetank.sizing['mass_flow'] == pt.approx(124.23959898908693, abs=1.0e-8)
    assert icetank.sizing['requested_num_tanks'] == pt.approx(8.951787304642279, abs=1.0e-8)
    assert icetank.sizing['interval_start'] == 12
    assert icetank.sizing['interval_end'] == 18
    assert icetank.sizing['requested_capacity'] == pt.approx(21527258110.20375, abs=1.0e-8)
    assert icetank.sizing['actual_capacity'] == pt.approx(21643199999.999996, abs=1.0e-8)
    assert icetank.sizing['computed_trim_temperature'] == pt.approx(8.629440537564381, abs=1.0e-8)
    osw = icetank.osw(large_office, measures_dir, epw)
    assert osw is not None
    assert 'seed_file' in osw
    assert osw['seed_file'] == large_office
    assert 'weather_file' in osw
    assert osw['weather_file'] == epw
    assert len(osw['steps']) == 3
    assert osw['steps'][0]['name'] == 'Add CSV Output'
    assert osw['steps'][0]['measure_dir_name'] == 'add_csv_output'
    assert osw['steps'][0]['arguments'] == {}
    assert len(osw['steps'][0]) == 3
    assert osw['steps'][1]['name'] == 'Add Python Tank'
    assert osw['steps'][1]['measure_dir_name'] == 'add_pytank'
    assert len(osw['steps'][1]['arguments']) == 9
    assert 'chrg_start' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['chrg_start'] == s4b.IceTank.default_charge_start
    assert 'chrg_end' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['chrg_end'] == s4b.IceTank.default_charge_end
    assert 'dchrg_start' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['dchrg_start'] == s4b.IceTank.default_discharge_start
    assert 'dchrg_end' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['dchrg_end'] == s4b.IceTank.default_discharge_end
    assert 'chrg_temp' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['chrg_temp'] == s4b.IceTank.default_ice_charge_temp
    assert 'num_tanks' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['num_tanks'] == 9
    assert 'trim_temp' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['trim_temp'] == 8.629440537564381
    assert 'strg_type' in osw['steps'][1]['arguments']
    assert osw['steps'][1]['arguments']['strg_type'] == 'ice'
    assert len(osw['steps'][1]) == 3
    assert osw['steps'][2]['name'] == 'Run Cooling Season Only'
    assert osw['steps'][2]['measure_dir_name'] == 'run_cooling_season_only'
    assert osw['steps'][2]['arguments'] == {}
    assert len(osw['steps'][2]) == 3

