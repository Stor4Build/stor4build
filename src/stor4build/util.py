# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import pandas as pd
import tempfile
import dataclasses
import json
import datetime
import csv
from .__about__ import __version__

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

def int_row(row):
    x = [int(el) for el in row]
    if len(x) == 1:
        return x[0]
    return x

def float_row(row):
    x = [float(el) for el in row]
    if len(x) == 1:
        return x[0]
    return x

def string_row(row):
    if len(row) == 1:
        return row[0]
    return row

def read_results(csv_file:str, echo=print):
    with open(csv_file, 'r') as fp:
        reader = csv.reader(fp)
        # Check for the info block
        info = []
        skiprows = 0
        for line in reader:
            if len(line) > 1:
                if line[0].strip() == 'Date/Time':
                    break
                else:
                    info.append(line)
                    skiprows += 1
            else:
                skiprows += 1
    echo(info)
    header_info = {}
    for line in info:
        try:
            # Need to adjust this for the DX coil system
            header_info[line[0]] = int_row(line[1:])
        except ValueError:
            try:
                header_info[line[0]] = float_row(line[1:])
            except ValueError:
                header_info[line[0]] = string_row(line[1:])
    echo(header_info)
    echo(skiprows)
    df = pd.read_csv(csv_file, skiprows=skiprows)
    df['Date/Time'] = pd.to_datetime(df['Date/Time'], format='mixed')
    if 'maximum_date' in header_info:
        header_info['maximum_date'] = pd.to_datetime(header_info['maximum_date']).date()
    echo(df)
    return header_info, df

def prepare_detailed_header(building_type, climate_zone, vintage, storage_type, storage_medium=None, report_dir=None,
                            sizing=None, arguments=None):
    response_txt = f'version,{__version__}\n'
    response_txt += f'building_type,"{building_type}"\n'
    response_txt += f'climate_zone,"{climate_zone}"\n'
    response_txt += f'vintage,"{vintage}"\n'
    response_txt += f'storage,"{storage_type}"\n'
    # This isn't handled as generally as it should be (still)
    if storage_type == 'PackagedIceStorage':
        sizing_report_path = os.path.join(report_dir, 'get_dx_coil_sizes_report.csv')
        with open(sizing_report_path, 'r') as fp:
            names = next(fp).strip()
            values = next(fp).strip()
        response_txt += 'packaged_ice_object_names,' + names + '\n'
        response_txt += 'packaged_ice_capacities,' + values + '\n'
        names = [el.strip().upper() for el in names.split(',')]
        replacement_report_path = os.path.join(report_dir, 'add_packaged_ice_storage_report.txt')
        with open(replacement_report_path, 'r') as fp:
            lines = fp.read().splitlines()
        if len(lines) % 2 == 0:
            lookup = {}
            itr = iter([line.strip() for line in lines])
            for original,new in zip(itr, itr):
                lookup[new.upper()] = original.upper()
            replaced = [f'"{lookup[el]}"' for el in names]
            response_txt += 'replaced_object_names,' + ','.join(replaced) + '\n'
        else:
            # Something is wrong 
            response_txt += 'Unable to determine new-to-old object mapping'
    else:
        response_txt += f'storage_medium,"{storage_medium}"\n'
    if sizing is not None:
        for k,v in sizing.items():
            response_txt += '%s,"%s"\n' % (k, str(v))
    if arguments is not None:
        for k,v in arguments.items():
            response_txt += 'argument: %s,"%s"\n' % (k, str(v))
    
    return response_txt

