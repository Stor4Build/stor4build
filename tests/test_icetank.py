# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import stor4build as s4b
import pytest as pt

# Make some assumptions
this_dir = os.path.abspath(os.path.dirname(__file__))
results_dir = os.path.join(this_dir, 'csv')
large_office = os.path.abspath(os.path.join('not', 'a', 'real', 'model', 'LargeOffice.osm'))
measures_dir = os.path.abspath(os.path.join(this_dir, '..', 'measures'))
epw = os.path.abspath(os.path.join(this_dir, '..', 'resources', 'USA_TN_Knoxville-McGhee.Tyson.AP.723260_TMY3.epw'))


def assert_pytank_steps(osw, control_index, system_index, icetank):
    control_step = osw['steps'][control_index]
    assert control_step['name'] == 'Add Python Tank Control Schedules'
    assert control_step['measure_dir_name'] == 'add_pytank_control_schedules'
    assert control_step['arguments'] == {
        'chrg_start': s4b.IceTankControl.default_charge_start,
        'chrg_end': s4b.IceTankControl.default_charge_end,
        'dchrg_start': s4b.IceTankControl.default_discharge_start,
        'dchrg_end': s4b.IceTankControl.default_discharge_end,
        'chrg_temp': icetank.control.charge_temp,
    }
    assert len(control_step) == 3

    system_step = osw['steps'][system_index]
    assert system_step['name'] == 'Add Python Tank System'
    assert system_step['measure_dir_name'] == 'add_pytank_system'
    assert system_step['arguments'] == {
        'chrg_temp': icetank.control.charge_temp,
        'num_tanks': icetank.num_tanks,
        'trim_temp': icetank.trim_temp,
        'size_frac': icetank.size_fraction,
        'strg_type': 'ice',
        'strg_medium': icetank.storage_medium,
        'custom_site_packages': icetank.custom_site_packages,
    }
    assert len(system_step) == 3


def test_100pct_sizing():
    icetank = s4b.IceTank.size('icetank', results_dir, peak_reduction=100.0, csv='full-year-baseline.csv')
    assert icetank.size_fraction == 1
    assert icetank.store_ice
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
    assert len(osw['steps']) == 3
    assert osw['steps'][0]['name'] == 'Add CSV Output'
    assert osw['steps'][0]['measure_dir_name'] == 'add_csv_output'
    assert osw['steps'][0]['arguments'] == {}
    assert len(osw['steps'][0]) == 3
    assert_pytank_steps(osw, 1, 2, icetank)
    
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
    assert len(osw['steps']) == 3
    assert osw['steps'][0]['name'] == 'Add CSV Output'
    assert osw['steps'][0]['measure_dir_name'] == 'add_csv_output'
    assert osw['steps'][0]['arguments'] == {}
    assert len(osw['steps'][0]) == 3
    assert_pytank_steps(osw, 1, 2, icetank)
    
def test_50pct_sizing():
    post = [s4b.ModelMeasure('Run Cooling Season Only', 'run_cooling_season_only')]
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
    assert len(osw['steps']) == 4
    assert osw['steps'][0]['name'] == 'Add CSV Output'
    assert osw['steps'][0]['measure_dir_name'] == 'add_csv_output'
    assert osw['steps'][0]['arguments'] == {}
    assert len(osw['steps'][0]) == 3
    assert_pytank_steps(osw, 2, 3, icetank)
    assert len(osw['steps'][1]) == 3
    assert osw['steps'][1]['name'] == 'Run Cooling Season Only'
    assert osw['steps'][1]['measure_dir_name'] == 'run_cooling_season_only'
    assert osw['steps'][1]['arguments'] == {}
    assert len(osw['steps'][1]) == 3
    
def test_50pct_sizing_simplewater():
    post = [s4b.ModelMeasure('Run Cooling Season Only', 'run_cooling_season_only')]
    icetank = s4b.IceTank.size('icetank', results_dir, peak_reduction=50.0, post_steps=post, csv='full-year-baseline.csv', storage_medium='simplewater')
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
    assert icetank.sizing['computed_trim_temperature'] == pt.approx(8.627595948140323, abs=1.0e-8)
    osw = icetank.osw(large_office, measures_dir, epw)
    assert osw is not None
    assert 'seed_file' in osw
    assert osw['seed_file'] == large_office
    assert 'weather_file' in osw
    assert osw['weather_file'] == epw
    assert len(osw['steps']) == 4
    assert osw['steps'][0]['name'] == 'Add CSV Output'
    assert osw['steps'][0]['measure_dir_name'] == 'add_csv_output'
    assert osw['steps'][0]['arguments'] == {}
    assert len(osw['steps'][0]) == 3
    assert_pytank_steps(osw, 2, 3, icetank)
    assert len(osw['steps'][1]) == 3
    assert osw['steps'][1]['name'] == 'Run Cooling Season Only'
    assert osw['steps'][1]['measure_dir_name'] == 'run_cooling_season_only'
    assert osw['steps'][1]['arguments'] == {}
    
def test_50pct_sizing_pcm2x2a():
    post = [s4b.ModelMeasure('Run Cooling Season Only', 'run_cooling_season_only')]
    icetank = s4b.IceTank.size('icetank', results_dir, peak_reduction=50.0, post_steps=post, csv='full-year-baseline.csv', storage_medium='pcm2x2a')
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
    assert icetank.sizing['computed_trim_temperature'] == pt.approx(10.732530723509557, abs=1.0e-8)
    osw = icetank.osw(large_office, measures_dir, epw)
    assert osw is not None
    assert 'seed_file' in osw
    assert osw['seed_file'] == large_office
    assert 'weather_file' in osw
    assert osw['weather_file'] == epw
    assert len(osw['steps']) == 4
    assert osw['steps'][0]['name'] == 'Add CSV Output'
    assert osw['steps'][0]['measure_dir_name'] == 'add_csv_output'
    assert osw['steps'][0]['arguments'] == {}
    assert len(osw['steps'][0]) == 3
    assert_pytank_steps(osw, 2, 3, icetank)
    assert len(osw['steps'][1]) == 3
    assert osw['steps'][1]['name'] == 'Run Cooling Season Only'
    assert osw['steps'][1]['measure_dir_name'] == 'run_cooling_season_only'
    assert osw['steps'][1]['arguments'] == {}


