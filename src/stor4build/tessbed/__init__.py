# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import csv
import tempfile
import stor4build
from flask import Flask, request, make_response

from ..__about__ import __version__

# Make some assumptions to get the default locations
this_dir = os.path.abspath(os.path.dirname(__file__))
default_measures_dir = os.path.join(this_dir, '..', '..', '..', 'measures')
default_weather_dir = os.path.join(this_dir, '..', '..', '..', 'resources')


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
    @app.route('/simulate', methods=['POST'])
    def simulate_route():
        # Get the inputs
        data = request.get_json()
        prototype = data.get('prototype') # Unused for now
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
            print(arguments)
            technology_object = stor4build.IceTank('icetank',**arguments)
            added = [{
                        "measure_dir_name" : "add_output_variables",
                        "name" : "Add Output Variables",
                        "arguments" : {}
                    }]
        else:
            return make_response({'error': 'UnknownTechnologyType', 'message': 'Technology type "%s" is unknown.' % tes_type}, 500)
        
        osm = os.path.abspath(os.path.join(weather_dir, 'LargeOffice.osm'))
        epw = os.path.abspath(os.path.join(weather_dir, 'USA_TN_Knoxville-McGhee.Tyson.AP.723260_TMY3.epw'))
        
        with tempfile.TemporaryDirectory() as run_dir:
        
            runner = stor4build.Runner(osm, epw, openstudio_exe, run_dir, 'run', measures_dir)
    
            work = [stor4build.Simulation('baseline', added_steps=added), technology_object]
            
            for case in work:
                osw = case.osw(osm, measures_dir, epw)
                runner.run(osw, case.tag())

        response = make_response({'message': 'Yay!'}, 200) 
        response.headers["Content-Type"] = "application/json" 
        return response
    return app

