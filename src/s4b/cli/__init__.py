# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import click
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

@click.group(context_settings={'help_option_names': ['-h', '--help']}, invoke_without_command=True)
@click.version_option(version=__version__, prog_name='s4b')
@click.pass_context
def s4b(ctx: click.Context):
    click.echo('Hello Stor4Build!')

s4b.add_command(run)
