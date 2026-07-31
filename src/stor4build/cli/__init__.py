# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import click
import os
import stor4build
import warnings
from matplotlib import pyplot as plt
import pandas as pd

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

# Charge temps
sensible_and_latent_charge_temp = {'water': -3.8,
                                   'simplewater': -3.8,
                                   'pcm2x2a': -3.8}
sensible_only_charge_temp = {'water': 1.1}

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
@click.argument('csvfile',metavar='CSV', type=click.Path(exists=True))
# Need to fix this so it doesn't need a year
@click.option('--date', type=click.DateTime(formats=["%Y-%m-%d"]), default='2006-07-07')
#@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
@click.option('-l', '--legend-loc', type=str, show_default=True, default='lower left', help='Location for the matplotlib legend.')
#@click.option('--measures-only', is_flag=True, show_default=True, default=False, help='Run the measures but not the simulation.')
#@click.option('-r', '--run-dir', type=click.Path(exists=True), show_default=True, default='.', help='Directory to run in.')
def process(csvfile, date, legend_loc): #osm, epw, openstudio, measures_dir, measures_only, run_dir):
    """
    Post-process the hourly CSV from the TES simulations.
    """
    date = date.date()
    info, df = stor4build.read_results(csvfile)
    if 'maximum_date' in info:
        date = info['maximum_date']
    hilight_start = None
    if 'interval_start' in info:
        try:
            hilight_start = int(info['interval_start'])
        except ValueError:
            pass
    hilight_end = None
    if 'interval_end' in info:
        try:
            hilight_end = int(info['interval_end'])
        except ValueError:
            pass

    df['date'] = df['Date/Time'].dt.date

    if 'storage' in info and info['storage'] == 'PackagedIceStorage':
        baseline_cols = []
        utss_cols = [el for el in df.columns.values.tolist() if 'UTSS COIL' in el]
        notutss_cols = [el for el in df.columns.values.tolist() if 'UTSS COIL' not in el]
        #print(utss_cols)
        tes_cols = [el for el in utss_cols if 'Cooling Coil Electricity Energy' in el]
        baseline_cols = [el for el in notutss_cols if 'Cooling Coil Electricity Energy' in el]
        soc_cols = [el for el in utss_cols if 'Cooling Coil Ice Thermal Storage End Fraction' in el]
        #print(tes_cols)
        #print(soc_cols)
        #print(info['packaged_ice_object_names'])
        cap_lookup = {}
        for k,v in zip(info['packaged_ice_object_names'],info['packaged_ice_capacities']):
            #print(k,v)
            cap_lookup[k] = v
        total_cap = sum(cap_lookup.values())
        #print(total_cap)
        df['soc'] = 0.0
        for col in soc_cols:
            cap = 0.0
            for k,v in cap_lookup.items():
                if k in col:
                    cap = v
                    break
            df['soc'] += (cap/total_cap)*df[col]
        #print(df['soc'])
        dfx = df[df['date'] == date]
        baseline = dfx[baseline_cols].sum(axis=1)
        tes = dfx[tes_cols].sum(axis=1)
        soc = dfx['soc']
        label = 'Coil Electrical'
        #dfx['tes'] = 0
        #for col in tes_cols:
        #    dfx['tes'] += dfx[col]
        #dfx['baseline'] = 0
        #for col in baseline_cols:
        #    dfx['baseline'] += dfx[col]
    else:
        # Assume thermaltank to start
        soc_col = 'soc:PythonPlugin:OutputVariable [](Hourly)'
        energy_cols = [el for el in df.columns.values.tolist() if 'Chiller Evaporator Cooling Energy' in el]
        #print(energy_cols)
        baseline_cols = []
        tes_cols = []
        for el in energy_cols:
            if 'Baseline' in el:
                baseline_cols.append(el)
            else:
                tes_cols.append(el)
        assert(len(baseline_cols) == len(tes_cols))
        click.echo(df)
        dfx = df[df['date'] == date]
        click.echo(dfx)
        baseline = dfx[baseline_cols].sum(axis=1)
        tes = dfx[tes_cols].sum(axis=1)
        soc = dfx[soc_col]
        label = 'Chiller Evaporator'

    x = list(range(24))
    fig, ax0 = plt.subplots()
    ax0.plot(x, baseline, label='Baseline Energy')
    ax0.plot(x, tes, label='TES Energy')
    ax0.set_ylabel(f'{label} Energy [J]')
    ax1 = ax0.twinx()
    ax1.plot(x, soc, 'g', label='SOC')
    ax1.set_ylabel('State of Charge')
    if hilight_start and hilight_end:
        plt.axvspan(hilight_start-1, hilight_end-1, color='red', alpha=0.5) # default was 11 to 17
    ax0.set_xlabel('Hour of Day [h]')
    #ax0.legend(['one', 'two', 'three'],loc='center left')
    lines0, labels0 = ax0.get_legend_handles_labels()
    lines1, labels1 = ax1.get_legend_handles_labels()
    ax0.legend(lines0 + lines1, labels0 + labels1, loc=legend_loc)
    plt.show()
    #fig, ax = plt.subplots()
    #
    #plt.show()
    

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
@click.option('-c', '--cooling-season-only', is_flag=True, show_default=True, default=False, help='Run only in cooling season.')
@click.option('--medium', type=click.Choice(['water', 'simplewater', 'pcm2x2a']), default='water', show_default=True,
              help='Set the storage medium to use.')
