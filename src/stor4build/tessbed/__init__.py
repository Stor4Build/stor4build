# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import csv
import tempfile
import io
import contextlib
import stor4build
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
        TIMESCALE_PORT='5432'
    )

    if config is None:
        app.config.from_prefixed_env()
    else:
        app.config.from_mapping(config)
    
    openstudio_exe = app.config['OPENSTUDIO']
    measures_dir = os.path.abspath(app.config['MEASURES_DIR'])
    weather_dir = os.path.abspath(app.config['WEATHER_DIR'])
    
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
                                           prototype_cases_table = 'baseline_cases',
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
            inputs = stor4build.InputData.load(data)
        except ValidationError as ve:
            return make_response({'error': 'Bad request', 'message': process_validation_error(ve)}, 400)
 
        type = inputs.baseline.type # Unused for now
        cz = 'ASHRAE 169-2006-%s' % inputs.baseline.climate
        vintage_to_use = stor4build.map_to_vintage(inputs.baseline.vintage)
        
        # Get utility rate info, just the one energy schedule for now
        energy_sch = inputs.energy.schedule.months[0].periods
        
        if len(energy_sch) != 24:
            return make_response({'error': 'Bad request', 'message': 'Energy cost schedule is not the correct length in input.'}, 400)

        needs_baseline = False
        if inputs.storage.type == 'ThermalTank-Ice':
            needs_baseline = True
            # Translate the utility rate parameters to charge/discharge start/end
            results = stor4build.process_energy_schedule(energy_sch)
            arguments = { k:v for k,v in zip(['charge_start', 'charge_end', 'discharge_start', 'discharge_end'], results)}
            arguments['peak_reduction'] = inputs.storage.capacity

            technology_object_factory = stor4build.IceTank.size

            post = [stor4build.Step('Add Output Variables', 'add_output_variables'),
                    stor4build.Step('Run Cooling Season Only', 'run_cooling_season_only')]
        else:
            return make_response({'error': 'UnknownTechnologyType', 'message': 'Technology type "%s" is unknown.' % tes_type}, 400)

        response_txt = ''
        if needs_baseline:
            # Run the baseline first, then the technology
            with managed_directory(debug_run_dir) as run_dir:
                run_path = os.path.abspath(run_dir)
                
                # Get the weather
                epw = os.path.join(run_dir, 'weather.epw')
                epw_file = resultsdb.get_weather(epw, inputs.baseline.climate)
                if epw_file is None:
                    return make_response({'error': 'UnknownWeather', 'message': 'Failed to find weather file for climate zone "%s".' % climate_string}, 500)
                
                # Get the baseline
                osm = os.path.join(run_dir, 'baseline.osm')
                building_id = resultsdb.get_prototype_model(osm, building_type='LargeOffice', climate_zone=inputs.baseline.climate, vintage=vintage_to_use)
                if building_id is None:
                    return make_response({'error': 'UnknownBaseline', 'message': 'Baseline for inputs %s, %s, %s is unknown.' % (type, climate_string, vintage_to_use)}, 400)

                # Run the baseline
                baseline = stor4build.Simulation('baseline', post_steps=post)
                osw = baseline.osw(osm, measures_dir, epw)
                stor4build.run_workflow(openstudio_exe, os.path.join(run_path, baseline.tag()), osw, measures_only=False)
                
                # Baseline results are in this directory
                baseline_path = os.path.join(run_dir, 'baseline', 'run')
                baseline_csv = os.path.join(baseline_path, 'eplusout.csv')
                stor4build.fix_csv(baseline_csv)
                
                # Run the technology
                technology_object = technology_object_factory('sized_icetank', baseline_path, post_steps=post, **arguments)
                osw = technology_object.osw(osm, measures_dir, epw)
                stor4build.run_workflow(openstudio_exe, os.path.join(run_path, 
                                        technology_object.tag()), osw, measures_only=False)
                if detailed_header:
                    for k,v in technology_object.sizing.items():
                        response_txt += '%s,"%s"\n' % (k, str(v)) 
                tech_csv = os.path.join(run_dir, 'sized_icetank', 'run', 'eplusout.csv')
                stor4build.fix_csv(tech_csv)
                response_txt += stor4build.combine_csvs(baseline_csv, tech_csv)
                
        else:
            return make_response({'error': 'Not implemented', 'message': 'Parallel tech/baseline not implemented.'}, 500)
            # Run things in a loop, this could be done in parallel
            #with tempfile.TemporaryDirectory() as run_dir:
            #    run_path = os.path.abspath(run_dir)
            #    technology_object = technology_object_factory('sized_icetank', **tech)
            #    for case in [stor4build.Simulation('baseline', added_steps=added), technology_object]:
            #        osw = case.osw(osm, measures_dir, epw)
            #        stor4build.run_workflow(openstudio_exe, os.path.join(run_path, case.tag()), osw, measures_only=False)

        response = make_response(response_txt)
        response.headers["Content-Disposition"] = "attachment; filename=results.csv"
        response.headers["Content-type"] = "text/csv"
        #response = make_response(technology_object.sizing, 200)
        #response.headers["Content-Type"] = "application/json" 
        return response
    return app

