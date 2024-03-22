# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import click
import os
import s4b as stor4build
from flask import Flask, request

from ..__about__ import __version__

def create_app(config=None, instance_path=None):
    # create and configure the app
    if instance_path is not None:
        app = Flask(__name__, instance_relative_config=True, instance_path=instance_path)
    else:
        app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        OPENSTUDIO='openstudio',
        MEASURES_DIR='.',
        WEATHER_DIR='.'
    )

    if config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(config)

    # Make some assumptions if specific variables are missing
    if 'MODELS_DIR' not in app.config:
        app.config['MODELS_DIR'] = app.config['WEATHER_DIR']

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #
    @app.route('/prototype', methods=['GET', 'POST'])
    def prototype_route():
        # POST request
        if request.method == 'POST':
            prototype = request.form.get('prototype')
            cz = 'ASHRAE 169-2006-%s' % request.form.get('cz')
            vintage = request.form.get('vintage')
            epw = stor4build.weather_lookup(cz)
            osw = {
                'created_at': '20200127T205012Z',
                'measure_paths': [ os.path.abspath(app.config['MEASURES_DIR']) ],
                'run_directory': os.path.join(app.instance_path, 'run'),
                'seed_file': '',
                'steps': [
                    {
                        'arguments' : {
                            'building_type': prototype,
                            'climate_zone': cz,
                            'template': vintage
                            },
                        'measure_dir_name' : 'create_doe_prototype_building_extended',
                        'name' : 'Create DOE Prototype Building Extended'
                    }
                ],
                'updated_at': '20200127T213540Z',
                'weather_file': os.path.join(app.config['WEATHER_DIR'], epw)
            }
            stor4build.run(app.config['OPENSTUDIO'], app.instance_path, osw)

            return '''
<h1>%s</h1>
<h2>Climate zone: %s</h2>
<h2>Vintage: %s</h2>
''' % (prototype, cz, vintage)

        # GET request
        return '''
<form method="POST">
    <div><label>Prototype: <select id="prototype" name="prototype">
        %s
        </select></label></div>
    <div><label>Climate Zone: <select id="cz" name="cz">
        %s
        </select></label></div>
    <div><label>Vintage: <select id="vintage" name="vintage">
        %s
        </select></label></div>
    <input type="submit" value="Submit">
</form>''' % (''.join(['<option value="%s">%s</option>' % (el,el) for el in stor4build.prototypes_list]),
              ''.join(['<option value="%s">%s</option>' % (el,el) for el in stor4build.climate_zone_list]),
              ''.join(['<option value="%s">%s</option>' % (el,el) for el in stor4build.vintage_values]))

    #
    @app.route('/tank', methods=['GET', 'POST'])
    def tank_route():
        # POST request
        if request.method == 'POST':
            prototype = request.form.get('prototype')
            cz = 'ASHRAE 169-2006-%s' % request.form.get('cz')
            vintage = request.form.get('vintage')
            charge_start = request.form.get('charge_start')
            charge_end = request.form.get('charge_end')
            discharge_start = request.form.get('discharge_start')
            discharge_end = request.form.get('discharge_end')
            charge_temp = request.form.get('charge_temp')
            ntanks = request.form.get('ntanks')
            trim_temp = request.form.get('trim_temp')
            epw = stor4build.weather_lookup(cz)
            osw = {
                'measure_paths': [ os.path.abspath(app.config['MEASURES_DIR']) ],
                'run_directory': os.path.join(app.instance_path, 'run'),
                'seed_file': os.path.join(app.config['MODELS_DIR'], stor4build.prototype_lookup(prototype, cz, vintage)),
                'steps': [
                    {
                        "measure_dir_name" : "add_csv_output",
                        "name" : "Add CSV Output",
                        "arguments" : {}
                    },
                    {
                        "measure_dir_name" : "add_pytank",
                        "name" : "Add Python Tank",
                        "description" : "This measure will add the Python tank model.",
                        "modeler_description" : "This measure will add the Python tank model.",
                        "arguments" : {
                            "chrg_start" : charge_start,
                            "chrg_end" : charge_end,
                            "dchrg_start" : discharge_start,
                            "dchrg_end" : discharge_end,
                            "chrg_temp" : charge_temp,
                            "num_tanks" : ntanks,
                            "trim_temp" : trim_temp
                        }
                    }
                ],
                'weather_file': os.path.join(app.config['WEATHER_DIR'], epw)
            }
            stor4build.run(app.config['OPENSTUDIO'], app.instance_path, osw)

            return '''
<h1>%s</h1>
<h2>Climate zone: %s</h2>
<h2>Vintage: %s</h2>
''' % (prototype, cz, vintage)

        # GET request
        return '''
<form method="POST">
    <div><label>Prototype: <select id="prototype" name="prototype">
        %s
        </select></label></div>
    <div><label>Climate Zone: <select id="cz" name="cz">
        %s
        </select></label></div>
    <div><label>Vintage: <select id="vintage" name="vintage">
        %s
        </select></label></div>
    <div><label>Charge Start Time: <input type="time" id="charge_start" name="charge_start" min="00:00" max="24:00" value="21:00" required /></label></div>
    <div><label>Charge End Time: <input type="time" id="charge_end" name="charge_end" min="00:00" max="24:00" value="07:00" required /></label></div>
    <div><label>Discharge Start Time: <input type="time" id="discharge_start" name="discharge_start" min="00:00" max="24:00" value="12:00" required /></label></div>
    <div><label>Discharge End Time: <input type="time" id="discharge_end" name="discharge_end" min="00:00" max="24:00" value="18:00" required /></label></div>
    <div><label>Charge Temperature: <input type="number" id="charge_temp" name="charge_temp" min="-10.0" max="10.0" value="-3.8" step="any" required /></label></div>
    <div><label>Number of Tanks: <input type="number" id="ntanks" name="ntanks" min="1" step="1" max="50" value="1" required /></label></div>
    <div><label>Trim Temperature: <input type="number" id="trim_temp" name="trim_temp" min="0.0" max="20.0" value="10.0" step="any" required /></label></div>
    <input type="submit" value="Submit">
</form>''' % (''.join(['<option value="LargeOffice">Large Office</option>']),
              ''.join(['<option value="%s">%s</option>' % (el,el) for el in stor4build.climate_zone_list]),
              ''.join(['<option value="%s">%s</option>' % (el,el) for el in stor4build.vintage_values]))


    return app


@click.command()
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('--instance-path', show_default=False, default=None, help='Instance folder path.')
@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.',
              help='Directory containing measures.')
@click.option('-w', '--weather-dir', type=click.Path(exists=True), show_default=True, default='.',
              help='Directory containing weather files.')
def prototype(openstudio, instance_path, measures_dir, weather_dir):
    """
    Run the OpenStudion command line on a particular prototype.
    """
    config = {
        'OPENSTUDIO': openstudio,
        'MEASURES_DIR': measures_dir,
        'WEATHER_DIR': weather_dir
    }
    app = create_app(config=config, instance_path=instance_path)
    app.run(host='127.0.0.1', port=5000, debug=True)

@click.group(context_settings={'help_option_names': ['-h', '--help']}, invoke_without_command=False)
@click.version_option(version=__version__, prog_name='s4b-api')
@click.pass_context
def s4b_api(ctx: click.Context):
    pass

s4b_api.add_command(prototype)