@click.option('--size-fraction', metavar='F', type=click.Choice(['1', '0.9', '0.8', '0.7', '0.6', '0.5']), show_default=True,
              default='1', help='Fraction to use to downsize the chiller.')
@click.option('--control', metavar='NAME', show_default=True,
              default='default', help='Specify a built-in control scheme (default | demo12to6) or a measure that implements the scheme.')
@click.option('--sensible-only', is_flag=True, show_default=True, default=False, help='Utilize sensible storage only.')
def run_icetank(osm, epw, openstudio, run_dir, measures_dir, output, measures_only,
                charge_start, charge_end, discharge_start, discharge_end, charge_temp, ntanks, trim_temp, run_baseline,
                cooling_season_only, medium, size_fraction, control, sensible_only):
    """
    Add an ice tank TES system to an OpenStudio model and run it.
    """
    # Make paths absolute
    run_path = os.path.abspath(run_dir)
    osm = os.path.abspath(osm)
    epw = os.path.abspath(epw)
    measures_dir = os.path.abspath(measures_dir)

    print("Test: running icetank")
    
    # Organize the arguments
    arguments = {
        "charge_start" : charge_start,
        "charge_end" : charge_end,
        "discharge_start" : discharge_start,
        "discharge_end" : discharge_end,
        "charge_temp" : charge_temp,
        "num_tanks" : ntanks,
        "trim_temp" : trim_temp,
        "size_fraction": float(size_fraction),
        "storage_medium" : medium
    }

    # Handle storage details
    tes_type = 'ThermalTank-Ice'
    if sensible_only:
        tes_type = 'ThermalTank-ChilledWater'
        arguments['store_ice'] = False
        if charge_temp is None:
            arguments['charge_temp'] = sensible_only_charge_temp[medium]
    else:
        arguments['store_ice'] = True
        if charge_temp is None:
            arguments['charge_temp'] = sensible_and_latent_charge_temp[medium]

    if output:
        #run_baseline = True
        measures_only = False

    # Run the ice tank
    post = [stor4build.Step('Add ThermalTank Outputs', 'add_thermaltank_outputs', {'baseline': False})]
    if cooling_season_only:
        post.append(stor4build.Step('Run Cooling Season Only', 'run_cooling_season_only'))
    if control == 'default':
        pass
    else:
        measure_name = control
        if control == 'demo12to6':
            measure_name = 'add_demo_noon_to_six'
        # For this to work, the measure will need to be in the measures directory
        control_measure_path = os.path.join(measures_dir, measure_name, 'measure')
        if os.path.exists(control_measure_path + '.py') or os.path.exists(control_measure_path + '.rb'):
            # Found it!
            post.append(stor4build.Step(measure_name.replace('_', ' ').title(), measure_name, {'tes_type': tes_type, 
                                                                                               'plugin_directory': os.path.join(run_dir, 'icetank')}))
            post.append(stor4build.Step('Add Path To Plugin Paths', 'add_path_to_plugin_paths', {'path': os.path.join(run_dir, 'icetank')}))
        else:
            warnings.warn(f'Failed to find measure "{measure_name}", default control will be used.')
        
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
            txt = stor4build.combine_single_frequency_csv(baseline_csv, icetank_csv, 'Hourly')
        else:
            txt = stor4build.single_frequency_csv(icetank_csv, 'Hourly', verbose=False)
        with open(output, 'w') as fp:
            fp.write(txt)

