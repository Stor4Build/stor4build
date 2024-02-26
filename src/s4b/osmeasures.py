# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
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

climate_zone_lookup = {cz:'ASHRAE 169-2006-{}'.format(cz) for cz in climate_zone_list}

vintage_lookup = {'pre1980':'DOE Ref Pre-1980',
                  '1980_2004': 'DOE Ref 1980-2004',
                  '2004': '90.1-2004',
                  '2007': '90.1-2007',
                  '2010': '90.1-2010',
                  '2013': '90.1-2013'
                 }

vintage_list = list(vintage_lookup.keys())
vintage_values = list(vintage_lookup.values())