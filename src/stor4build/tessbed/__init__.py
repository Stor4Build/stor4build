# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import csv
import tempfile
import io
import contextlib
import stor4build
import datetime
from flask import Flask, request, make_response
from marshmallow import ValidationError

from ..__about__ import __version__

# Make some assumptions to get the default locations
this_dir = os.path.abspath(os.path.dirname(__file__))
default_measures_dir = os.path.join(this_dir, '..', '..', '..', 'measures')
default_weather_dir = os.path.join(this_dir, '..', '..', '..', 'resources')

# Supported climate zones
supported_czs = ['1A', '2A', '2B', '3A', '3B', '3C', '4A', '4B', '4C', '5A', '5B', '6A', '6B', '7A', '8A']

@contextlib.contextmanager
def managed_directory(run_dir):
    if run_dir is None:
        tmp = tempfile.TemporaryDirectory()
        try:
            yield tmp.name
        finally:
            tmp.cleanup()
    else:
        try:
            yield run_dir
        finally:
            pass

class MissingConfig(Exception):
    pass

def process_validation_error(err):
    mesgs = []
    try:
        for k,v in err.messages.items():
            if isinstance(v, dict):
                if 'type' in v:
                    if isinstance(v['type'], list):
                        mesg = ' '.join(v['type'])
                    else:
                        mesg = str(v['type'])
                else:
                    mesg = str(v)
            else:
                mesg = str(v)
            mesgs.append(f'{k}: {mesg}')
    except:
        return str(err)
    return '; '.join(mesgs)