# Begin dynamic charge controls
@click.command(name='run-icetank-dynamic')
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
@click.option('-c', '--cooling-season-only', is_flag=True, show_default=True, default=False, help='Run only in cooling season.')
@click.option('--medium', type=click.Choice(['water', 'simplewater', 'pcm2x2a']), default='water', show_default=True,
              help='Set the storage medium to use.')
@click.option('--size-fraction', metavar='F', type=click.Choice(['1', '0.9', '0.8', '0.7', '0.6', '0.5']), show_default=True,
              default='0.8', help='Fraction to use to downsize the chiller.')
@click.option('--control', metavar='NAME', show_default=True,
              default='default', help='Specify a built-in control scheme (default | demo12to6) or a measure that implements the scheme.')
@click.option('--sensible-only', is_flag=True, show_default=True, default=False, help='Utilize sensible storage only.')
# @click.option('--schedule-file', type=str, default=os.path.abspath(os.path.join(os.getcwd(), 'resources', 'baseline_schedule_15min.csv')), help='File path to CSV schedule for schedule-based control.')
@click.option('--schedule-file', type=str, default='resources/baseline_schedule_15min.csv', help='File path to CSV schedule for schedule-based control.')
@click.option('--timestep', type=int, default=15, help='Timestep in minutes for the schedule file.')
@click.option('--demand-charge-schedule', type=str, default=None, help='Comma-separated list for demand charge schedule.')
@click.option('--demand-charge-rate', type=str, default=None, help='Comma-separated list for demand charge rate.')
@click.option('--electric-rate', type=str, default=None, help='Comma-separated list for electricity rate.')
def run_icetank_dynamic(osm, epw, openstudio, run_dir, measures_dir, output, measures_only,
                charge_start, charge_end, discharge_start, discharge_end, charge_temp, ntanks, trim_temp, run_baseline,
                cooling_season_only, medium, size_fraction, control, sensible_only, schedule_file, timestep,
                demand_charge_schedule, demand_charge_rate, electric_rate):
    """
    Add an ice tank TES system to an OpenStudio model and run it.
    """
    print("Running icetank with dynamic charge controls")

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
        "size_fraction": float(size_fraction),
        "storage_medium" : medium,
        # add args for dynamic controls
        "chrg_temp_sch_file" : os.path.abspath(schedule_file),
        "timestep_min" : str(timestep)
    }

    # convert 
    # from pathlib import PureWindowsPath
    # schedule_file = str(PureWindowsPath(schedule_file))
    print(f"Schedule file is {schedule_file}")


    # Override the control variable to use the new measure folder
    control = 'add_pytank_with_schedule'

    # Handle storage details
    tes_type = 'ThermalTank-Ice'
    if sensible_only:
        tes_type = 'ThermalTank-ChilledWater'
        arguments['store_ice'] = False
        if charge_temp is None:
            arguments['charge_temp'] = sensible_only_charge_temp[medium]
    else:
        arguments['store_ice'] = True
        if charge_temp is None:
            arguments['charge_temp'] = sensible_and_latent_charge_temp[medium]

    if output:
        #run_baseline = True
        measures_only = False

    # Run the ice tank
    post = [stor4build.Step('Add ThermalTank Outputs', 'add_thermaltank_outputs', {'baseline': False})]
    if cooling_season_only:
        post.append(stor4build.Step('Run Cooling Season Only', 'run_cooling_season_only'))
    
    # Setup the control measure path
    control_measure_path = os.path.join(measures_dir, control, 'measure')
    if os.path.exists(control_measure_path + '.py') or os.path.exists(control_measure_path + '.rb'):
        post.append(stor4build.Step(control.replace('_', ' ').title(), control, {'tes_type': tes_type, 
                                                                                'plugin_directory': os.path.join(run_dir, 'icetank')}))
        post.append(stor4build.Step('Add Path To Plugin Paths', 'add_path_to_plugin_paths', {'path': os.path.join(run_dir, 'icetank')}))
    else:
        warnings.warn(f'Failed to find measure "{control}", default control will be used.')

    # =========================================================
    # STEP 1: Run First Simulation (No Charging / Baseline)
    # =========================================================
    icetank_step1 = stor4build.IceTank('icetank', post_steps=post, **arguments)
    osw_step1 = icetank_step1.osw(osm, measures_dir, epw)
    
    # Define the directory for the first run
    no_charging_dir = os.path.join(run_path, icetank_step1.tag(), 'no_charging')
    
    # Run workflow. Note: OpenStudio workflow typically saves E+ outputs into a 'run' subfolder inside the target directory.
    stor4build.run_workflow(openstudio, no_charging_dir, osw_step1, measures_only=measures_only)
    
    # The E+ output CSV from step 1
    step1_eplusout_csv = os.path.join(no_charging_dir, 'run', 'eplusout.csv')

    # =========================================================
    # STEP 2: Generate Dynamic Schedule
    # =========================================================
    # Import the function from dynamic_charge_controls.py
    from stor4build.dynamic_charge_controls import generate_schedule
    
    if not measures_only:
        # Parse rate options if provided
        dcs = [float(x) for x in demand_charge_schedule.split(',')] if demand_charge_schedule else None
        dcr = [float(x) for x in demand_charge_rate.split(',')] if demand_charge_rate else None
        er = [float(x) for x in electric_rate.split(',')] if electric_rate else None

        # Generate the new schedule using the output directory from Step 1.
        # We point to the 'run' subfolder because that's where OpenStudio saves the IDF and E+ output files.
        new_schedule_file = generate_schedule(os.path.join(no_charging_dir, 'run'), demand_charge_schedule=dcs, demand_charge_rate=dcr, electric_rate=er)
    else:
        # Fallback if we only generated measures and didn't simulate
        new_schedule_file = os.path.abspath(schedule_file)

    # =========================================================
    # STEP 3: Run Second Simulation (Dynamic Schedule)
    # =========================================================
    # Update arguments with the newly generated schedule
    arguments["chrg_temp_sch_file"] = os.path.abspath(new_schedule_file)
    
    # Re-instantiate the IceTank with the updated arguments
    icetank = stor4build.IceTank('icetank', post_steps=post, **arguments)
    osw = icetank.osw(osm, measures_dir, epw)
    
    # Run the final workflow in the primary directory
    stor4build.run_workflow(openstudio, os.path.join(run_path, icetank.tag()), osw, measures_only=measures_only)



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
@click.option('-c', '--cooling-season-only', is_flag=True, show_default=True, default=False, help='Run only in cooling season.')
@click.option('--medium', type=click.Choice(['water', 'simplewater', 'pcm2x2a']), default='water', show_default=True,
              help='Set the storage medium to use.')
