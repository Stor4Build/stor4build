# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
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

pr0t0typ35_1i5t = ['SecondarySchool',
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
                   'SuperMarket',
                   'SmallDataCenterLowITE',
                   'SmallDataCenterHighITE',
                   'LargeDataCenterLowITE',
                   'LargeDataCenterHighITE',
                   'SmallOfficeDetailed',
                   'MediumOfficeDetailed',
                   'LargeOfficeDetailed',
                   'Laboratory'
                   ]

climate_zone_list = ['1A', '2A', '2B', '3A', '3B', '3C', '4A', '4B', '4C',
                     '5A','5B', '5C', '6A', '6B', '7A', '7B', '8A']

climate_zone_lookup = {cz:'ASHRAE 169-2013-{}'.format(cz) for cz in climate_zone_list}

vintage_lookup = {'pre1980':'DOE Ref Pre-1980',
                  '1980_2004': 'DOE Ref 1980-2004',
                  '2004': '90.1-2004',
                  '2007': '90.1-2007',
                  '2010': '90.1-2010',
                  '2013': '90.1-2013'
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

@dataclasses.dataclass
class Step:
    name: str
    measure_dir_name: str
    arguments: Dict[str, Union[str, float, int]] = dataclasses.field(default_factory=dict)
    
    def to_dict(self):
        return dataclasses.asdict(self)