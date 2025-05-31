# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
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

@click.command()
@click.argument('OSM', type=click.Path(exists=True))
@click.argument('EPW', type=click.Path(exists=True))
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory containing measures.')
@click.option('-o', '--output', type=click.Path(writable=True, dir_okay=False), default=None, help='Run baseline and write combined CSV to specified file.')
@click.option('--measures-only', is_flag=True, show_default=True, default=False, help='Run the measures but not the simulation.')
@click.option('--charge-start', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_charge_start,
              help='Time to start charging tank(s).')
@click.option('--charge-end', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_charge_end,
              help='Time to end charging tank(s).')
@click.option('--discharge-start', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_discharge_start,
              help='Time to start discharging tank(s).')
@click.option('--discharge-end', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_discharge_end,
              help='Time to end discharging tank(s).')
@click.option('--charge-temp', metavar='T', type=click.FloatRange(min=-10.0, max=10.0), show_default=False,
              default=None, help='Tank charging temperature.')
@click.option('-n', '--ntanks', type=click.IntRange(min=1), metavar='N', show_default=True,
              default=stor4build.IceTank.default_num_tanks, help='Number of tanks.')
@click.option('--trim-temp', metavar='T', type=click.FloatRange(min=0.0, max=20.0), show_default=True,
              default=stor4build.IceTank.default_trim_temp, help='Trim temperature.')
@click.option('-b', '--run-baseline', is_flag=True, show_default=True, default=False, help='Run the baseline.')
@click.option('-c', '--cooling_season_only', is_flag=True, show_default=True, default=False, help='Run only in cooling season.')
@click.option('--chw', is_flag=True, show_default=True, default=False, help='Use chilled water as the storage medium.')
@click.option('--size-fraction', metavar='F', type=click.Choice(['1', '0.9', '0.8', '0.7', '0.6', '0.5']), show_default=True,
              default='1', help='Fraction to use to downsize the chiller.')
def run_icetank(osm, epw, openstudio, run_dir, measures_dir, output, measures_only,
                charge_start, charge_end, discharge_start, discharge_end, charge_temp, ntanks, trim_temp, run_baseline,
                cooling_season_only, chw, size_fraction):
    """
    Add an ice tank TES system to an OpenStudio model and run it.
    """
    # Make paths absolute
    run_path = os.path.abspath(run_dir)
    osm = os.path.abspath(osm)
    epw = os.path.abspath(epw)
    measures_dir = os.path.abspath(measures_dir)
    
    # Organize the arguments
    arguments = {
        "charge_start" : charge_start,
        "charge_end" : charge_end,
        "discharge_start" : discharge_start,
        "discharge_end" : discharge_end,
        "charge_temp" : charge_temp,
        "num_tanks" : ntanks,
        "trim_temp" : trim_temp,
        "size_fraction": float(size_fraction)
    }
    
    if chw:
        arguments['store_ice'] = False
        if charge_temp is None:
            arguments['charge_temp'] = stor4build.IceTank.default_chw_charge_temp
    elif charge_temp is None:
        arguments['charge_temp'] = stor4build.IceTank.default_ice_charge_temp
    
    if output:
        #run_baseline = True
        measures_only = False

    # Run the ice tank
    post = [stor4build.Step('Add ThermalTank Outputs', 'add_thermaltank_outputs', {'baseline': False})]
    if cooling_season_only:
        post.append(stor4build.Step('Run Cooling Season Only', 'run_cooling_season_only'))
    icetank = stor4build.IceTank('icetank', post_steps=post, **arguments)
    osw = icetank.osw(osm, measures_dir, epw)
    stor4build.run_workflow(openstudio, os.path.join(run_path, icetank.tag()), osw, measures_only=measures_only)
    
    # Run the baseline if requested
    if run_baseline:
        post = [stor4build.Step('Add ThermalTank Outputs', 'add_thermaltank_outputs')]
        if cooling_season_only:
            post.append(stor4build.Step('Run Cooling Season Only', 'run_cooling_season_only'))
        baseline = stor4build.Simulation('baseline', post_steps=post)
        osw = baseline.osw(osm, measures_dir, epw)
        stor4build.run_workflow(openstudio, os.path.join(run_path, baseline.tag()), osw, measures_only=measures_only)

    # Combine the CSVs
    if output:
        icetank_csv = os.path.join(run_path, icetank.tag(),'run', 'eplusout.csv')
        stor4build.fix_csv(icetank_csv)
        if run_baseline:
            baseline_csv = os.path.join(run_path, baseline.tag(),'run', 'eplusout.csv')
            stor4build.fix_csv(baseline_csv)
            txt = stor4build.combine_single_frequency_csvs(baseline_csv, icetank_csv, 'Hourly')
        else:
            txt = stor4build.single_frequency_csv(icetank_csv, 'Hourly', verbose=False)
        with open(output, 'w') as fp:
            fp.write(txt)
    

