# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import click
import os
import stor4build

from ..__about__ import __version__

@click.command()
@click.argument('OSM', type=click.Path(exists=True))
@click.argument('EPW', type=click.Path(exists=True))
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('--measures-only', is_flag=True, show_default=True, default=False, help='Run the measures but not the simulation.')
@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
def run(osm, epw, openstudio, measures_only, run_dir):
    """
    Run the OpenStudio command line on the model in OSM with the weather in EPW.
    """
    runner = stor4build.Runner(openstudio, run_dir, 'run', '.')
    osw = runner.osw(osm, epw)
    runner.run(osw, measures_only=measures_only)

#@click.command()
#@click.argument('PROTOTYPE', type=click.Choice(stor4build.prototypes_list))
#@click.argument('VINTAGE', type=click.Choice(stor4build.vintage_list))
#@click.argument('CLIMATE_ZONE', type=click.Choice(stor4build.climate_zone_list))
#@click.argument('EPW', type=click.Path(exists=True))
#@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
#@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
#@click.option('-o', '--output-dir', show_default=True, default='run', help='Directory for OpenStudio outputs.')
#@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory containing measures.')
#def run_prototype(prototype, vintage, climate_zone, epw, openstudio, run_dir, output_dir, measures_dir):
#    """
#    Run the OpenStudio command line on a particular prototype model with the weather in EPW.
#    """
#    click.echo('Run Prototype!')
#    cz_arg = stor4build.climate_zone_lookup[climate_zone]
#    vintage_arg = stor4build.vintage_lookup[vintage]
#    osw = {
#        'created_at': '20200127T205012Z',
#        'measure_paths': [ os.path.abspath(measures_dir) ],
#        'run_directory': os.path.join(run_dir, output_dir),
#        'seed_file': '',
#        'steps': [
#            {
#                'arguments' : {
#                    'building_type': prototype,
#                    'climate_zone': cz_arg,
#                    'template': vintage_arg
#                    },
#                'measure_dir_name' : 'create_doe_prototype_building',
#                'name' : 'Create DOE Prototype Building Extended'
#            }
#        ],
#        'updated_at': '20200127T213540Z',
#        'weather_file': os.path.abspath(epw)
#    }
#    stor4build.run(openstudio, run_dir, osw)

@click.command()
@click.argument('OSM', type=click.Path(exists=True))
@click.argument('EPW', type=click.Path(exists=True))
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
@click.option('-o', '--output-dir', show_default=True, default='run', help='Directory for OpenStudio outputs.')
@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory containing measures.')
@click.option('--measures-only', is_flag=True, show_default=True, default=False, help='Run the measures but not the simulation.')
@click.option('--charge-start', metavar='HH:MM', show_default=True, default='21:00', help='Time to start charging tank.')
@click.option('--charge-end', metavar='HH:MM', show_default=True, default='07:00', help='Time to end charging tank.')
@click.option('--discharge-start', metavar='HH:MM', show_default=True, default='12:00', help='Time to start discharging tank.')
@click.option('--discharge-end', metavar='HH:MM', show_default=True, default='18:00', help='Time to end discharging tank.')
@click.option('--charge-temp', metavar='T', type=click.FloatRange(min=-10.0, max=10.0), show_default=True, default=-3.8, help='Tank charging temperature.')
@click.option('-n', '--ntanks', type=click.IntRange(min=1), metavar='N', show_default=True, default=1, help='Number of tanks.')
@click.option('--trim-temp', metavar='T', type=click.FloatRange(min=0.0, max=20.0), show_default=True, default='10.0', help='Trim temperature.')
def run_icetank(osm, epw, openstudio, run_dir, output_dir, measures_dir, measures_only,
             charge_start, charge_end, discharge_start, discharge_end, charge_temp, ntanks, trim_temp):
    """
    Add an ice tank TES system to an OpenStudio model and run it.
    """
    runner = stor4build.Runner(openstudio, run_dir, output_dir, measures_dir)
    arguments = {
        "chrg_start" : charge_start,
        "chrg_end" : charge_end,
        "dchrg_start" : discharge_start,
        "dchrg_end" : discharge_end,
        "chrg_temp" : charge_temp,
        "num_tanks" : ntanks,
        "trim_temp" : trim_temp
    }
    icetank = stor4build.IceTank()
    icetank.run(runner, osm, epw, measures_only=measures_only, **arguments)

#@click.command()
#@click.argument('PROTOTYPE', type=click.Choice(stor4build.prototypes_list))
#@click.argument('VINTAGE', type=click.Choice(stor4build.vintage_list))
#@click.argument('CLIMATE_ZONE', type=click.Choice(stor4build.climate_zone_list))
#@click.argument('EPW', type=click.Path(exists=True))
#@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
#@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
#@click.option('-o', '--output-dir', show_default=True, default='run', help='Directory for OpenStudio outputs.')
#@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory containing measures.')
#@click.option('--measures-only', is_flag=True, show_default=True, default=False, help='Run the measures but not the simulation.')
#def run_prototype_tank(prototype, vintage, climate_zone, epw, openstudio, run_dir, output_dir, measures_dir, measures_only):
#    """
#    Run the OpenStudio command line on a prototype with a ice tank TES model.
#    """
#    cz_arg = stor4build.climate_zone_lookup[climate_zone]
#    vintage_arg = stor4build.vintage_lookup[vintage]
#    runner = stor4build.Runner(openstudio, run_dir, output_dir, measures_dir)
#    arguments = {
#        "chrg_start" : charge_start,
#        "chrg_end" : charge_end,
#        "dchrg_start" : discharge_start,
#        "dchrg_end" : discharge_end,
#        "chrg_temp" : charge_temp,
#        "num_tanks" : ntanks,
#        "trim_temp" : trim_temp
#    }
#    icetank = stor4build.IceTank()
#    icetank.run(runner, osm, epw, measures_only=measures_only, **arguments)

@click.group(context_settings={'help_option_names': ['-h', '--help']}, invoke_without_command=False)
@click.version_option(version=__version__, prog_name='s4b-compute')
@click.pass_context
def s4b_compute(ctx: click.Context):
    pass

s4b_compute.add_command(run)
#s4b.add_command(run_prototype)
s4b_compute.add_command(run_icetank)
#s4b.add_command(run_prototype_tank)
