# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import stor4build

# Connect to the DEVELOPMENT db and get models. Not for use in production envs

# Configuration complete
resultsdb = stor4build.ResultsDatabase(database = "stor4build",
                                       user = "postgres",
                                       password = "postgres",
                                       host = 'localhost',
                                       port = '5432',
                                       cases_table = 'baseline_cases',
                                       results_table = 'baseline_results',
                                       weather_table = 'weather',
                                       verbose = True)
                                       
prototypes = {'College': (('3A', '2007'),),
              'Courthouse': (('5B', 'post1980'),),
              'FullServiceRestaurant': (('3A', '2010'), ('3A', 'pre1980')),
              'Hospital': (('5A', 'post1980'),),
              'Laboratory': (('5A', '2004'),),
              'LargeDataCenterHighITE': (('3A', '2019'),),
              'LargeDataCenterLowITE': (('5A', '2004'),),
              'LargeHotel': (('5A', '2016'),),
              'LargeOffice': (('3A', '2013'), ('4A', '2019'), ('5A', 'pre1980')),
              'MediumOffice': (('5A', '2004'),),
              'Outpatient': (('3A', '2013'),),
              'PrimarySchool': (('5B', '2016'),),
              'QuickServiceRestaurant': (('3A', '2019'),),
              'RetailStandalone': (('3A', '2007'), ('4A', '2004'), ('5A', '2016')),
              'RetailStripmall': (('5B', '2007'),),
              'SecondarySchool': (('3A', '2010'),),
              'SmallOffice': (('4A', 'post1980'), ('5A', '2019')),
              'Warehouse': (('3A', '2010'),)}
              
for type, pairs in prototypes.items():
    for cz,vintage in pairs:
        filename = type + '_' + cz + '_' + vintage + '.osm'
        print(filename)
        result = resultsdb.get_model(filename, building_type=type, climate_zone=cz, vintage=vintage)