@click.command()
@click.argument('OSM', type=click.Path(exists=True))
@click.argument('EPW', type=click.Path(exists=True))
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory containing measures.')
@click.option('-o', '--output', type=click.Path(writable=True, dir_okay=False), default=None, help='Run baseline and write combined CSV to specified file.')
@click.option('--charge-start', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_charge_start,
              help='Time to start charging tank(s).')
@click.option('--charge-end', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_charge_end,
              help='Time to end charging tank(s).')
@click.option('--discharge-start', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_discharge_start,
              help='Time to start discharging tank(s), beginning of sizing window.')
@click.option('--discharge-end', metavar='HH:MM', show_default=True, default=stor4build.IceTank.default_discharge_end,
              help='Time to end discharging tank(s), end of sizing window.')
@click.option('--charge-temp', metavar='T', type=click.FloatRange(min=-10.0, max=10.0), show_default=False,
              default=None, help='Tank charging temperature.')
@click.option('--peak-reduction', type=click.FloatRange(min=0.0, min_open=True, max=100.0), metavar='PCT',
              show_default=True, default=stor4build.IceTank.default_peak_reduction,
              help='Target percentage to reduce the peak load.')
@click.option('-s', '--show-sizing', is_flag=True, show_default=True, default=False, help='Show sizing results.')
@click.option('-c', '--cooling_season_only', is_flag=True, show_default=True, default=False, help='Run only in cooling season.')
@click.option('--chw', is_flag=True, show_default=True, default=False, help='Use chilled water as the storage medium.')
@click.option('--size-fraction', metavar='F', type=click.Choice(['1', '0.9', '0.8', '0.7', '0.6', '0.5']), show_default=True,
              default='1', help='Fraction to use to downsize the chiller.')
def size_icetank(osm, epw, openstudio, run_dir, measures_dir, output,
                 charge_start, charge_end, discharge_start, discharge_end, charge_temp, peak_reduction, show_sizing,
                 cooling_season_only, chw, size_fraction):
    """
    Add an ice tank TES system to an OpenStudio model, size it, and run it.
    """
    # Make paths absolute
    run_path = os.path.abspath(run_dir)
    osm = os.path.abspath(osm)
    epw = os.path.abspath(epw)
    measures_dir = os.path.abspath(measures_dir)
    
    # Organize the arguments
    arguments = {
        "charge_start" : charge_start,
        "charge_end" : charge_end,
        "discharge_start" : discharge_start,
        "discharge_end" : discharge_end,
        "charge_temp" : charge_temp,
        "peak_reduction" : peak_reduction,
        "size_fraction": float(size_fraction)
    }
    
    if chw:
        arguments['store_ice'] = False
        if charge_temp is None:
            arguments['charge_temp'] = stor4build.IceTank.default_chw_charge_temp
    elif charge_temp is None:
        arguments['charge_temp'] = stor4build.IceTank.default_ice_charge_temp
    
    # Run the baseline
    post = [stor4build.Step('Add ThermalTank Outputs', 'add_thermaltank_outputs')]
    if cooling_season_only:
        post.append(stor4build.Step('Run Cooling Season Only', 'run_cooling_season_only'))
    baseline = stor4build.Simulation('baseline', post_steps=post)
    osw = baseline.osw(osm, measures_dir, epw)
    stor4build.run_workflow(openstudio, os.path.join(run_path, baseline.tag()), osw, measures_only=False)
    baseline_path = os.path.join(run_dir, 'baseline', 'run')
    baseline_csv = os.path.join(baseline_path, 'eplusout.csv')
    # Repair the output CSV
    stor4build.fix_csv(baseline_csv)

    # Size and run the ice tank
    post = [stor4build.Step('Add ThermalTank Outputs', 'add_thermaltank_outputs', {'baseline': False})]
    if cooling_season_only:
        post.append(stor4build.Step('Run Cooling Season Only', 'run_cooling_season_only'))
    icetank = stor4build.IceTank.size('sized_icetank', baseline_path, post_steps=post, **arguments)
    osw = icetank.osw(osm, measures_dir, epw)
    stor4build.run_workflow(openstudio, os.path.join(run_path, icetank.tag()), osw, measures_only=False)
    if show_sizing:
        print('# Sizing Information #')
        for k,v in icetank.sizing.items():
            if k in units:
                print(k+':', v, units[k])
            else:
                print(k+':', v)

    # Combine the CSVs
    if output:
        icetank_csv = os.path.join(run_path, icetank.tag(),'run', 'eplusout.csv')
        stor4build.fix_csv(icetank_csv)
        txt = stor4build.combine_single_frequency_csvs(baseline_csv, icetank_csv, 'Hourly')
        with open(output, 'w') as fp:
            fp.write(txt)

