# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import click
import os
import s4b as stor4build

from ..__about__ import __version__

@click.command()
@click.argument('OSM', type=click.Path(exists=True))
@click.argument('EPW', type=click.Path(exists=True))
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
def run(osm, epw, openstudio, run_dir):
    """
    Run the OpenStudion command line on the model in OSM with the weather in EPW.
    """
    click.echo('Run!')
    osw = {
        'created_at': '20200127T205012Z',
        'measure_paths': [ '.' ],
        'run_directory': run_dir,
        'seed_file': osm,
        'steps': [],
        'updated_at': '20200127T213540Z',
        'weather_file': epw
    }
    stor4build.run(openstudio, run_dir, osw)

@click.command()
@click.argument('PROTOTYPE', type=click.Choice(stor4build.prototypes_list))
@click.argument('VINTAGE', type=click.Choice(stor4build.vintage_list))
@click.argument('CLIMATE_ZONE', type=click.Choice(stor4build.climate_zone_list))
@click.argument('EPW', type=click.Path(exists=True))
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
@click.option('-o', '--output-dir', show_default=True, default='run', help='Directory for OpenStudio outputs.')
@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory containing measures.')
def run_prototype(prototype, vintage, climate_zone, epw, openstudio, run_dir, output_dir, measures_dir):
    """
    Run the OpenStudion command line on a particular prototype model with the weather in EPW.
    """
    click.echo('Run Prototype!')
    #stor4build.seed_model(openstudio, run_dir, 'seed.osm')
    cz_arg = stor4build.climate_zone_lookup[climate_zone]
    vintage_arg = stor4build.vintage_lookup[vintage]
    osw = {
        'created_at': '20200127T205012Z',
        'measure_paths': [ os.path.abspath(measures_dir) ],
        'run_directory': os.path.join(run_dir, output_dir),
        'seed_file': '',
        'steps': [
            {
                'arguments' : {
                    'building_type': prototype,
                    'climate_zone': cz_arg,
                    'template': vintage_arg
                    },
                'measure_dir_name' : 'create_doe_prototype_building',
                'name' : 'Create DOE Prototype Building Extended'
            }
        ],
        'updated_at': '20200127T213540Z',
        'weather_file': os.path.abspath(epw)
    }
    stor4build.run(openstudio, run_dir, osw)

@click.command()
#@click.argument('PROTOTYPE', type=click.Choice(stor4build.prototypes_list))
@click.argument('VINTAGE', type=click.Choice(stor4build.vintage_list))
@click.argument('CLIMATE_ZONE', type=click.Choice(stor4build.climate_zone_list))
@click.argument('EPW', type=click.Path(exists=True))
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
@click.option('-o', '--output-dir', show_default=True, default='run', help='Directory for OpenStudio outputs.')
@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory containing measures.')
def run_tank(vintage, climate_zone, epw, openstudio, run_dir, output_dir, measures_dir):
    """
    Run the OpenStudion command line on a TES model.
    """
    click.echo('Run Tank!')
    prototype = 'LargeOffice'
    cz_arg = stor4build.climate_zone_lookup[climate_zone]
    vintage_arg = stor4build.vintage_lookup[vintage]
    osw = {
        'measure_paths': [ os.path.abspath(measures_dir) ],
        'run_directory': os.path.join(run_dir, output_dir),
        'seed_file': '',
        'steps': [
            {
                'arguments' : {
                    'building_type': prototype,
                    'climate_zone': cz_arg,
                    'template': vintage_arg
                    },
                'measure_dir_name' : 'create_doe_prototype_building',
                'name' : 'Create DOE Prototype Building Extended'
            },
            {
                "measure_dir_name" : "add_pytank",
                "name" : "Add Python Tank",
                "description" : "This measure will add the Python tank model.",
                "modeler_description" : "This measure will add the Python tank model.",
                "arguments" : {
                    "chrg_start" : "22:00",
                    "chrg_end" : "07:58",
                    "dchrg_start" : "07:59",
                    "dchrg_end" : "18:00",
                    "chrg_temp" : -3.8,
                    "num_tanks" : 1,
                    "trim_temp" : 10
                }
            }
        ],
        'weather_file': os.path.abspath(epw)
    }
    stor4build.run(openstudio, run_dir, osw)

@click.group(context_settings={'help_option_names': ['-h', '--help']}, invoke_without_command=False)
@click.version_option(version=__version__, prog_name='s4b')
@click.pass_context
def s4b(ctx: click.Context):
    pass

s4b.add_command(run)
s4b.add_command(run_prototype)
s4b.add_command(run_tank)
