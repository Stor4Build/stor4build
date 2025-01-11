# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import stor4build as s4b
import os
import json

# Make some assumptions
this_dir = os.path.abspath(os.path.dirname(__file__))
resources_dir = os.path.join(this_dir, '..', 'resources')
    
def test_input_ice():
    input_path = os.path.join(resources_dir, 'input-ice.json')
    data = s4b.InputData.load(input_path)
    assert data.baseline.type == 'LargeOffice'
    assert data.baseline.vintage == 2011
    assert data.baseline.climate == '5A'
    