@click.command()
@click.argument('OSM', type=click.Path(exists=True))
@click.argument('EPW', type=click.Path(exists=True))
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory containing measures.')
@click.option('-o', '--output', type=click.Path(writable=True, dir_okay=False), default=None, help='Run baseline and write combined CSV to specified file.')
@click.option('--measures-only', is_flag=True, show_default=True, default=False, help='Run the measures but not the simulation.')
@click.option('-b', '--run-baseline', is_flag=True, show_default=True, default=False, help='Run the baseline.')
@click.option('-c', '--cooling_season_only', is_flag=True, show_default=True, default=False, help='Run only in cooling season.')
@click.option('-s', '--show-sizing', is_flag=True, show_default=True, default=False, help='Show sizing results.')
#@click.option('--hourly', is_flag=True, show_default=True, default=False, help='Run hourly outputs.')
def run_dxcoil(osm, epw, openstudio, run_dir, measures_dir, output, measures_only,
               run_baseline, cooling_season_only, show_sizing):
    """
    Add an DX coil TES system to an OpenStudio model and run it.
    """
    # Make paths absolute
    run_path = os.path.abspath(run_dir)
    osm = os.path.abspath(osm)
    epw = os.path.abspath(epw)
    measures_dir = os.path.abspath(measures_dir)
    if output:
        run_baseline = True
        measures_only = False

    pre = []
    #post = []
    if cooling_season_only:
        pre.append(stor4build.Step('Run Cooling Season Only', 'run_cooling_season_only'))
        
    arguments = {}
    #freq = 'Timestep'
    #if hourly:
    #    arguments = {'hourly': True}
    #    freq = 'Hourly'

    # Run the baseline if requested
    if run_baseline:
        post=[stor4build.Step('Add DX Coil Outputs', 'add_dx_coil_outputs', arguments={'baseline': True})]
        baseline = stor4build.Simulation('baseline', pre_steps=pre, post_steps=post)
        osw = baseline.osw(osm, measures_dir, epw)
        stor4build.run_workflow(openstudio, os.path.join(run_path, baseline.tag()), osw, measures_only=measures_only)

    # Run the DX coil model
    post=[stor4build.Step('Add DX Coil Outputs', 'add_dx_coil_outputs', arguments={'baseline': False})]
    if show_sizing:
        post.append(stor4build.Step('Get DX Coil Sizes', 'get_dx_coil_sizes'))
    dxcoil = stor4build.DxCoil('dxcoil', pre_steps=pre, hourly=False, post_steps=post)
    osw = dxcoil.osw(osm, measures_dir, epw)
    stor4build.run_workflow(openstudio, os.path.join(run_path, dxcoil.tag()), osw, measures_only=measures_only)
    
    if show_sizing:
        print('# Sizing Information #')
        sizing_report_path = os.path.join(run_path, dxcoil.tag(),'reports', 'get_dx_coil_sizes_report.csv')
        with open(sizing_report_path, 'r') as fp:
            names = next(fp).split(',')
            values = next(fp).split(',')
        for name, size in zip(names, values):
            print(name.strip()+': '+size.strip()+' (GJ)')
    
    # Combine the CSVs
    if output:
        baseline_csv = os.path.join(run_path, baseline.tag(),'run', 'eplusout.csv')
        dxcoil_csv = os.path.join(run_path, dxcoil.tag(),'run', 'eplusout.csv')
        txt = stor4build.combine_single_frequency_csvs(baseline_csv, dxcoil_csv, 'Hourly')
        with open(output, 'w') as fp:
            fp.write(txt)

@click.group(context_settings={'help_option_names': ['-h', '--help']}, invoke_without_command=False)
@click.version_option(version=__version__, prog_name='stor4build')
@click.pass_context
def s4b(ctx: click.Context):
    pass

s4b.add_command(run)
s4b.add_command(run_icetank)
s4b.add_command(size_icetank)
s4b.add_command(run_dxcoil)
