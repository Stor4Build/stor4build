import os
import stor4build as s4b

# Make some assumptions
this_dir = os.path.abspath(os.path.dirname(__file__))
results_dir = os.path.join(this_dir, '..', 'resources', 'LargeOfficeCSV')

def test_100pct_sizing():
    icetank = s4b.IceTank.size('icetank', results_dir, peak_reduction=100.0)
    assert icetank.sizing['peak_reduction'] == 100.0
    assert icetank.sizing['actual_num_tanks'] == 18
    
def test_50pct_sizing():
    icetank = s4b.IceTank.size('icetank', results_dir, peak_reduction=50.0)
    assert icetank.sizing['peak_reduction'] == 50.0
    assert icetank.sizing['actual_num_tanks'] == 9

