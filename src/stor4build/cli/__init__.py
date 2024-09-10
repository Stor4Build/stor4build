# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import click
import os
import stor4build

from ..__about__ import __version__

units = {'maximum_load': '(J)',
         'peak_reduction': '(%)',
         'window_start': '(HH:MM)',
         'window_end': '(HH:MM)',
         'num_tanks': '(before round up)',
         'interval_start': '(hour of day)',
         'interval_end': '(hour of day)',
         'requested_capacity': '(J)',
         'actual_capacity': '(J)',
         'mass_flow': '(kg/s)',
         'computed_trim_temperature': '(C)'}

@click.command()
@click.argument('OSM', type=click.Path(exists=True))
@click.argument('EPW', type=click.Path(exists=True))
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory containing measures.')
@click.option('--measures-only', is_flag=True, show_default=True, default=False, help='Run the measures but not the simulation.')
@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
def run(osm, epw, openstudio, measures_dir, measures_only, run_dir):
    """
    Run the OpenStudio command line on the model in OSM with the weather in EPW.
    """    
    # Make paths absolute
    run_path = os.path.abspath(run_dir)
    osm_path = os.path.abspath(osm)
    measures_path = os.path.abspath(measures_dir)
    epw_path = os.path.abspath(epw)
    
    case = stor4build.Simulation('simulation')
    osw = case.osw(osm_path, measures_path, epw_path)
    stor4build.run_workflow(openstudio, os.path.join(run_path, case.tag()), osw, measures_only=measures_only)

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
#def run_prototype(prototype, vintage, climate_zone, epw, openstudio, run_dir, output_dir, measures_dir, measures_only):
#    """
#    Run the OpenStudio command line on a particular prototype model with the weather in EPW.
#    """
#    runner = stor4build.PrototypeRunner(openstudio, run_dir, 'run', measures_dir)
#    cz_arg = stor4build.climate_zone_lookup[climate_zone]
#    vintage_arg = stor4build.vintage_lookup[vintage]
#    osw = runner.osw(prototype, cz_arg, vintage_arg, epw)
#    runner.run(osw, measures_only=measures_only)

@click.command()
@click.argument('OSM', type=click.Path(exists=True))
@click.argument('EPW', type=click.Path(exists=True))
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory containing measures.')
@click.option('--measures-only', is_flag=True, show_default=True, default=False, help='Run the measures but not the simulation.')
@click.option('--charge-start', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_charge_start,
              help='Time to start charging tank.')
@click.option('--charge-end', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_charge_end,
              help='Time to end charging tank.')
@click.option('--discharge-start', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_discharge_start,
              help='Time to start discharging tank.')
@click.option('--discharge-end', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_discharge_end,
              help='Time to end discharging tank.')
@click.option('--charge-temp', metavar='T', type=click.FloatRange(min=-10.0, max=10.0), show_default=True,
              default=stor4build.IceTank.default_charge_temp, help='Tank charging temperature.')
@click.option('-n', '--ntanks', type=click.IntRange(min=1), metavar='N', show_default=True,
              default=stor4build.IceTank.default_num_tanks, help='Number of tanks.')
@click.option('--trim-temp', metavar='T', type=click.FloatRange(min=0.0, max=20.0), show_default=True,
              default=stor4build.IceTank.default_trim_temp, help='Trim temperature.')
