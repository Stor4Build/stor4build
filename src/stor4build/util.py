# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import pandas as pd
import tempfile
import dataclasses
import json
import datetime

def seed_model(openstudio_exe, path, filename):
    cur_dir = os.getcwd()
    os.chdir(path)
    filepath = os.path.join(path, filename)
    os.system('%s -e "require \'openstudio\'; model = OpenStudio::Model::Model.new; out = OpenStudio::Path.new(\'%s\'); model.save(out,true)"' % (openstudio_exe, filepath))
    os.chdir(cur_dir)

def weather_lookup(climate_zone):
    # Cheat for now, all the world is 4A
    return 'USA_TN_Knoxville-McGhee.Tyson.AP.723260_TMY3.epw'

def prototype_lookup(type, climate_zone, vintage):
    # Cheat for now, all buildings are this one large office
    return 'LargeOffice.osm'
    
def process_energy_schedule(sch, peak=3):
    # Process the energy schedule and produce charge/discharge windows
    reverse_sch = list(reversed(sch)) # This is probably bad, just do it for now
    discharge_start_hour = sch.index(peak) + 1
    discharge_end_hour = len(sch) - reverse_sch.index(peak)
    charge_start_hour = discharge_end_hour + 1
    charge_end_hour = discharge_start_hour - 1
    if discharge_start_hour == 1:
        charge_end_hour = 24
    if discharge_end_hour == 24:
        charge_start_hour = 1
    return ('%02d:00' % charge_start_hour,
            '%02d:00' % charge_end_hour,
            '%02d:00' % discharge_start_hour,
            '%02d:00' % discharge_end_hour)
            
def rate_array(sch, rates):
    result = []
    for v in sch:
        if v in rates:
            result.append(rates[v])
        else:
            return None
    return result
    
def convert_string_time_interval(start, end):
    hour, minute = start.split(':')
    hour = int(hour)
    minute = int(minute)
    window_start = hour
    if minute != 0:
        raise NotImplementedError('Non-zero minute not yet implemented')
    hour, minute = end.split(':')
    hour = int(hour)
    minute = int(minute)
    window_end = hour
    if minute != 0:
        raise NotImplementedError('Non-zero minute not yet implemented')
    #print(window_start, window_end)
    return window_start, window_end
    
def fix_csv(filepath, verbose=False):
    # This needs to be rewritten to do everything in memory
    with tempfile.NamedTemporaryFile('w', delete=False) as tmp: # This is different in later versions of Python
        with open(filepath, 'r') as fp:
            for line in fp:
                if not line.lstrip().startswith('0000'):
                    tmp.write(line)
        tmp.close()
        df = pd.read_csv(tmp.name)
        drop_cols = [col for col in df.columns if 'Facility' in col]
        if verbose:
            print('Dropping columns: ' + ', '.join(drop_cols))
        df = df.drop(drop_cols, axis=1).dropna()
        df.to_csv(filepath, index=False)

def prefix_with_baseline(name):
    return 'Baseline ' + name

def combine_csvs(baseline_csv, tech_csv):
    baseline = pd.read_csv(baseline_csv)
    baseline.rename(prefix_with_baseline, axis='columns', inplace=True)
    tech = pd.read_csv(tech_csv)
    result = pd.concat([baseline, tech], axis=1)
    result.drop(['Date/Time'], axis=1, inplace=True)
    result.rename(columns={'Baseline Date/Time': 'Date/Time'}, inplace=True)
    return result.to_csv(index=False, lineterminator='\n')
    
def combine_single_frequency_df(baseline_csv, tech_csv, freq, energy_data=None, demand_data=None):
    baseline = single_frequency_df(baseline_csv, freq)
    baseline.rename(prefix_with_baseline, axis='columns', inplace=True)
    tech = single_frequency_df(tech_csv, freq)
    result = pd.concat([baseline, tech], axis=1)
    result.drop(['Date/Time'], axis=1, inplace=True)
    result.rename(columns={'Baseline Date/Time': 'Date/Time'}, inplace=True)
    if energy_data is not None:
        first_day = get_first_day(result)
        last_day = get_last_day(result)
        result['energy rate [$/kWh]'] = energy_data.rate_schedule(first_day, last_day)
        if demand_data is not None:
            result['demand period []'] = demand_data.demand_schedule(first_day, last_day)
    return result
    
def combine_single_frequency_csv(baseline_csv, tech_csv, freq, energy_data=None, demand_data=None):
    result = combine_single_frequency_df(baseline_csv, tech_csv, freq, energy_data=energy_data, demand_data=demand_data)
    return result.to_csv(index=False, lineterminator='\n')

def single_frequency_csv(eplusout_csv, freq, verbose=False):
    df = pd.read_csv(eplusout_csv)
    drop_cols = [col for col in df.columns if col != 'Date/Time' and f'({freq})' not in col]
    if verbose:
         print('Dropping columns: ' + ', '.join(drop_cols))
    df = df.drop(drop_cols, axis=1).dropna()
    return df.to_csv(index=False, lineterminator='\n')
    
def single_frequency_df(eplusout_csv, freq, verbose=False):
    df = pd.read_csv(eplusout_csv)
    drop_cols = [col for col in df.columns if col != 'Date/Time' and f'({freq})' not in col]
    if verbose:
         print('Dropping columns: ' + ', '.join(drop_cols))
    return df.drop(drop_cols, axis=1).dropna()

class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        return super().default(o)
        
def get_first_day(eplusout_df):
    return datetime.datetime.fromisoformat(eplusout_df['Date/Time'][0].strip()).date()

def get_last_day(eplusout_df):
    return datetime.datetime.fromisoformat(eplusout_df.tail()['Date/Time'].iloc[-1].strip()).date()

