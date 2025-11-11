# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import stor4build as s4b
import os

# Make some assumptions
this_dir = os.path.abspath(os.path.dirname(__file__))
stand_alone_retail = os.path.abspath(os.path.join(this_dir, '..', 'resources', 'StandAloneRetail-5A-2004.osm'))
measures_dir = os.path.abspath(os.path.join(this_dir, '..', 'measures'))
epw = os.path.abspath(os.path.join(this_dir, '..', 'resources', 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'))

def test_dxcoil_init():
    dxcoil = s4b.DxCoil('dxcoil')
    osw = dxcoil.osw(stand_alone_retail, measures_dir, epw)
    assert len(osw['steps']) == 2
    assert osw['steps'][0]['name'] == 'Add CSV Output'
    assert osw['steps'][0]['measure_dir_name'] == 'add_csv_output'
    assert osw['steps'][0]['arguments'] == {}
    assert len(osw['steps'][0]) == 3
    assert osw['steps'][1]['name'] == 'Add Packaged Ice Storage'
    assert osw['steps'][1]['measure_dir_name'] == 'add_packaged_ice_storage'
    assert osw['steps'][1]['arguments'] == {'ctl': 'ScheduledModes',
                                            'hourly': False,
                                            'ice_cap': 'AutoSize',
                                            'sched': 'Simple User Sched',
                                            'size_mult': '1',
                                            'wknd': False}
    assert len(osw['steps'][1]) == 3

def test_dxcoil_size():
    # Not a lot to test here, maybe more later
    pre = [s4b.Step("Add CSV Output", "add_csv_output")]
    post = []
    dxcoil = s4b.DxCoil.size('dxcoil', None, pre_steps=pre, post_steps=post)
    osw = dxcoil.osw(stand_alone_retail, measures_dir, epw)
    assert len(osw['steps']) == 3
    assert osw['steps'][0]['name'] == 'Add CSV Output'
    assert osw['steps'][0]['measure_dir_name'] == 'add_csv_output'
    assert osw['steps'][0]['arguments'] == {}
    assert len(osw['steps'][0]) == 3
    assert osw['steps'][1]['name'] == "Add CSV Output"
    assert osw['steps'][1]['measure_dir_name'] == "add_csv_output"
    assert osw['steps'][1]['arguments'] == {}
    assert len(osw['steps'][1]) == 3
    assert osw['steps'][2]['name'] == 'Add Packaged Ice Storage'
    assert osw['steps'][2]['measure_dir_name'] == 'add_packaged_ice_storage'
    assert osw['steps'][2]['arguments'] == {'ctl': 'ScheduledModes',
                                            'hourly': False,
                                            'ice_cap': 'AutoSize',
                                            'sched': 'Simple User Sched',
                                            'size_mult': '1',
                                            'wknd': False}
    assert len(osw['steps'][2]) == 3
