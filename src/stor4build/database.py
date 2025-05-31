# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import pandas as pd
import psycopg2
from psycopg2 import sql

class ResultsDatabase:
    def __init__(self, database, user, password, host, port, **kwargs):
        self.connection = None
        self.cursor = None
        self.connection = psycopg2.connect(database = database,
                                           user = user,
                                           password = password,
                                           host = host,
                                           port = port)
        self.cursor = self.connection.cursor()
        self.cases_table = kwargs.get('cases_table', 'cases')
        self.weather_table = kwargs.get('weather_table', 'weather')
        self.results_table = kwargs.get('results_table', 'results')
        self.verbose = kwargs.get('verbose', False)
    def __del__(self):
        if self.connection:
            self.connection.close()
    def get_weather(self, filepath, climate_zone):
        self.cursor.execute(sql.SQL("SELECT epw, filename FROM {} WHERE climate_zone=%s").format(sql.Identifier(self.weather_table)),
                            (climate_zone, ))
        result = self.cursor.fetchone()
        if result:
            epw_txt, filename = result
            if self.verbose:
                print('Found weather file for climate zone "%s" (%s)' % (climate_zone, filename))
            with open(filepath, 'w') as fp:
                fp.write(epw_txt)
            return filename
        if self.verbose:
            print('Failed to find weather file for climate zone "%s"!' % climate_zone)
        return None
    def get_model(self, filepath, building_type='LargeOffice', climate_zone='4A', vintage='2010'):
        self.cursor.execute(sql.SQL("SELECT building_id, osm FROM {} WHERE building_type=%s AND vintage=%s AND climate_zone=%s").format(sql.Identifier(self.cases_table)),
                            (building_type, str(vintage), climate_zone))
        result = self.cursor.fetchone()
        if result:
            building_id, osm_txt = result
            if self.verbose:
                print('Found "%s" building in climate zone "%s" from %s: %d' % (building_type, climate_zone, vintage, building_id))
            with open(filepath, 'w') as fp:
                fp.write(osm_txt)
            return building_id
        if self.verbose:
            print('Failed to find "%s" building in climate zone "%s" from %s!' % (building_type, climate_zone, vintage))
        return None
    def get_results(self, building_id, output_path=None, filename='eplusout.csv', oldest_acceptable=None):
        self.cursor.execute(sql.SQL("SELECT created_at,results FROM {} WHERE building_id=%s").format(sql.Identifier(self.results_table)),
                                                                                                      (building_id,))
        result = self.cursor.fetchone()
        if result:
            created_at, results_txt = result
            if self.verbose:
                print('Found results for id %d, created at %s' % (building_id, str(created_at)))
            if oldest_acceptable is not None:
                if created_at < oldest_acceptable:
                    if self.verbose:
                        print('Results for id %d are older than %s, rejecting!' % (building_id, str(oldest_acceptable)))
                    return False
                elif self.verbose:
                    print('Results for id %d are newer than %s' % (building_id, str(oldest_acceptable)))
            os.makedirs(output_path, exist_ok=True)
            filepath = os.path.join(output_path, filename)
            with open(filepath, 'w') as fp:
                fp.write(results_txt)
            return True
        if self.verbose:
            print('Failed to find results for id %d!' % building_id)
        return False
    def set_results(self, building_id, filepath):
        with open(filepath, 'r') as fp:
            results_txt = fp.read()
        self.cursor.execute(sql.SQL("""insert into {} (building_id,results) values (%s,%s)
on conflict (building_id) do update
set created_at = NOW(), results = EXCLUDED.results""").format(sql.Identifier(self.results_table)), (building_id, results_txt))
        self.connection.commit()
        if self.verbose:
            print('Inserted results for id %d' % building_id)
         
        
