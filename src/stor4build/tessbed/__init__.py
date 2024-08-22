# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import csv
import tempfile
import io
import stor4build
from flask import Flask, request, make_response

from ..__about__ import __version__

# Make some assumptions to get the default locations
this_dir = os.path.abspath(os.path.dirname(__file__))
default_measures_dir = os.path.join(this_dir, '..', '..', '..', 'measures')
default_weather_dir = os.path.join(this_dir, '..', '..', '..', 'resources')

# Supported climate zones
supported_czs = ['1A', '2A', '2B', '3A', '3B', '3C', '4A', '4B', '4C', '5A', '5B', '6A', '6B', '7A', '8A']


def create_app(config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        OPENSTUDIO='openstudio',
        MEASURES_DIR=default_measures_dir,
        WEATHER_DIR=default_weather_dir
    )

    if config is None:
        app.config.from_prefixed_env()
    else:
        app.config.from_mapping(config)
    
    openstudio_exe = app.config['OPENSTUDIO']
    measures_dir = os.path.abspath(app.config['MEASURES_DIR'])
    weather_dir = os.path.abspath(app.config['WEATHER_DIR'])

    # Route(s)
    @app.route('/simple', methods=['POST'])
    def simple_route():
        """
        Simulate a TES technology without sizing.
        """
        # Get the inputs
        data = request.get_json()
        type = data.get('prototype') # Unused for now
        cz = 'ASHRAE 169-2006-%s' % data.get('cz') # Unused for now
        vintage = data.get('vintage') # Unused for now
        tech = data.get('technology')
        tes_type = tech.get('type')
        if tes_type == 'icetank':
            charge_start = tech.get('charge_start', stor4build.IceTank.default_charge_start)
            charge_end = tech.get('charge_end', stor4build.IceTank.default_charge_end)
            discharge_start = tech.get('discharge_start', stor4build.IceTank.default_discharge_start)
            discharge_end = tech.get('discharge_end', stor4build.IceTank.default_discharge_end)
            charge_temp = tech.get('charge_temp', stor4build.IceTank.default_charge_temp)
            num_tanks = tech.get('num_tanks', stor4build.IceTank.default_num_tanks)
            trim_temp = tech.get('trim_temp', stor4build.IceTank.default_trim_temp)
            arguments = {
                "charge_start" : charge_start,
                "charge_end" : charge_end,
                "discharge_start" : discharge_start,
                "discharge_end" : discharge_end,
                "charge_temp" : charge_temp,
                "num_tanks" : num_tanks,
                "trim_temp" : trim_temp
            }
            technology_object = stor4build.IceTank('icetank',**arguments)
            added = [{
                        "measure_dir_name" : "add_output_variables",
                        "name" : "Add Output Variables",
                        "arguments" : {}
                    }]
        else:
            return make_response({'error': 'UnknownTechnologyType', 'message': 'Technology type "%s" is unknown.' % tes_type}, 400)
        
        osm = os.path.abspath(os.path.join(weather_dir, 'LargeOffice.osm'))
        epw = os.path.abspath(os.path.join(weather_dir, 'USA_TN_Knoxville-McGhee.Tyson.AP.723260_TMY3.epw'))
        
        response_txt = ''
        with tempfile.TemporaryDirectory() as run_dir:
            run_path = os.path.abspath(run_dir)
    
            work = [stor4build.Simulation('baseline', added_steps=added), technology_object]
            
            for case in work:
                osw = case.osw(osm, measures_dir, epw)
                stor4build.run_workflow(openstudio_exe, os.path.join(run_path, case.tag()), osw, measures_only=False)
            # Baseline results are in this directory
            baseline_path = os.path.join(run_dir, 'baseline', 'run')
            baseline_csv = os.path.join(baseline_path, 'eplusout.csv')
            stor4build.fix_csv(baseline_csv)
            with open(baseline_csv, 'r') as fp:
                response_txt = fp.read()

        response = make_response(response_txt)
        response.headers["Content-Disposition"] = "attachment; filename=results.csv"
        response.headers["Content-type"] = "text/csv"
        return response
    @app.route('/simulate', methods=['POST'])
    def simulate_route():
        """
        Simulate a TES technology, including sizing.
        """
        # Get the inputs
        data = request.get_json()
        detailed_header = True
        if 'header_style' in data:
            if data['header_style'] == 'simple':
                detailed_header = False
        baseline_data = data.get('baseline')
        # Get the building data
        # There's a better way to do all of this, no time now
        if baseline_data is None:
            return make_response({'error': 'Bad request', 'message': 'Expected "baseline" data in input.'}, 400)
        type = baseline_data.get('type') # Unused for now
        if type is None:
            return make_response({'error': 'Bad request', 'message': 'Expected "building" parameter in "baseline" data input.'}, 400)
        climate_string = baseline_data.get('climate')
        if climate_string is None:
            return make_response({'error': 'Bad request', 'message': 'Expected "climate" parameter in "baseline" data input.'}, 400)
        climate_string = str(climate_string).strip()
        if len(climate_string) != 2:
            return make_response({'error': 'Bad request', 'message': '"climate" parameter value "%s" in "baseline" data input is incorrect.' % climate_string}, 400)
        climate_string = climate_string.upper()
        if climate_string not in supported_czs:
            return make_response({'error': 'Bad request', 'message': 'Climate zone "%s" specified in "baseline" data input is not supported.' % climate_string}, 400)
        cz = 'ASHRAE 169-2006-%s' % climate_string # Unused for now
        vintage = baseline_data.get('vintage') # Unused for now
        if vintage is None:
            return make_response({'error': 'Bad request', 'message': 'Expected "vintage" parameter in "baseline" data input.'}, 400)
        try:
            vintage = int(vintage)
        except ValueError:
            return make_response({'error': 'Bad request', 'message': '"vintage" parameter value "%s" in "baseline" data input is not an integer.' % vintage}, 400)
        
        # Get utility rate info, just the one energy schedule for now
        try:
            energy_sch = data['energy']['schedule']['months'][0]['periods']
        except (KeyError, TypeError, IndexError):
            return make_response({'error': 'Bad request', 'message': 'Expected energy cost schedule was not found in input.'}, 400)
        if len(energy_sch) != 24:
            return make_response({'error': 'Bad request', 'message': 'Energy cost schedule is not the correct length in input.'}, 400)
        
        # Type is still not sent, punt for now
        tech = data.get('storage')
        if tech is None:
            return make_response({'error': 'Bad request', 'message': 'Expected input on storage technology not in input.'}, 400)
        #tes_type = tech.get('type')
        tes_type = 'icetank'
        needs_baseline = False
        if tes_type == 'icetank':
            needs_baseline = True
            # Translate the utility rate parameters to charge/discharge start/end
            capacity = tech.get('capacity')
            if capacity is None:
                return make_response({'error': 'Bad request', 'message': 'Expected "capacity" parameter for ice tank storage is not in input.'}, 400)
            try:
                capacity = float(capacity)
            except ValueError:
                return make_response({'error': 'Bad request', 'message': '"capacity" parameter "%s" value for ice tank storage in non-numeric.' % capacity}, 400)
            results = stor4build.process_energy_schedule(energy_sch)
            arguments = { k:v for k,v in zip(['charge_start', 'charge_end', 'discharge_start', 'discharge_end'], results)}
            arguments['peak_reduction'] = capacity

            technology_object_factory = stor4build.IceTank.size

            added = [{
                        "measure_dir_name" : "add_output_variables",
                        "name" : "Add Output Variables",
                        "arguments" : {}
                    },
                    {
                        "measure_dir_name" : "run_cooling_season_only",
                        "name" : "Run Cooling Season Only",
                        "arguments" : {}
                    }]
        else:
            return make_response({'error': 'UnknownTechnologyType', 'message': 'Technology type "%s" is unknown.' % tes_type}, 400)
            
        osm = os.path.abspath(os.path.join(weather_dir, 'LargeOffice.osm'))
        epw = os.path.abspath(os.path.join(weather_dir, 'USA_TN_Knoxville-McGhee.Tyson.AP.723260_TMY3.epw'))
        
        response_txt = ''
        if needs_baseline:
            # Run the baseline first, then the technology
            with tempfile.TemporaryDirectory() as run_dir:
                #run_dir = '/home/jason/Desktop/s4b-run'
                #if '/home/jason/Desktop/s4b-run' == run_dir:
                run_path = os.path.abspath(run_dir)
                
                # Run the baseline
                baseline = stor4build.Simulation('baseline', added_steps=added)
                osw = baseline.osw(osm, measures_dir, epw)
                stor4build.run_workflow(openstudio_exe, os.path.join(run_path, baseline.tag()), osw, measures_only=False)
                
                # Baseline results are in this directory
                baseline_path = os.path.join(run_dir, 'baseline', 'run')
                baseline_csv = os.path.join(baseline_path, 'eplusout.csv')
                stor4build.fix_csv(baseline_csv)
                
                # Run the technology
                technology_object = technology_object_factory('sized_icetank', baseline_path, **arguments)
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