def create_app(config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        OPENSTUDIO='openstudio',
        MEASURES_DIR=default_measures_dir,
        WEATHER_DIR=default_weather_dir,
        TIMESCALE_HOST='timescale',
        TIMESCALE_PORT='5432',
        CACHE_BASELINE=False,
        STORE_MISSING_RESULTS=True,
        OLDEST_ACCEPTABLE=None #'2025-06-30T20:20:37.885565-04:00'
    )

    if config is None:
        app.config.from_prefixed_env()
    else:
        app.config.from_mapping(config)
    
    openstudio_exe = app.config['OPENSTUDIO']
    measures_dir = os.path.abspath(app.config['MEASURES_DIR'])
    weather_dir = os.path.abspath(app.config['WEATHER_DIR'])
    cache_baseline = app.config['CACHE_BASELINE']
    store_missing_results = app.config['STORE_MISSING_RESULTS']
    if app.config['OLDEST_ACCEPTABLE'] is None:
        oldest_acceptable = None
    else:
        oldest_acceptable = datetime.datetime.fromisoformat(app.config['OLDEST_ACCEPTABLE'])
    
    debug_run_dir = None
    if 'RUN_DIRECTORY' in app.config:
        debug_run_dir = app.config['RUN_DIRECTORY']
    
    # Connect to the database
    try:
        database = app.config['TIMESCALE_DB']
        user = app.config['TIMESCALE_USERNAME']
        password = app.config['TIMESCALE_PASSWORD']
    except KeyError as exc:
        raise MissingConfig('Missing flask configuration variable: {}'.format(str(exc)))
        
    # Configuration complete
    resultsdb = stor4build.ResultsDatabase(database = database,
                                           user = user,
                                           password = password,
                                           host = app.config['TIMESCALE_HOST'],
                                           port = app.config['TIMESCALE_PORT'],
                                           cases_table = 'baseline_cases',
                                           results_table = 'baseline_results',
                                           weather_table = 'weather',
                                           verbose = True)

    # Route(s)
    @app.route('/simulate', methods=['POST'])
    def simulate_route():
        """
        Simulate a TES technology, including sizing.
        """
        # Get the inputs
        data = request.get_json()
        # This may not be needed
        detailed_header = True
        if 'header_style' in data:
            if data['header_style'] == 'simple':
                detailed_header = False
        try:
            inputs = stor4build.InputData.load_tessbed_v1(data)
        except ValidationError as ve:
            return make_response({'error': 'Bad request', 'message': process_validation_error(ve)}, 400)
 
        building_type = inputs.baseline.type
        cz = 'ASHRAE 169-2006-%s' % inputs.baseline.climate
        vintage_to_use = stor4build.map_to_vintage(inputs.baseline.vintage)
        
        # Get utility rate info, just the one energy schedule for now
        energy_sch = inputs.energy.schedule.months['All'].periods
        
        if len(energy_sch) != 24:
            return make_response({'error': 'Bad request', 'message': 'Energy cost schedule is not the correct length in input.'}, 400)

        needs_baseline = False
        baseline_post = []
        technology_post = []
        technology_object_factory = None
        # Translate the utility rate parameters to charge/discharge start/end
        results = stor4build.process_energy_schedule(energy_sch)
        arguments = {k:v for k,v in zip(['charge_start', 'charge_end', 'discharge_start', 'discharge_end'], results)}
        if inputs.storage.charge_interval is not None:
            # Override the charge interval if it's in the input - implementation commented out
            # arguments['charge_start'] = str(inputs.storage.charge_interval.begin)
            # arguments['charge_end'] = str(inputs.storage.charge_interval.end)
            if inputs.storage.discharge_interval is not None:
                return make_response({'error': 'Bad request', 'message': 'Charge and discharge intervals in input are no longer accepted.'}, 400)
            else:
                return make_response({'error': 'Bad request', 'message': 'Charge interval in input is no longer accepted.'}, 400)
        elif inputs.storage.discharge_interval is not None:
            return make_response({'error': 'Bad request', 'message': 'Discharge interval in input is no longer accepted.'}, 400)

        if inputs.storage.type in ['ThermalTank-Ice', 'ThermalTank-ChilledWater']:
            if building_type != 'LargeOffice':
                return make_response({'error': 'Bad request', 'message': f'Building type "{building_type}" is not supported for this TES type.'}, 400)
            needs_baseline = True
            
            arguments['peak_reduction'] = inputs.storage.capacity
            arguments['store_ice'] = {"ThermalTank-Ice": True, "ThermalTank-ChilledWater": False}[inputs.storage.type]
            arguments['size_fraction'] = inputs.storage.size_fraction

            technology_object_factory = stor4build.IceTank.size

            baseline_post = [stor4build.Step('Add ThermalTank Outputs', 'add_thermaltank_outputs'),
                             stor4build.Step('Run Cooling Season Only', 'run_cooling_season_only')]
            technology_post = [stor4build.Step('Add ThermalTank Outputs', 'add_thermaltank_outputs',{'baseline': False}),
                               stor4build.Step('Run Cooling Season Only', 'run_cooling_season_only')]
        elif inputs.storage.type == 'PackagedIceStorage':
            if building_type not in ['SmallOffice', 'RetailStandalone']:
                return make_response({'error': 'Bad request', 'message': f'Building type "{building_type}" is not supported for this TES type.'}, 400)
            technology_object_factory = stor4build.DxCoil.size
            baseline_post = [stor4build.Step('Add DX Coil Outputs', 'add_dx_coil_outputs'),
                             stor4build.Step('Run Cooling Season Only', 'run_cooling_season_only')]
            technology_post = [stor4build.Step('Add DX Coil Outputs', 'add_dx_coil_outputs',{'baseline': False}),
                               stor4build.Step('Run Cooling Season Only', 'run_cooling_season_only'),
                               stor4build.Step('Get DX Coil Sizes', 'get_dx_coil_sizes')]
        else:
            # Should never reach here because the input is validated, but leave it in as a safety
            return make_response({'error': 'UnknownTechnologyType', 'message': 'Technology type "%s" is unknown.' % tes_type}, 400)

        response_txt = ''
        # Run/load the baseline first, then the technology
        with managed_directory(debug_run_dir) as run_dir:
            run_path = os.path.abspath(run_dir)
            
            # Get the weather
            epw = os.path.join(run_dir, 'weather.epw')
            epw_file = resultsdb.get_weather(epw, inputs.baseline.climate)
            if epw_file is None:
                return make_response({'error': 'UnknownWeather', 'message': 'Failed to find weather file for climate zone "%s".' % climate_string}, 500)
            
            # Get the baseline model
            osm = os.path.join(run_dir, 'baseline.osm')
            building_id = resultsdb.get_model(osm, building_type=building_type, climate_zone=inputs.baseline.climate, vintage=vintage_to_use)
            if building_id is None:
                return make_response({'error': 'UnknownBaseline', 'message': 'Baseline for inputs %s, %s, %s is unknown.' % (type, climate_string, vintage_to_use)}, 400)
            # Get the baseline results
            baseline_path = os.path.join(run_dir, 'baseline', 'run')
            baseline_csv = os.path.join(baseline_path, 'eplusout.csv')
            found_results = False
            if cache_baseline:
                found_results = resultsdb.get_results(building_id, output_path=baseline_path, filename='eplusout.csv', oldest_acceptable=oldest_acceptable)
            if not found_results:
                # Run the baseline
                baseline = stor4build.Simulation('baseline', post_steps=baseline_post)
                osw = baseline.osw(osm, measures_dir, epw)
                stor4build.run_workflow(openstudio_exe, os.path.join(run_path, baseline.tag()), osw, measures_only=False)
                stor4build.fix_csv(baseline_csv)
                if cache_baseline and store_missing_results:
                    resultsdb.set_results(building_id, baseline_csv)
            
            # Run the technology
            technology_object = technology_object_factory('tes', baseline_path, post_steps=technology_post, **arguments)
            osw = technology_object.osw(osm, measures_dir, epw)
            stor4build.run_workflow(openstudio_exe, os.path.join(run_path, 
                                    technology_object.tag()), osw, measures_only=False)

            if detailed_header:
                response_txt += f'version,{__version__}\n'
                # This isn't handled as generally as it should be
                if inputs.storage.type == 'PackagedIceStorage':
                    sizing_report_path = os.path.join(run_dir, 'tes', 'reports', 'get_dx_coil_sizes_report.csv')
                    with open(sizing_report_path, 'r') as fp:
                        names = next(fp).strip()
                        values = next(fp).strip()
                    response_txt += 'packaged_ice_object_names,' + names + '\n'
                    response_txt += 'packaged_ice_capacities,' + values + '\n'
                    names = [el.strip().upper() for el in names.split(',')]
                    replacement_report_path = os.path.join(run_dir, 'tes', 'reports', 'add_packaged_ice_storage_report.txt')
                    with open(replacement_report_path, 'r') as fp:
                        lines = fp.read().splitlines()
                    if len(lines) % 2 == 0:
                        lookup = {}
                        itr = iter([line.strip() for line in lines])
                        for original,new in zip(itr, itr):
                            lookup[new.upper()] = original.upper()
                        replaced = [lookup[el] for el in names]
                        response_txt += 'replaced_object_names,' + ','.join(replaced) + '\n'
                    else:
                        # Something is wrong 
                        response_txt += 'Unable to determine new-to-old object mapping'
                for k,v in technology_object.sizing.items():
                    response_txt += '%s,"%s"\n' % (k, str(v))

            tech_csv = os.path.join(run_dir, 'tes', 'run', 'eplusout.csv')
            stor4build.fix_csv(tech_csv)
            response_txt += stor4build.combine_single_frequency_csv(baseline_csv, tech_csv, 'Hourly')

        response = make_response(response_txt)
        response.headers["Content-Disposition"] = "attachment; filename=results.csv"
        response.headers["Content-type"] = "text/csv"
        return response
    return app

