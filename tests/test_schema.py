# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import stor4build as s4b
from stor4build.schema import InputDataSchema
from stor4build import __version__ as stor4build_version
import os
import json
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

# Make some assumptions
this_dir = os.path.abspath(os.path.dirname(__file__))
resources_dir = os.path.join(this_dir, '..', 'resources')
schema_path = os.path.join(this_dir, '..', 'schema', 'stor4build.json')
    
def test_minimal_input_ice():
    input_path = os.path.join(resources_dir, 'minimal-input-ice.json')
    data = s4b.InputData.read(input_path)
    assert data.baseline.type == 'LargeOffice'
    assert data.baseline.vintage == 2011
    assert data.baseline.climate == '5A'
    assert data.storage.type == 'ThermalTank-Ice'
    assert data.storage.capacity == 100.0
    assert data.energy.schedule.months['All'].month == 'All'
    assert len(data.energy.schedule.months) == 1
    assert data.demand.schedule.months['All'].month == 'All'
    assert len(data.demand.schedule.months) == 1
    assert data.storage.discharge_interval is None
    assert data.storage.charge_interval is None
    assert len(data.energy.costs) == 3
    assert data.energy.costs[3].rate > data.energy.costs[2].rate > data.energy.costs[1].rate
    assert len(data.demand.costs) == 3
    assert data.demand.costs[3].rate > data.demand.costs[2].rate > data.demand.costs[1].rate

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
    assert data.energy.schedule.months['All'].month == 'All'
    assert len(data.energy.schedule.months) == 1
    assert data.demand.schedule.months['All'].month == 'All'
    assert len(data.demand.schedule.months) == 1
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
    assert data.energy.schedule.months['All'].month == 'All'
    assert len(data.energy.schedule.months) == 1
    assert data.demand.schedule.months['All'].month == 'All'
    assert len(data.demand.schedule.months) == 1
    assert data.storage.discharge_interval is None
    assert data.storage.charge_interval is None

def test_schema_changes():
    spec = APISpec(
        title="stor4build",
        version=stor4build_version,
        openapi_version="3.0.2",
        info=dict(description="The stor4build API for TES calculations"),
        plugins=[MarshmallowPlugin()],
    )

    spec.components.schema("InputData", schema=InputDataSchema)
    current = spec.to_dict()
    with open(schema_path, 'r') as fp:
        in_repo = json.load(fp)
    assert current == in_repo

def test_utility_schedule_proc():
    test_string = '''
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
    data = json.loads(test_string)
    utility_data = s4b.schema.UtilityDataSchema().load(data)
    assert len(utility_data.costs) == 3
    assert utility_data.costs[3].period == 3
    assert utility_data.costs[3].rate == 0.2
    assert utility_data.schedule.months['All'].month == 'All'
    start,end = utility_data.schedule.months['All'].find_peak_window(3)
    assert start == 12
    assert end == 17
    rate_array = utility_data.schedule.months['All'].rate_array(utility_data.costs)
    assert len(rate_array) == 24
    assert rate_array == [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.1, 0.1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.1, 0.1, 0.01, 0.01, 0.01, 0.01, 0.01]
    
