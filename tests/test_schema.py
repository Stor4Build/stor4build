# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import stor4build as s4b
import os
import json

# Make some assumptions
this_dir = os.path.abspath(os.path.dirname(__file__))
resources_dir = os.path.join(this_dir, '..', 'resources')
    
def test_minimal_input_ice():
    input_path = os.path.join(resources_dir, 'minimal-input-ice.json')
    data = s4b.InputData.read(input_path)
    assert data.baseline.type == 'LargeOffice'
    assert data.baseline.vintage == 2011
    assert data.baseline.climate == '5A'
    assert data.storage.type == 'ThermalTank-Ice'
    assert data.storage.capacity == 100.0
    assert data.energy.schedule.months[0].month == 'All'
    assert data.demand.schedule.months[0].month == 'All'
    assert data.storage.discharge_interval is None
    assert data.storage.charge_interval is None

def test_intervals():
    input_path = os.path.join(resources_dir, 'minimal-input-ice.json')
    with open(input_path, 'r') as fp:
        inputs = json.load(fp)
    inputs['storage']['charge_interval'] = {'begin': {'hour': 17}, 'end': {'hour': 7}}
    inputs['storage']['discharge_interval'] = {'begin': {'hour': 11}, 'end': {'hour': 16}}
    data = s4b.InputData.load(inputs)
    assert data.baseline.type == 'LargeOffice'
    assert data.baseline.vintage == 2011
    assert data.baseline.climate == '5A'
    assert data.storage.type == 'ThermalTank-Ice'
    assert data.storage.capacity == 100.0
    assert data.energy.schedule.months[0].month == 'All'
    assert data.demand.schedule.months[0].month == 'All'
    assert data.storage.charge_interval.begin.hour == 17
    assert ('%s' % data.storage.charge_interval.begin) == '17:00'
    assert str(data.storage.charge_interval.end) == '07:00'
    assert data.storage.charge_interval.end.hour == 7
    assert data.storage.discharge_interval.begin.hour == 11
    assert data.storage.discharge_interval.end.hour == 16
    
def test_larger_input_chw():
    input_path = os.path.join(resources_dir, 'larger-input-chw.json')
    data = s4b.InputData.read(input_path)
    assert data.baseline.type == 'LargeOffice'
    assert data.baseline.vintage == 2000
    assert data.baseline.climate == '4A'
    assert data.storage.type == 'ThermalTank-ChilledWater'
    assert data.storage.capacity == 100.0
    assert data.energy.schedule.months[0].month == 'All'
    assert data.demand.schedule.months[0].month == 'All'
    assert data.storage.discharge_interval is None
    assert data.storage.charge_interval is None
    