@click.option('-b', '--run-baseline', is_flag=True, show_default=True, default=False, help='Run the baseline as well.')
def run_icetank(osm, epw, openstudio, run_dir, measures_dir, measures_only,
                charge_start, charge_end, discharge_start, discharge_end, charge_temp, ntanks, trim_temp, run_baseline):
    """
    Add an ice tank TES system to an OpenStudio model and run it.
    """
    runner = stor4build.Runner(osm, epw, openstudio, run_dir, 'run', measures_dir)
    arguments = {
        "charge_start" : charge_start,
        "charge_end" : charge_end,
        "discharge_start" : discharge_start,
        "discharge_end" : discharge_end,
        "charge_temp" : charge_temp,
        "num_tanks" : ntanks,
        "trim_temp" : trim_temp
    }
    work = []
    if run_baseline:
        added = [{
                    "measure_dir_name" : "add_output_variables",
                    "name" : "Add Output Variables",
                    "arguments" : {}
                }]
        work.append(stor4build.Simulation('baseline', added_steps=added))
    icetank = stor4build.IceTank('icetank',**arguments)
    work.append(icetank)
    # Make paths absolute
    run_path = os.path.abspath(run_dir)
    osm_path = os.path.abspath(osm)
    measures_path = os.path.abspath(measures_dir)
    epw_path = os.path.abspath(epw)
    for case in work:
        osw = case.osw(osm_path, measures_path, epw_path)
        stor4build.run_workflow(openstudio, os.path.join(run_path, case.tag()), osw, measures_only=measures_only)

@click.command()
@click.argument('OSM', type=click.Path(exists=True))
@click.argument('EPW', type=click.Path(exists=True))
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory containing measures.')
#@click.option('--measures-only', is_flag=True, show_default=True, default=False, help='Run the measures but not the simulation.')
@click.option('--charge-start', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_charge_start,
              help='Time to start charging tank.')
@click.option('--charge-end', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_charge_end,
              help='Time to end charging tank.')
@click.option('--discharge-start', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_discharge_start,
              help='Time to start discharging tank.')
@click.option('--discharge-end', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_discharge_end,
              help='Time to end discharging tank.')
@click.option('--charge-temp', metavar='T', type=click.FloatRange(min=-10.0, max=10.0), show_default=True,
              default=stor4build.IceTank.default_charge_temp, help='Tank charging temperature.')
@click.option('--peak-reduction', type=click.FloatRange(min=0.0, min_open=True, max=100.0), metavar='PCT',
              show_default=True, default=stor4build.IceTank.default_peak_reduction,
              help='Target percentage to reduce the peak load.')
#@click.option('--trim-temp', metavar='T', type=click.FloatRange(min=0.0, max=20.0), show_default=True,
#              default=stor4build.IceTank.default_trim_temp, help='Trim temperature.')
@click.option('-s', '--show-sizing', is_flag=True, show_default=True, default=False, help='Show sizing results.')
def size_icetank(osm, epw, openstudio, run_dir, measures_dir,
                 charge_start, charge_end, discharge_start, discharge_end, charge_temp, peak_reduction, show_sizing):
    """
    Add an ice tank TES system to an OpenStudio model, size it, and run it.
    """
    run_path = os.path.abspath(run_dir)
    osm = os.path.abspath(osm)
    epw = os.path.abspath(epw)
    measures_dir = os.path.abspath(measures_dir)
    arguments = {
        "charge_start" : charge_start,
        "charge_end" : charge_end,
        "discharge_start" : discharge_start,
        "discharge_end" : discharge_end,
        "charge_temp" : charge_temp,
        "peak_reduction" : peak_reduction,
        #"trim_temp" : trim_temp
    }
    work = []
    added = [{
                "measure_dir_name" : "add_output_variables",
                "name" : "Add Output Variables",
                "arguments" : {}
            }]
    baseline = stor4build.Simulation('baseline', added_steps=added)
    osw = baseline.osw(osm, measures_dir, epw)
    stor4build.run_workflow(openstudio, os.path.join(run_path, baseline.tag()), osw, measures_only=False)
    baseline_results = os.path.join(run_dir, 'baseline', 'run')
    icetank = stor4build.IceTank.size('sized_icetank', baseline_results, **arguments)
    osw = icetank.osw(osm, measures_dir, epw)
    stor4build.run_workflow(openstudio, os.path.join(run_path, icetank.tag()), osw, measures_only=False)
    if show_sizing:
        print('Number of tanks:', icetank.num_tanks)
        for k,v in icetank.sizing.items():
            if k in units:
                print(k+':', v, units[k])
            else:
                print(k+':', v)

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
#s4b_compute.add_command(run_prototype)
s4b_compute.add_command(run_icetank)
s4b_compute.add_command(size_icetank)
#s4b.add_command(run_prototype_tank)
