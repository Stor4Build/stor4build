# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import click
import os
import s4b as stor4build
from flask import Flask, request

from ..__about__ import __version__

prototypes_list = ['SecondarySchool',
                   'PrimarySchool',
                   'SmallOffice',
                   'MediumOffice',
                   'LargeOffice',
                   'SmallHotel',
                   'LargeHotel',
                   'Warehouse',
                   'RetailStandalone',
                   'RetailStripmall',
                   'QuickServiceRestaurant',
                   'FullServiceRestaurant',
                   'MidriseApartment',
                   'HighriseApartment',
                   'Hospital',
                   'Outpatient',
                   'SuperMarket',
                   'SmallDataCenterLowITE',
                   'SmallDataCenterHighITE',
                   'LargeDataCenterLowITE',
                   'LargeDataCenterHighITE',
                   'SmallOfficeDetailed',
                   'MediumOfficeDetailed',
                   'LargeOfficeDetailed',
                   'Laboratory'
                   ]

cz_list = ['1A', '2A', '2B', '3A', '3B', '3C', '4A', '4B', '4C', '5A',
           '5B', '5C', '6A', '6B', '7A', '7B', '8A']

vintage_list = ['DOE Ref Pre-1980',
                'DOE Ref 1980-2004',
                '90.1-2004',
                '90.1-2007',
                '90.1-2010',
                '90.1-2013']

def create_app(config=None, instance_path=None):
    # create and configure the app
    if instance_path is not None:
        app = Flask(__name__, instance_relative_config=True, instance_path=instance_path)
    else:
        app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        OPENSTUDIO='openstudio',
        MEASURES_DIR='.'
    )

    if config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #
    @app.route('/prototype', methods=['GET', 'POST'])
    def protootype_route():
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
                'weather_file': epw
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
</form>''' % (''.join(['<option value="%s">%s</option>' % (el,el) for el in prototypes_list]),
              ''.join(['<option value="%s">%s</option>' % (el,el) for el in cz_list]),
              ''.join(['<option value="%s">%s</option>' % (el,el) for el in vintage_list]))

    return app


@click.command()
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('--instance-path', show_default=False, default=None, help='Instance folder path.')
@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.',
              help='Directory containing measures.')
def prototype(openstudio, instance_path, measures_dir):
    """
    Run the OpenStudion command line on a particular prototype.
    """
    config = {
        'OPENSTUDIO': openstudio,
        'MEASURES_DIR': measures_dir
    }
    app = create_app(config=config, instance_path=instance_path)
    app.run(host='127.0.0.1', port=5000, debug=True)

@click.group(context_settings={'help_option_names': ['-h', '--help']}, invoke_without_command=False)
@click.version_option(version=__version__, prog_name='s4b-api')
@click.pass_context
def s4b_api(ctx: click.Context):
    pass

s4b_api.add_command(prototype)
