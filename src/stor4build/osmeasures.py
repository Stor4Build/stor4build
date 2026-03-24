# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from typing import Dict, Union
import dataclasses

prototypes_list = ['SecondarySchool',
                   'PrimarySchool',
                   'SmallOffice',
                   'MediumOffice',
                   'LargeOffice',
                   'SmallHotel',
                   'LargeHotel',
                   'Warehouse',
                   'RetailStandalone',
                   'RetailStripmall',
                   'QuickServiceRestaurant',
                   'FullServiceRestaurant',
                   'MidriseApartment',
                   'HighriseApartment',
                   'Hospital',
                   'Outpatient',
                   'Laboratory',
                   'LargeDataCenterHighITE',
                   'LargeDataCenterLowITE',
                   'SmallDataCenterHighITE',
                   'SmallDataCenterLowITE',
                   'Courthouse',
                   'College']

supported_prototypes_list = [
    'SecondarySchool',
    'PrimarySchool',
    'SmallOffice',
    'MediumOffice',
    'LargeOffice',
    'SmallHotel',
    'LargeHotel',
    'Warehouse',
    'RetailStandalone',
    'RetailStripmall',
    'QuickServiceRestaurant',
    'FullServiceRestaurant',
    'Hospital',
    'Outpatient',
    'Laboratory',
    'LargeDataCenterHighITE',
    'LargeDataCenterLowITE',
    'Courthouse',
    'College'
]

tes_support = {
    'SecondarySchool': ['DX coil packaged ice'],
    'PrimarySchool': ['DX coil packaged ice'],
    'SmallOffice': ['DX coil packaged ice'],
    'MediumOffice': ['DX coil packaged ice'],
    'LargeOffice': ['ThermalTank'],
    'SmallHotel': ['DX coil packaged ice'],
    'LargeHotel': ['ThermalTank'],
    'Warehouse': ['DX coil packaged ice'],
    'RetailStandalone': ['DX coil packaged ice'],
    'RetailStripmall': ['DX coil packaged ice'],
    'QuickServiceRestaurant': ['DX coil packaged ice'],
    'FullServiceRestaurant': ['DX coil packaged ice'],
    'Hospital': ['ThermalTank'],
    'Outpatient': ['DX coil packaged ice'],
    'Laboratory': ['DX coil packaged ice'],
    'LargeDataCenterHighITE': ['ThermalTank'],
    'LargeDataCenterLowITE': ['ThermalTank'],
    'Courthouse': ['ThermalTank'],
    'College': ['ThermalTank']
}

dxcoil_supported = [k for k,v in tes_support.items() if 'DX coil packaged ice' in v]
thermaltank_supported = [k for k,v in tes_support.items() if 'ThermalTank' in v]

climate_zone_list = ['1A', '2A', '2B', '3A', '3B', '3C', '4A', '4B', '4C',
                     '5A','5B', '5C', '6A', '6B', '7A', '7B', '8A']

climate_zone_lookup = {cz:'ASHRAE 169-2013-{}'.format(cz) for cz in climate_zone_list}

vintage_lookup = {'pre1980':'DOE Ref Pre-1980',
                  '1980_2004': 'DOE Ref 1980-2004',
                  '2004': '90.1-2004',
                  '2007': '90.1-2007',
                  '2010': '90.1-2010',
                  '2013': '90.1-2013',
                  '2016': '90.1-2016',
                  '2019': '90.1-2019'
                 }
                 
vintage_map = {
               0:    'pre1980',
               1980: 'post1980',
               2004: '2004',
               2007: '2007',
               2010: '2010',
               2013: '2013',
               2016: '2016',
               2019: '2019'
              }

vintage_keys = list(vintage_map.keys())
vintage_keys.sort()

vintage_list = list(vintage_lookup.keys())
vintage_values = list(vintage_lookup.values())

def map_to_vintage(vintage:int):
    last_key = vintage_keys[0]
    for key in vintage_keys[1:]:
        if vintage < key:
            break
        last_key = key
    return vintage_map[last_key]

def validate_template(building:str, template:str):
    if building in ['Laboratory', 'LargeDataCenterLowITE', 'LargeDataCenterHighITE']:
        if template in ['pre1980', 'post1980']:
            return False
    return True

@dataclasses.dataclass
class Step:
    name: str
    measure_dir_name: str
    arguments: Dict[str, Union[str, float, int]] = dataclasses.field(default_factory=dict)
    
    def to_dict(self):
        return dataclasses.asdict(self)
