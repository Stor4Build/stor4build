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

vintage_list = ['pre1980',
                '1980_2004',
                '2004',
                '2007',
                '2010',
                '2013']

vintage_lookup = {'pre1980':'DOE Ref Pre-1980',
                  '1980_2004': 'DOE Ref 1980-2004',
                  '2004': '90.1-2004',
                  '2007': '90.1-2007',
                  '2010': '90.1-2010',
                  '2013': '90.1-2013'
                 }

@click.command()
@click.argument('PROTOTYPE', type=click.Choice(prototypes_list))
@click.argument('VINTAGE', type=click.Choice(vintage_list))
@click.argument('CLIMATE_ZONE', type=click.Choice(cz_list))
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
    stor4build.seed_model(openstudio, run_dir, 'seed.osm')
    cz_arg = 'ASHRAE 169-2006-%s' % climate_zone
    vintage_arg = vintage_lookup[vintage]
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
                'measure_dir_name' : 'create_doe_prototype_building_extended',
                'name' : 'Create DOE Prototype Building Extended'
            }
        ],
        'updated_at': '20200127T213540Z',
        'weather_file': epw
    }
    stor4build.run(openstudio, run_dir, osw)

@click.group(context_settings={'help_option_names': ['-h', '--help']}, invoke_without_command=True)
@click.version_option(version=__version__, prog_name='s4b')
@click.pass_context
def s4b(ctx: click.Context):
    click.echo('Hello Stor4Build!')

s4b.add_command(run)
s4b.add_command(run_prototype)
