import os
import stor4build as s4b
import pytest as pt

# Make some assumptions
this_dir = os.path.abspath(os.path.dirname(__file__))
results_dir = os.path.join(this_dir, '..', 'resources', 'LargeOfficeCSV')

def test_100pct_sizing():
    icetank = s4b.IceTank.size('icetank', results_dir, peak_reduction=100.0, csv='full-year-baseline.csv')
    assert icetank.sizing['peak_reduction'] == 100.0
    assert icetank.sizing['actual_num_tanks'] == 18
    assert icetank.sizing['maximum_date'] == '2006-08-09'
    assert icetank.sizing['window_start'] == '12:00'
    assert icetank.sizing['window_end'] == '18:00'
    assert icetank.sizing['maximum_load'] == pt.approx(43054516220.4075, abs=1.0e-8)
    assert icetank.sizing['mass_flow'] == pt.approx(124.23959898908693, abs=1.0e-8)
    assert icetank.sizing['requested_num_tanks'] == pt.approx(17.903574609284558, abs=1.0e-8)
    assert icetank.sizing['interval_start'] == 12
    assert icetank.sizing['interval_end'] == 18
    assert icetank.sizing['requested_capacity'] == pt.approx(43054516220.4075, abs=1.0e-8)
    assert icetank.sizing['actual_capacity'] == pt.approx(43286399999.99999, abs=1.0e-8)
    assert icetank.sizing['computed_trim_temperature'] == pt.approx(10.558881075128763, abs=1.0e-8)
    
def test_100pct_sizing_cooling():
    icetank = s4b.IceTank.size('icetank', results_dir, peak_reduction=100.0, csv='cooling-baseline.csv')
    assert icetank.sizing['peak_reduction'] == 100.0
    assert icetank.sizing['actual_num_tanks'] == 18
    assert icetank.sizing['maximum_date'] == '2006-08-09'
    assert icetank.sizing['window_start'] == '12:00'
    assert icetank.sizing['window_end'] == '18:00'
    assert icetank.sizing['maximum_load'] == pt.approx(42615337308.797195, abs=1.0e-8)
    assert icetank.sizing['mass_flow'] == pt.approx(124.239598989087, abs=1.0e-8)
    assert icetank.sizing['requested_num_tanks'] == pt.approx(17.720948648036092, abs=1.0e-8)
    assert icetank.sizing['interval_start'] == 12
    assert icetank.sizing['interval_end'] == 18
    assert icetank.sizing['requested_capacity'] == pt.approx(42615337308.797195, abs=1.0e-8)
    assert icetank.sizing['actual_capacity'] == pt.approx(43286399999.99999, abs=1.0e-8)
    assert icetank.sizing['computed_trim_temperature'] == pt.approx(10.558881075128763, abs=1.0e-8)
    
def test_50pct_sizing():
    icetank = s4b.IceTank.size('icetank', results_dir, peak_reduction=50.0, csv='full-year-baseline.csv')
    assert icetank.sizing['peak_reduction'] == 50.0
    assert icetank.sizing['actual_num_tanks'] == 9
    assert icetank.sizing['maximum_date'] == '2006-08-09'
    assert icetank.sizing['window_start'] == '12:00'
    assert icetank.sizing['window_end'] == '18:00'
    assert icetank.sizing['maximum_load'] == pt.approx(43054516220.4075, abs=1.0e-8)
    assert icetank.sizing['mass_flow'] == pt.approx(124.23959898908693, abs=1.0e-8)
    assert icetank.sizing['requested_num_tanks'] == pt.approx(8.951787304642279, abs=1.0e-8)
    assert icetank.sizing['interval_start'] == 12
    assert icetank.sizing['interval_end'] == 18
    assert icetank.sizing['requested_capacity'] == pt.approx(21527258110.20375, abs=1.0e-8)
    assert icetank.sizing['actual_capacity'] == pt.approx(21643199999.999996, abs=1.0e-8)
    assert icetank.sizing['computed_trim_temperature'] == pt.approx(8.629440537564381, abs=1.0e-8)

