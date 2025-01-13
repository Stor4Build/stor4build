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
    
