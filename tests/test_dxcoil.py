# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import stor4build as s4b
import os
from click.testing import CliRunner

from stor4build.cli import run_dxcoil

# Make some assumptions
this_dir = os.path.abspath(os.path.dirname(__file__))
stand_alone_retail = os.path.abspath(os.path.join(this_dir, '..', 'models', 'RetailStandalone_5A_2016.osm'))
measures_dir = os.path.abspath(os.path.join(this_dir, '..', 'measures'))
epw = os.path.abspath(os.path.join(this_dir, '..', 'weather', 'USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw'))

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
    pre = [s4b.ModelMeasure("Add CSV Output", "add_csv_output")]
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


def test_dxcoil_cli_intervals(monkeypatch):
    observed = {}

    def observe_workflow(openstudio, run_dir, osw, measures_only=False):
        observed["osw"] = osw
        observed["measures_only"] = measures_only

    monkeypatch.setattr(s4b, "run_workflow", observe_workflow)
    result = CliRunner().invoke(
        run_dxcoil,
        [
            "--measures-only",
            "--measures-dir",
            measures_dir,
            "--charge-start",
            "19:00",
            "--charge-end",
            "07:00",
            "--discharge-start",
            "11:00",
            "--discharge-end",
            "17:00",
            stand_alone_retail,
            epw,
        ],
    )

    assert result.exit_code == 0, result.output
    packaged_ice = next(
        step for step in observed["osw"]["steps"] if step["measure_dir_name"] == "add_packaged_ice_storage"
    )
    assert packaged_ice["arguments"]["charge_start"] == "19:00"
    assert packaged_ice["arguments"]["charge_end"] == "07:00"
    assert packaged_ice["arguments"]["discharge_start"] == "11:00"
    assert packaged_ice["arguments"]["discharge_end"] == "17:00"
    assert observed["measures_only"] is True
