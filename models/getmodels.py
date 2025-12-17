
import stor4build

# Connect to the DEVELOPMENT db and get models. Not for use in production envs

# Configuration complete
resultsdb = stor4build.ResultsDatabase(database = "tessbed",
                                       user = "postgres",
                                       password = "postgres",
                                       host = 'localhost',
                                       port = '5432',
                                       cases_table = 'baseline_cases',
                                       results_table = 'baseline_results',
                                       weather_table = 'weather',
                                       verbose = True)
                                       
prototypes = {'LargeOffice': {'cz': ['3A', '4A', '5A'], 'vintage': ['2013', '2019', 'pre1980']},
              'SmallOffice': {'cz': ['3A', '4A', '5A'], 'vintage': ['2010', 'post1980', '2019']},
              'RetailStandalone': {'cz': ['3A', '4A', '5A'], 'vintage': ['2007', '2004', '2016']}}
              
for type, value in prototypes.items():
    for cz,vintage in zip(value['cz'], value['vintage']):
        filename = type + '_' + cz + '_' + vintage + '.osm'
        print(filename)
        result = resultsdb.get_model(filename, building_type=type, climate_zone=cz, vintage=vintage)
