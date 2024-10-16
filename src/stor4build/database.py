# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
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
        self.prototype_cases_table = kwargs.get('prototype_cases_table', 'prototype_cases')
        #self.prototype_chillers_table = kwargs.get('prototype_chillers_table', 'prototype_chillers')
        #self.prototype_chiller_results_table = kwargs.get('prototype_chiller_results_table', 'prototype_chiller_results')
        self.weather_table = kwargs.get('weather_table', 'weather')
        self.verbose = kwargs.get('verbose', False)
        # Get the columns
        #self.columns = []
        #self.cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = %s", (self.prototype_chiller_results_table,))
        #for result in self.cursor.fetchall():
        #    self.columns.append(result[0])
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
    def get_prototype_model(self, filepath, building_type='LargeOffice', climate_zone='4A', vintage='2010'):
        self.cursor.execute(sql.SQL("SELECT building_id, osm FROM {} WHERE building_type=%s AND vintage=%s AND climate_zone=%s").format(sql.Identifier(self.prototype_cases_table)),
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
         
        