@click.option('--size-fraction', metavar='F', type=click.Choice(['1', '0.9', '0.8', '0.7', '0.6', '0.5']), show_default=True,
              default='1', help='Fraction to use to downsize the chiller.')
@click.option('--sensible-only', is_flag=True, show_default=True, default=False, help='Utilize sensible storage only.')
def size_icetank(osm, epw, openstudio, run_dir, measures_dir, output,
                 charge_start, charge_end, discharge_start, discharge_end, charge_temp, peak_reduction, show_sizing,
                 cooling_season_only, medium, size_fraction, sensible_only):
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
        "size_fraction": float(size_fraction),
        "storage_medium" : medium
    }

    # Handle storage details
    if sensible_only:
        arguments['store_ice'] = False
        if charge_temp is None:
            arguments['charge_temp'] = sensible_only_charge_temp[medium]
    else:
        arguments['store_ice'] = True
        if charge_temp is None:
            arguments['charge_temp'] = sensible_and_latent_charge_temp[medium]
    
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
        txt = stor4build.combine_single_frequency_csv(baseline_csv, icetank_csv, 'Hourly')
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

    # Run the baseline if requested
    if run_baseline:
        post=[stor4build.Step('Add DX Coil Outputs', 'add_dx_coil_outputs', arguments={'baseline': True})]
        baseline = stor4build.Simulation('baseline', pre_steps=pre, post_steps=post)
        osw = baseline.osw(osm, measures_dir, epw)
        stor4build.run_workflow(openstudio, os.path.join(run_path, baseline.tag()), osw, measures_only=measures_only)

    # Run the DX coil model
    post=[stor4build.Step('Add DX Coil Outputs', 'add_dx_coil_outputs', arguments={'baseline': False})]
    if show_sizing or output:
        post.append(stor4build.Step('Get DX Coil Sizes', 'get_dx_coil_sizes'))
    dxcoil = stor4build.DxCoil('dxcoil', pre_steps=pre, hourly=False, post_steps=post)
    osw = dxcoil.osw(osm, measures_dir, epw)
    stor4build.run_workflow(openstudio, os.path.join(run_path, dxcoil.tag()), osw, measures_only=measures_only)
    
    report_dir = os.path.join(run_path, dxcoil.tag(),'reports')
    
    if show_sizing:
        print('# Sizing Information #')
        sizing_report_path = os.path.join(report_dir, 'get_dx_coil_sizes_report.csv')
        with open(sizing_report_path, 'r') as fp:
            names = next(fp).split(',')
            values = next(fp).split(',')
        for name, size in zip(names, values):
            print(name.strip()+': '+size.strip()+' (GJ)')
    
    # Combine the CSVs
    if output:
        header = stor4build.prepare_detailed_header('Unknown', 'Unknown', 'Unknown', 'PackagedIceStorage',
                                                    storage_medium='water', report_dir=report_dir,
                                                    sizing=None, arguments=None)
        baseline_csv = os.path.join(run_path, baseline.tag(),'run', 'eplusout.csv')
        dxcoil_csv = os.path.join(run_path, dxcoil.tag(),'run', 'eplusout.csv')
        txt = stor4build.combine_single_frequency_csv(baseline_csv, dxcoil_csv, 'Hourly')
        with open(output, 'w') as fp:
            fp.write(header)
            fp.write(txt)

@click.group(context_settings={'help_option_names': ['-h', '--help']}, invoke_without_command=False)
@click.version_option(version=__version__, prog_name='stor4build')
@click.pass_context
def s4b(ctx: click.Context):
    pass

s4b.add_command(run)
s4b.add_command(process)
s4b.add_command(run_icetank)
s4b.add_command(size_icetank)
s4b.add_command(run_dxcoil)
s4b.add_command(run_icetank_dynamic) 