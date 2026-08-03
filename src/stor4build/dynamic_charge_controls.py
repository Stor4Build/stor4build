# SPDX-FileCopyrightText: 2026-present Lawrence Berkeley National Laboratory

import pandas as pd
import numpy as np
import datetime
from datetime import timedelta
import matplotlib.pyplot as plt
import traceback
import os
import re
import collections
import sys

debug = False

def read_eplusout_skip_sizing(file_path, date_column = 'Date/Time'):
    """
    Reads eplusout.csv file and skips the sizing rows where the specified date_column has a year of "0000".

    Parameters:
    - file_path: str, path to the CSV file
    - date_column: str, name of the column containing date strings

    Returns:
    - df: pandas.DataFrame, containing only rows with valid dates
    """
    # Open the file and read line by line to find the first valid row
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Find the index of the first valid row
    start_index = 0
    for i, line in enumerate(lines):
        if date_column in line.split(',')[0]:  # Check if this is the header row
            continue
        date_str = line.split(',')[lines[0].split(',').index(date_column)].strip()
        if not date_str.startswith('0000-'):
            start_index = i
            break

    # Read the CSV file starting from the valid row
    # Note: cols with "ZN" or "(Hourly)" are ignored because these are not useful for this analysis and can cause confusion later
    df = pd.read_csv(file_path, skiprows=range(1,start_index), usecols=lambda col: (("ZN" not in col) and ("(Hourly)" not in col)))

    return df


def quadratic(x, *coeffs):
    """
    Evaluate a quadratic function.

    This function can be called in two ways:
    1. With separate coefficients: quadratic(x, a, b, c)
    2. With a list or tuple of coefficients: quadratic(x, [a, b, c])

    Parameters:
    - x: float, the independent variable.
    - a, b, c: float, coefficients for the function OR a list [a, b, c]

    Returns:
    - float: The result of the quadratic equation a + bx + cx^2.
    
    Raises:
    - TypeError: If the coefficients are not provided in one of the two valid formats.
    """
    # Case 1: Separate arguments (a, b, c)
    if len(coeffs) == 3:
        a, b, c = coeffs
    # Case 2: A single list or tuple of 3 elements [a, b, c]
    elif len(coeffs) == 1 and isinstance(coeffs[0], (list, tuple)) and len(coeffs[0]) == 3:
        a, b, c = coeffs[0]
    else:
        raise TypeError("Invalid arguments. Coefficients must be either 3 floats or a list of 3 floats")
    
    return a + b * x + c * x**2


def biquadratic(x,y,*coeffs):
    """
    Evaluate a biquadratic function of two variables.

    Parameters:
    - x: float, first independent variable
    - y: float, second independent variable
    - a, b, c, d, e, f: float, coefficients for the function OR a list [a, b, c, d, e, f]

    Returns:
    - float, the result of a + bx + cx^2 + dy + ey^2 + fxy
    """
    if len(coeffs) ==6:
        a,b,c,d,e,f = coeffs
    elif len(coeffs)==1  and isinstance(coeffs[0], (list, tuple)) and len(coeffs[0]) == 6:
        a,b,c,d,e,f = coeffs[0]
    else: raise TypeError("Invalid arguments. Coefficients must be either 6 floats or a list of 6 floats")
    return a + b*x + c*x**2 + d*y + e*y**2 + f*x*y


# Constants for this particular system (LargeOffice_new.osm)
# Note: these are PER CHILLER, and there are 2 chillers
# TODO: figure out how to get this automatically
# design_capacity = 1505041.80 #W
# design_capacity_kW = 1505.04180 #kW
# full_load_power = 225840.67 #W


def getCOPstaged(load, T_cw, info, T_cond=25):
    """
    Calculate the COP of 2+ staged chillers, based on the criteria E+ uses.
    Assumes chillers are identical

    Parameters:
    - load: float or pd.Series, thermal load on chiller, kW
    - T_cw: float or pd.Series, chilled water temperature, °C
    - T_cond: float, condenser side temperature, °C
    - info: dictionary as specified in getCOP

    Returns:
    - float or pd.Series with the calculated COP
    """
    COP_ref = info["cop_ref"]
    design_capacity_kW = info["design_capacity_kW"]
    min_PLR = info['min_plr']
    min_unloading = info['min_ur']
    num_chillers = info['num_chillers']
    def calculate_cop_single_load(single_load):
        """
        Calculate the COP for a single load across staged chillers.

        Parameters:
        - single_load: float, the thermal load to be distributed across chillers

        Returns:
        - float, the combined COP of the staged system
        """
        if single_load <= 0: return COP_ref #987654.3
        remaining_load = single_load
        COP_list = []
        c = 0
        chiller_load = np.zeros(num_chillers)
        PLR = np.zeros(num_chillers)
        EIRfPLR = np.zeros(num_chillers)
        EIRfT = biquadratic(T_cw, T_cond, info['eirft_coeffs']) # EIRfT is constant
        COP = np.ones(num_chillers)
        while remaining_load > 0 and c < num_chillers:
            chiller_load[c] = min(remaining_load, design_capacity_kW )
            remaining_load = remaining_load - chiller_load[c]
            if (remaining_load > 0) & (remaining_load < design_capacity_kW*min_PLR):
                chiller_load[c] -= design_capacity_kW*min_PLR - remaining_load
                remaining_load += design_capacity_kW*min_PLR - remaining_load
            PLR[c] = chiller_load[c]/design_capacity_kW
            if PLR[c] < min_PLR:
                PLR[c] = min_PLR
            EIRfPLR[c] = quadratic(PLR[c], info['fqratio_coeffs'])
            COP[c] =  (COP_ref * PLR[c]) / (EIRfPLR[c] * EIRfT)
            c += 1
        return sum(chiller_load) / sum(chiller_load/COP)

    if isinstance(load, pd.Series):
        return load.apply(calculate_cop_single_load)
    else:
        return calculate_cop_single_load(load)


def getCOPpaired(load, T_cw, info, T_cond=25):
    """
    Calculate the COP of paired chillers (both run in sync), based on the criteria E+ uses.
    Assumes chillers are identical

    Parameters:
    - load: float or pd.Series, thermal load on chiller, kW
    - T_cw: float or pd.Series, chilled water temperature, °C
    - T_cond: float, condenser side temperature, °C
    - info: dictionary as specified in getCOP

    Returns:
    - float or pd.Series with the calculated COP
    """
    COP_ref = info["cop_ref"]
    # print(f"COP_ref = {COP_ref}")
    design_capacity_kW = info["design_capacity_kW"]
    min_PLR = info['min_plr']
    min_unloading = info['min_ur']
    num_chillers = info['num_chillers']
    def calculate_cop_single_load(single_load):
        """
        Calculate the COP for a single load using paired chiller operation.

        Parameters:
        - single_load: float, the thermal load to be distributed across chillers

        Returns:
        - float, the COP for the paired configuration
        """
        if single_load <= 0: return COP_ref #987654.3
        PLR = max(single_load/(design_capacity_kW*num_chillers), min_unloading)
        EIRfPLR = quadratic(PLR, info['fqratio_coeffs'])
        EIRfT = biquadratic(T_cw, T_cond, info['eirft_coeffs'])
        COP =  (COP_ref * PLR) / (EIRfPLR * EIRfT)
        return COP

    if isinstance(load, pd.Series):
        return load.apply(calculate_cop_single_load)
    else:
        return calculate_cop_single_load(load)

def getCOPoptimal(load, T_cw, info, T_cond=25):
    """
    Calculate the COP of 2+ chillers running in the current optimal configuration,
    defined as whichever of paired or staged configuration has the higher COP
    Assumes chillers are identical

    Parameters:
    - load: float or pd.Series, thermal load on chiller, kW
    - T_cw: float or pd.Series, chilled water temperature, °C
    - T_cond: float, condenser side temperature, °C
    - info: dictionary as specified in getCOP

    Returns:
    - float or pd.Series with the calculated COP
    """
    return max( getCOPstaged(load, T_cw, info, T_cond),  getCOPpaired(load, T_cw, info, T_cond))


def getCOP(load, T_cw, info, T_cond=25):
    """
    Wrapper function that calculates the COP (currently using the paired chiller configuration, but can easily be pointed to a different configuration as needed)

    Parameters:
    - load: float or pd.Series, thermal load on chiller, kW
    - T_cw: float or pd.Series, chilled water temperature, °C
    - T_cond: float, condenser side temperature, °C
    - info: dict that contains variables to represent these items
        - COP_ref: float, reference COP constant for chiller
        - design_capacity_kW: float, reference design capacity for chiller
        - min_PLR: float, minimum PLR at which chiller can operate
        - min_unloading: float, the unloading ratio for the chiller
        - num_chillers: int, number of chillers
        - eirft_coeffs: list of 6 floats
        - fqratio_coeffs: list of 3 floats

    Returns:
    - float or pd.Series with the calculated COP
    """
    return getCOPpaired(load, T_cw, info, T_cond)




def get_chiller_design_capacities(eio_path):
    """
    Extracts the Initial Design Size Reference Capacity [W] for all
    Chiller:Electric:EIR components from an .eio file.

    Parameters:
    - eio_path: str, path to the EnergyPlus .eio output file

    Returns:
    - list, a list of design capacities (float) for each chiller found
    """
    if debug: print(f"[dynamic_charge_controls] run\nget_chiller_design_capacities({eio_path})")

    capacities = collections.OrderedDict()
    # target_field = "Initial Design Size Reference Capacity [W]"
    target_object = "Chiller:Electric:EIR"

    with open(eio_path, 'r') as f:
        for line in f:
            # Split by comma and strip whitespace
            parts = [p.strip() for p in line.split(',')]
            
            # Ensure line has enough parts and matches our criteria
            if len(parts) >= 5:
                if parts[0] == "Component Sizing Information" and parts[1] == target_object:
                    chiller_name = parts[2]
                    # field_name = parts[3]
                    value = parts[4]
                    
                    # if field_name == target_field:
                    if "Design Size Reference Capacity [W]" in parts[3]:
                        capacities[chiller_name] = float(value)
    # TODO: code a fallback if no valid info found
    return list(capacities.values())


def get_idf_info(file_path):
    """
    Parse an IDF file to extract chiller specifications and simulation run periods.

    Parameters:
    - file_path: str, path to the .idf file

    Returns:
    - dict, contains start_date, end_date, eirft_coeffs, fqratio_coeffs, num_chillers, cop_ref, min_plr, and min_ur
    """
    if debug: print(f"[dynamic_charge_controls] run\nget_idf_info({file_path})")

    with open(file_path, 'r') as f:
        content = f.read()

    # Initialize all outputs to None/0 to ensure the function always returns the same structure
    start_date = None
    end_date = None
    eirft_coeffs = [0.6772577,0.0117857,-0.0001967, 0.0014414, 0.0003005, -0.0006807]
    fqratio_coeffs = [0.222149, 0.503156,0.256905]
    num_chillers = 0
    cop_ref = 6
    min_plr = 0.15
    min_ur = 0.25

    # --- RunPeriod ---
    rp_match = re.search(r'RunPeriod,.*?;', content, re.DOTALL)
    if rp_match:
        # Clean the block into a list of values, removing comments and trailing commas
        lines = [line.split('!')[0].strip().rstrip(',') for line in rp_match.group(0).split('\n') if line.strip()]

        # Drop the object type line ("RunPeriod") itself, keeping only the field values
        if lines and lines[0].strip().lower() == 'runperiod':
            lines = lines[1:]

        try:
            # Based on IDF schema for RunPeriod:
            # Index 0: Name
            # Index 1: Begin Month, 2: Begin Day, 3: Begin Year
            # Index 4: End Month, 5: End Day, 6: End Year
            # Note: detected off-by-one error, so indexes had to be decremented manually by 1
            start_date = f"{lines[3]}-{lines[1].zfill(2)}-{lines[2].zfill(2)}"
            end_date = f"{lines[6]}-{lines[4].zfill(2)}-{lines[5].zfill(2)}"
            if debug: print(f"RunPeriod: {start_date}   to   {end_date}")
        except (IndexError, AttributeError):
            print("[dynamic_charge_controls] Warning: RunPeriod data malformed")

    # --- Curves ---
    # EIRFT (Biquadratic)
    # for block in re.finditer(r'OS:Curve:Biquadratic,.*?;', content, re.DOTALL):
    for block in re.finditer(r'Curve:Biquadratic,.*?;', content, re.DOTALL):
        text = block.group(0)
        if "EIRFT" in text:
            lines = [line.split('!')[0].strip().rstrip(',') for line in text.split('\n') if line.strip()]
            # Index 0: Class, 1: Handle, 2: Name, 3-8: Coefficients
            eirft_coeffs = lines[2:8]
            eirft_coeffs = [float(coeff) for coeff in eirft_coeffs]
            if debug: 
                print(f'Found EIRFT: {text}')
                print(f'eirft_coeffs: {eirft_coeffs}')
            break

    # fQRatio (Quadratic)
    for block in re.finditer(r'Curve:Quadratic,.*?;', content, re.DOTALL):
        text = block.group(0)
        if "fQRatio" in text:
            lines = [line.split('!')[0].strip().rstrip(',') for line in text.split('\n') if line.strip()]
            # Index 0: Class, 1: Handle, 2: Name, 3-5: Coefficients
            fqratio_coeffs = lines[2:5]
            fqratio_coeffs = [float(coeff) for coeff in fqratio_coeffs]
            if debug: 
                print(f'Found fQRatio: {text}')
                print(f'fqratio_coeffs: {fqratio_coeffs}')
            break
    
    # --- Chiller Info ---
    # Count chillers: Only match "Chiller:Electric:EIR" if it starts a line (or follows a semicolon/newline)
    # This prevents counting the string if it appears inside a name or comment.
    num_chillers = len(re.findall(r'(?:^|\n)Chiller:Electric:EIR,', content))

    if debug: print(f"Found {num_chillers} chillers")

    chiller_match = re.search(r'Chiller:Electric:EIR,\n.*?;', content, re.DOTALL)
    if chiller_match:
        # if debug: print(f'Found chiller_match: {chiller_match}')
        lines = [line.split('!')[0].strip().rstrip(',') for line in chiller_match.group(0).split('\n') if line.strip()]
        try:
            # Index 0: Class name
            # Index 1: Name
            # Index 2: Reference Capacity
            # Index 3: Reference COP
            cop_ref = float(lines[3])
            # Index 11: Minimum Part Load Ratio
            # Index 14: Minimum Unloading Ratio
            min_plr = float(lines[11])
            min_ur = float(lines[14])
        except IndexError:
            print("[dynamic_charge_controls] Warning: Chiller:Electric:EIR section not found or bad data")
        except ValueError:
            print("[dynamic_charge_controls] Warning: Invalid data for one of these: ")
            print(f"   cop_ref: {lines[3]}")
            print(f"   min_plr: {lines[11]}")
            print(f"   min_ur: {lines[14]}")

    # return start_date, end_date, eirft_coeffs, fqratio_coeffs, num_chillers, cop_ref, min_plr, min_ur
    return {
        "start_date": start_date,
        "end_date": end_date,
        "eirft_coeffs": eirft_coeffs,
        "fqratio_coeffs": fqratio_coeffs,
        "num_chillers": num_chillers,
        "cop_ref": cop_ref,
        "min_plr": min_plr,
        "min_ur": min_ur
    }


def get_icetank_specs(num_tanks):
    """
    Calculate ice tank specifications based on the number of tanks. NOTE: Future development should get this from the icetank definitions rather than hardcoded values for robustness. This seems to work for now.

    Parameters:
    - num_tanks: int, number of ice storage tanks

    Returns:
    - dict, contains total_capacity, usable_TES_capacity, discharge_rate, charge_rate, loss_rate, and Q_env
    """

    total_capacity = 668*num_tanks #kWh
    usable_TES_capacity = total_capacity*0.85 # assume 85% is usable
    # print('Max allowed storage: ', usable_TES_capacity, ' kWh')

    discharge_rate = (0.9996-0.1737)/(3+20/60) * usable_TES_capacity * 0.85
    # print('Discharge rate: ', discharge_rate, ' kW')

    charge_rate = (0.8012-0.1340)/(4+10/60) * usable_TES_capacity *0.85
    # print('Charge rate: ', charge_rate, ' kW')

    loss_rate = (0.99176 - 0.98849)/(6+10/60) * usable_TES_capacity * num_tanks
    # print('loss rate: ', loss_rate, ' kW')

    Q_env = 14.97667276295127 * (20 - 0)
    # print('loss rate calculated Q_env at T_tank = 0 degC: ', Q_env, ' W')

    return {
        "total_capacity": total_capacity,
        "usable_TES_capacity": usable_TES_capacity,
        "discharge_rate": discharge_rate,
        "charge_rate": charge_rate,
        "loss_rate": loss_rate,
        "Q_env": Q_env,
    }

def generate_electricity_prices(electric_rate, demand_charge_schedule, demand_charge_rate, info):
    """
    Generate a yearly electricity price and demand charge schedule. 
    NOTE: This function may be replaced later on with something more sophisticated. 

    Parameters:
    - electric_rate: list or array, 24-hour electricity rates in $/kWh
    - demand_charge_schedule: list or array, 24-hour demand charge period schedule, with different periods mapped to integers. The lowest cost period should be `0`, then the next highest `1`, `2`, etc.
    - demand_charge_rate: list, rates for different demand periods and overall demand. The indexes map to the numbering in demand_charge_schedule, such that the lowest cost period demand charge is in index 0, then the next highest in index 1, etc. The length should be 1 more than the number of different demand_charge_schedule periods. The final entry, index -1, is an overall demand charge applied to the highest consumption regardless of time. Any of these may be 0, but all must be included for the code to work correctly. 
    - info: dict, contains simulation timing information (start_date, end_date, timestep_s)

    Returns:
    - pd.DataFrame, containing datetime, Electricity Rate [$/kWh], Demand Period, and Overall Demand Rate [$/kW]
    """
    def np_extend_repeat(arr, target_length):
        """
        Extend an array by repeating its elements sequentially until the target length is reached.

        Parameters:
        - arr: np.array, the base array to repeat
        - target_length: int, the desired final length of the array

        Returns:
        - np.array, the extended array
        """
        i = 0
        while len(arr) < target_length:
            arr = np.append(arr, arr[i])
            i += 1
        return arr

    # info['end_date'] is a date-only string (e.g. '2006-12-31'), which pandas interprets as midnight.
    # Extend through the end of that final day so the resulting time_index covers the same span as the
    # hourly-resampled baseline dataframe (which runs through 23:00 on the last day).
    end_of_last_day = pd.Timestamp(info['end_date']) + pd.Timedelta(days=1) - pd.Timedelta(seconds=info['timestep_s'])
    time_index = pd.date_range(start=info['start_date'], end=end_of_last_day, freq=f"{info['timestep_s']}s")
    num_timesteps = len(time_index) / int(3600/info["timestep_s"])

    electric_rate = np_extend_repeat(np.array(electric_rate), num_timesteps)
    electric_rate = np.repeat(electric_rate, int(3600/info["timestep_s"]))
    demand_charge_schedule = np_extend_repeat(np.array(demand_charge_schedule), num_timesteps)
    demand_charge_schedule = np.repeat(demand_charge_schedule, int(3600/info["timestep_s"]))

    df = pd.DataFrame({'datetime': time_index, 'Electricity Rate [$/kWh]': electric_rate, 'Demand Period': demand_charge_schedule})

    df['Overall Demand Rate [$/kW]'] = demand_charge_rate[-1]

    return df


# Calculate demand charge
# demand charge will only be the incremental over the next highest hour for purposes of algorithm
# demand_charge_rate = [group0, group1, group2, ..., overall]
def applyDemandCharge(df_in, demand_charge_rate, cost='Electricity Rate [$/kWh]', elec = 'Electricity Consumption', demandWindow='Demand Period', demandCost='Demand Cost', debug=False):
    """
    Calculate and apply demand charges to a power consumption dataframe.

    Parameters:
    - df_in: pd.DataFrame, input dataframe containing power consumption and demand windows
    - demand_charge_rate: list, rates for different demand charge periods
    - cost: str, column name for electricity rate
    - elec: str, column name for electricity consumption
    - demandWindow: str, column name for the demand charge period schedule
    - demandCost: str, output column name for calculated demand costs
    - debug: bool, whether to print debug information

    Returns:
    - tuple (pd.DataFrame, list), the modified dataframe and a list of peak consumption levels per window
    """
    df = df_in.copy()
    df[demandCost] = 0.0
    curr_max_elec = [0]*len(demand_charge_rate)
    # overall demand charge
    # elec_max = max(df[elec])
    diff = df[elec].nlargest(1).iloc[-1] - df[elec].nlargest(2).iloc[-1]
    # print(df[elec].nlargest(1).iloc[-1], df[elec].nlargest(2).iloc[-1], diff)
    if debug:
        print('overall: ')
        print('Largest consumption: ', df[elec].nlargest(1).iloc[-1], ' at datetime: ', df['datetime'].loc[df[elec] == df[elec].nlargest(1).iloc[-1]])
        print('Next largest consumption: ', df[elec].nlargest(2).iloc[-1], ' at datetime: ', df['datetime'].loc[df[elec] == df[elec].nlargest(2).iloc[-1]])
    df.loc[df[elec] == df[elec].nlargest(1).iloc[-1], demandCost] += demand_charge_rate[-1] * diff
    # save next highest as the limit
    curr_max_elec[-1] = df[elec].nlargest(2).iloc[-1]
    # demand charges for each window
    for j in range(len(demand_charge_rate)-1):
        temp = df.loc[df[demandWindow]==j]
        diff = temp[elec].nlargest(1).iloc[-1] - temp[elec].nlargest(2).iloc[-1]
        if debug:
            print('i = ', j)
            print('Largest consumption: ', temp[elec].nlargest(1).iloc[-1], ' at datetime: ', temp['datetime'].loc[temp[elec] == temp[elec].nlargest(1).iloc[-1]])
            print('Next largest consumption: ', temp[elec].nlargest(2).iloc[-1], ' at datetime: ', temp['datetime'].loc[temp[elec] == temp[elec].nlargest(2).iloc[-1]])
        # df[demandCost].loc[df[elec] == temp[elec].nlargest(1).iloc[-1]] += demand_charge_rate[i] * diff
        df.loc[df[elec] == temp[elec].nlargest(1).iloc[-1], demandCost] += demand_charge_rate[j] * diff
        # save the highest as the limit
        curr_max_elec[j] = temp[elec].nlargest(2).iloc[-1]
        # df['inc_cost'] = df[cost] + df[demandCost]
        df.loc[:,'inc_cost'] = df[cost] + df[demandCost] # this is an artificial total cost
    
    return df, curr_max_elec


def preprocess_baseline(baseline_run_path, demand_charge_schedule=None, demand_charge_rate=None, electric_rate=None, epw_file=None):
    """
    Process baseline simulation results to set up baseline data dataframes and info dictionary.

    Parameters:
    - baseline_run_path: str, path to the folder containing EnergyPlus output files
    - demand_charge_schedule: array, optional custom demand charge schedule
    - demand_charge_rate: list, optional custom demand charge rates
    - electric_rate: list, optional custom electricity rates
    - epw_file: str, optional path to weather file for fallback OAT data

    Returns:
    - tuple (pd.DataFrame, dict), processed baseline dataframe and a dictionary of system specifications
    """

    print(f'[dynamic_charge_controls] Processing baseline from: {baseline_run_path}')
    if debug: print(f"[dynamic_charge_controls] run\npreprocess_baseline({baseline_run_path}, {demand_charge_schedule}, {demand_charge_rate}, {electric_rate}, {epw_file})")

    info = get_idf_info(os.path.join(baseline_run_path, "in.idf"))

    info["chiller_capacities"] = get_chiller_design_capacities(os.path.join(baseline_run_path, "eplusout.eio"))
    if len(info["chiller_capacities"]) < 1:
        print(f'[dynamic_charge_controls] got chiller capacities of {info["chiller_capacities"]}')
        print('Check if EnergyPlus was able to run in.idf (check err file) before checking get_chiller_design_capacities')
    
    info["design_capacity_kW"] = info["chiller_capacities"][0]/1000 # assume all chillers are the same and convert W to kW

    file_path = os.path.join(baseline_run_path, "eplusout.csv")
    df = read_eplusout_skip_sizing(file_path, date_column = 'Date/Time')

    # init smaller processed dataframe
    dfc = pd.DataFrame()
    dfc['datetime'] = pd.to_datetime(df['Date/Time'], format='ISO8601').copy(deep=True)

    timestep_s = (dfc['datetime'].iloc[1] - dfc['datetime'].iloc[0]).total_seconds()
    info["timestep_s"] = timestep_s

    info["year"] = dfc['datetime'].iloc[0].year

    num_tanks = df["NUM TANKS:Schedule Value [](TimeStep)"].iloc[0]
    info["num_tanks"] = num_tanks

    icetank_specs = get_icetank_specs(num_tanks)
    info = {**info, **icetank_specs} #info | icetank_specs # merge dicts. Using syntax that works for older Python versions just in case

    # attempt to get weather data, if not, fallback to epw file
    try:
        dfc['Dry Bulb Temperature'] = df['Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)']
    except KeyError:
        # Try explicitly provided epw_file first, then fallback to in.epw in baseline_run_path
        epw_path = epw_file if epw_file else os.path.join(baseline_run_path, "in.epw")

        print(f'[dynamic_charge_controls] Warning: No OAT data available in the output file, using epw file: {epw_path}')
        
        a=epw()
        a.read(epw_path)
        dfw=a.dataframe
        dfc['Dry Bulb Temperature'] = dfw['Dry Bulb Temperature']
    
    dfc["Chiller Electricity [W]"] = 0
    dfc["Thermal Load [W]"] = 0
    dfc["Condenser Heat Transfer [W]"] = 0

    # chiller_str = f"WATERCOOLED  CENTRIFUGAL CHILLER {chiller}"
    # chiller_str = f" CHILLER {chiller}"

    def get_chiller_data_col(df, chiller, key_str):
        # Use keyterms in col names to find correct data automatically for any number of chillers
        chiller_str = f" CHILLER {chiller}"
        matching_cols = [col for col in df.columns if all(s in col for s in [chiller_str, key_str])]
        if len(matching_cols) != 1:
            print(f'[dynamic_charge_controls] Warning: got wrong number of columns for Chiller {chiller} {key_str}:\n{matching_cols}')
        return df[matching_cols[0]]

    # chiller data
    for chiller in range(0,info["num_chillers"]):
        dfc[f"ChillerElec{chiller}"] = get_chiller_data_col(df, chiller, ":Chiller Electricity Rate [W](TimeStep)")
        dfc["Chiller Electricity [W]"] += dfc[f"ChillerElec{chiller}"]

        dfc[f"Cond Heat Transfer Chiller{chiller}"] = get_chiller_data_col(df, chiller, ":Chiller Condenser Heat Transfer Rate [W](TimeStep)")
        dfc["Condenser Heat Transfer [W]"] += dfc[f"Cond Heat Transfer Chiller{chiller}"]

        dfc[f"Thermal Load Chiller{chiller}"] = get_chiller_data_col(df, chiller, ":Chiller Evaporator Cooling Rate [W](TimeStep)")
        dfc["Thermal Load [W]"] += dfc[f"Thermal Load Chiller{chiller}"]

        dfc[f"PartLoadRatio{chiller}"] = get_chiller_data_col(df, chiller, ":Chiller Part Load Ratio [](TimeStep)")

        dfc[f"ChillerCOP{chiller}"] = get_chiller_data_col(df, chiller, ":Chiller COP [W/W](TimeStep)")

    dfc["Electricity:Facility [W]"] = df["Electricity:Facility [J](TimeStep)"] / timestep_s

    # NOTE: Resampling here to be compatible with earlier code. There might be a more efficient place to put this
    dfh = dfc.resample('h', on='datetime').mean()
    # resample(..., on='datetime') sets 'datetime' as the index and drops it as a column;
    # keep it as a column too so it survives the set_index() call below unchanged
    dfh['datetime'] = dfh.index
    # fix timestep_s
    info["original_timestep_s"] = info["timestep_s"]
    info["timestep_s"] = 3600

    # TODO: Get electricity prices from some other source, ideally not hardcoded
    if demand_charge_schedule is None:
        demand_charge_schedule = np.array([0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,2,2,2,2,2,1,1,0])
    else:
        demand_charge_schedule = np.array(demand_charge_schedule)

    if demand_charge_rate is None:
        demand_charge_rate = [0,9.92+5.09,45.8+20.36,32+19.11]
    else:
        demand_charge_rate = list(demand_charge_rate)

    if electric_rate is None:
        electric_rate = [0.22663]*14 + [0.29896] * 2 + [0.35709] * 5 +  [0.29896] * 2 + [0.22663]
    else:
        electric_rate = list(electric_rate)

    prices = generate_electricity_prices(electric_rate, demand_charge_schedule, demand_charge_rate, info)
    
    info["demand_charge_schedule"] = demand_charge_schedule
    info["demand_charge_rate"] = demand_charge_rate
    info["electric_rate"] = electric_rate

    dfh.set_index("datetime", inplace=True)
    prices.set_index("datetime", inplace=True)

    if len(dfh) != len(prices):
        print(f"[dynamic_charge_controls] Warning: dfh ({len(dfh)} rows) and prices ({len(prices)} rows) have different lengths; concat may introduce NaNs")

    dfh = pd.concat([dfh, prices] , axis=1)

    # Safety net: if dfh and prices don't perfectly align (e.g. differing lengths), the concat can
    # introduce NaNs which silently upcast integer columns like 'Demand Period' to float. Downstream
    # code uses 'Demand Period' values as list indices, so cast back to int here.
    dfh['Demand Period'] = dfh['Demand Period'].ffill().bfill().astype(int)

    dfh["Thermal Load [kW]"] = dfh["Thermal Load [W]"] / 1000

    dfh['Storage'] = 0.0
    dfh['Cooling'] = dfh['Thermal Load [kW]'] # Do NOT change all instances of 'Cooling' to 'Thermal Load [kW]' -- they will mean different things later on, 'Cooling' is how much cooling it will do in that hour (using storage to make up the diff) whereas 'Thermal Load [kW]' is the building load which can be met by chiller operation or storage.
    # dfh['Demand Charge Schedule'] = dfh['Demand Period'] # changed all of these to 'Demand Period' already
    dfh['COP'] = getCOP(dfh['Thermal Load [kW]'], 6.7, info)
    dfh['Electricity Consumption'] = dfh['Cooling'] / dfh['COP'] # electricity used to meet 'Cooling'; kept in sync with 'Cooling'/'COP' updates made throughout generate_schedule()
    dfh['Cost [kWh]'] = dfh['Electricity Rate [$/kWh]'] * dfh['Electricity Consumption']

    # set_index() above drops 'datetime' as a column (it becomes the index only);
    # restore it as a column too since downstream code (generate_schedule, etc.) expects df['datetime'] to work
    dfh['datetime'] = dfh.index

    return dfh, info

def consolidate_charging_hours(sch, demand_charge_rate):
    """
    Shift isolated single-hour charging events to be extend the beginning or end of an existing period with multi-hour charging to avoid inefficient operation. With the adaptive charge temperature, charging for 1 hour wastes electricity but does not lead to a net increase in SOC. 

    Parameters:
    - sch: pd.DataFrame, the charge schedule containing costs and charging status
    - demand_charge_rate: list, rates for different demand charge periods

    Returns:
    - pd.DataFrame, the updated schedule with consolidated charging hours
    """
    # Calculate the max cost threshold once
    cost_threshold = 0.5 * sch['inc_cost'].max()
    
    # Ensure the dataframe is sorted chronologically before running this
    # sch = sch.sort_index() 

    # Create charging col
    sch['charging'] = sch['Cooling'] - sch['Thermal Load [kW]']

    # Iterate through the DataFrame
    # Starting at index 1 and ending at len-1 to safely check i-1 and i+1
    for i in range(1, len(sch) - 1):
        current_charge = sch['charging'].iloc[i]
        
        # 1. Check for an isolated single charging hour
        is_isolated = current_charge > 0 and sch['charging'].iloc[i-1] <= 0 and sch['charging'].iloc[i+1] <= 0
        
        if is_isolated:
            # Define 24-hour lookback window
            start_idx = max(1, i - 24) 
            
            target_j_idx = None
            lowest_cost_found = float('inf')
            
            # Scan previous 24 hours
            for j in range(start_idx, i):
                # We only want to move the charge to an empty hour
                if sch['charging'].iloc[j] == 0:
                    
                    # Check if it is immediately before or after a previous charging period
                    adjacent_to_charge = sch['charging'].iloc[j-1] > 0 or sch['charging'].iloc[j+1] > 0

                    # add fix to prevent it from counting the current hour as adjacent, since we're trying to remove that
                    if j == i-1:
                        adjacent_to_charge = sch['charging'].iloc[j-1] > 0
                    
                    # Check if the cost is below the 50% max threshold
                    below_threshold = (sch['inc_cost'].iloc[j] < cost_threshold)
                    
                    low_demand_charge = True
                    if len(demand_charge_rate) > 2:
                        low_demand_charge = (demand_charge_rate[sch['Demand Period'].iloc[j]] < max(demand_charge_rate))
                    
                    if adjacent_to_charge and below_threshold and low_demand_charge:
                        # If multiple valid 'j' hours exist, track the one with the lowest cost
                        if sch['inc_cost'].iloc[j] < lowest_cost_found:
                            lowest_cost_found = sch['inc_cost'].iloc[j]
                            target_j_idx = j
            
            # If a qualifying earlier hour was found, execute the shift
            if target_j_idx is not None:
                # Copy the charge to the new earlier hour
                sch.loc[sch.index[target_j_idx], 'charging'] = current_charge
                sch.loc[sch.index[target_j_idx], 'Cooling'] += current_charge
                # Zero out the isolated hour
                sch.loc[sch.index[i], 'charging'] = 0
                sch.loc[sch.index[i], 'Cooling'] -= current_charge
                if debug: print(f"Avoid single-hour operation {sch.loc[sch.index[i], 'datetime']}, shift to hour {sch.loc[sch.index[target_j_idx], 'datetime']}")
            else: # no earlier hour would work
                if debug: print(f"Could not avoid single-hour operation {sch.loc[sch.index[i], 'datetime']} --> deactivate charging anyway")
                sch.loc[sch.index[i], 'charging'] = 0
                sch.loc[sch.index[i], 'Cooling'] -= current_charge

    return sch


def generate_schedule_file(dms, info, file_path):
    """
    Create and save a CSV schedule file for the EnergyPlus simulation.

    Parameters:
    - dms: pd.DataFrame, the optimized schedule data
    - info: dict, simulation information including year and timesteps_per_hour
    - file_path: str, path where the resulting CSV file will be saved

    Returns:
    - None
    """
    if debug: print(f"[dynamic_charge_controls] run\ngenerate_schedule_file({dms}, {info}, {file_path})")

    YEAR = info["year"] 
    timesteps_per_hour = info['timesteps_per_hour'] 

    # --------------------------------------------------------------
    # Convert timesteps_per_hour → pandas frequency string
    # --------------------------------------------------------------
    if 60 % timesteps_per_hour != 0:
        raise ValueError(
            "timesteps_per_hour must divide 60 evenly (e.g. 1,2,3,4,5,6,10,12,15,20,30,60)."
        )

    minutes_per_step = 60 // timesteps_per_hour
    freq_str = f"{minutes_per_step}T"      # 'T' = minute frequency

    # --------------------------------------------------------------
    # Build the datetime range covering the whole year
    # --------------------------------------------------------------
    start = f"{YEAR}-01-01 00:00:00"
    end   = f"{YEAR + 1}-01-01 00:00:00"   # first instant of the next year

    # pandas ≥ 1.4 supports the `inclusive` keyword.
    # For older versions we simply drop the last element after generation.
    try:
        datetime_series = pd.date_range(
            start=start,
            end=end,
            freq=freq_str,
            inclusive='left'          # exclude the final timestamp that equals `end`
        )
    except TypeError:               # pandas version does not accept `inclusive`
        datetime_series = pd.date_range(start=start, end=end, freq=freq_str)[:-1]

    # --------------------------------------------------------------
    # Assemble the DataFrame
    # --------------------------------------------------------------
    df = pd.DataFrame({
        "datetime": datetime_series,
        "mode":     np.zeros(len(datetime_series), dtype=int),
        "chrg_temp":     np.ones(len(datetime_series), dtype=float) * -3.8,
        "idle_temp":     np.ones(len(datetime_series), dtype=float) * 6.7,
        "discharge_temp":     np.ones(len(datetime_series), dtype=int) * 10
    })

    # Insert an explicit integer index column named "index"
    df.reset_index(inplace=True)          # creates column "index" with 0,1,2,...
    df.rename(columns={"index": "index"}, inplace=True)

    # --------------------------------------------------------------
    # Process the subset dataframe (dms)
    # --------------------------------------------------------------
    # 1. Ensure datetime is a pandas datetime object
    dms['datetime'] = pd.to_datetime(dms['datetime'])

    # 2. Rename 'charge_temperature' to match the annual schedule 'chrg_temp'
    #    and isolate only the columns we need to merge
    dms_subset = dms.rename(columns={"charge_temperature": "chrg_temp"})[['datetime', 'mode', 'chrg_temp']].copy()

    # # --------------------------------------------------------------
    # # Apply Daylight Savings Time (DST) Shift
    # # --------------------------------------------------------------
    # # In 2006, US DST started April 2 and ended October 29.
    # dst_start = pd.Timestamp(f'{YEAR}-04-02 02:00:00')
    # dst_end   = pd.Timestamp(f'{YEAR}-10-29 02:00:00')

    # # Create a boolean mask for dates falling within the DST period
    # is_dst = (dms_subset['datetime'] >= dst_start) & (dms_subset['datetime'] < dst_end)

    # # Shift the datetime 1 hour earlier for DST, as specified
    # # Note: If you find that standard time (PST) needs to jump FORWARD to match local PDT, 
    # # simply change `- pd.Timedelta` to `+ pd.Timedelta` below.
    # dms_subset.loc[is_dst, 'datetime'] -= pd.Timedelta(hours=1)

    # --------------------------------------------------------------
    # Integrate into the Annual Schedule (df)
    # --------------------------------------------------------------
    # Set the 'datetime' column as the index for both dataframes to align them properly
    df.set_index('datetime', inplace=True)
    dms_subset.set_index('datetime', inplace=True)

    # Update the blank annual schedule with the values from dms_subset.
    # This strictly updates 'mode' and 'chrg_temp' on matching datetimes 
    # while leaving 'idle_temp' and 'discharge_temp' at their default values.
    # TODO: fix futurewarning on this line. Tried
    # update_cols_dtypes = df[dms_subset.columns].dtypes
    # dms_subset = dms_subset.astype(update_cols_dtypes)
    # and
    # dms_subset = dms_subset.astype({col: df[col].dtype for col in dms_subset.columns})
    df.update(dms_subset)

    # Reset the index to restore 'datetime' as a standard column
    df.reset_index(inplace=True)

    df.to_csv(file_path, index=False)


def generate_schedule(baseline_run_path, demand_charge_schedule=None, demand_charge_rate=None, electric_rate=None, epw_file=None):
    """
    Generates the optimized load shifting schedule using dynamic charge controls. 

    Parameters
    - baseline_run_path: os.path, to "run" folder where the results from the baseline went
    - demand_charge_schedule: list or array, 24-hour demand charge period schedule, with different periods mapped to integers. The lowest cost period should be `0`, then the next highest `1`, `2`, etc. If not provided, will default to a sample schedule. 
    - demand_charge_rate: list, rates for different demand periods and overall demand. The indexes map to the numbering in demand_charge_schedule, such that the lowest cost period demand charge is in index 0, then the next highest in index 1, etc. The length should be 1 more than the number of different demand_charge_schedule periods. The final entry, index -1, is an overall demand charge applied to the highest consumption regardless of time. Any of these may be 0, but all must be included for the code to work correctly. If not provided, will default to a sample tariff rate. 
    - electric_rate: list or array, 24-hour electricity rates in $/kWh. If not provided, will default to a sample rate schedule. 
    - epw_file: os.path, to the EnergyPlus Weather file (.epw) used to run the simulation. If none, it will default to in.epw (note: current stor4build repo does not create the in.epw, so it will likely crash if not provided)

    Returns
    - os.path to the resulting schedule file (.csv) containing the optimized charging schedule and charging temperature, in the format required for the add_pytank_with_schedule measure
    """

    if debug: print(f"[dynamic_charge_controls] run\ngenerate_schedule({baseline_run_path}, {demand_charge_schedule}, {demand_charge_rate}, {electric_rate}, {epw_file})")

    df, info = preprocess_baseline(baseline_run_path, demand_charge_schedule, demand_charge_rate, electric_rate, epw_file=epw_file)
    demand_charge_rate = info['demand_charge_rate']

    df["Electricity:Facility [kW]"] = df["Electricity:Facility [W]"] / 1000

    total_cost_log = []
    hours_tested=[]
    unavoidable_hours = []

    sch = df.loc[(df['datetime'] >= info["start_date"]) & (df['datetime'] <= info["end_date"])]
    # df comes from preprocess_baseline() with a DatetimeIndex ('datetime' set as the index).
    # The optimization loop below relies on a plain sequential integer index (e.g. cheap_hour.name + 1
    # meaning "the next hour", int(cheap_hour.name) casts, etc.), so reset to a RangeIndex here while
    # keeping 'datetime' available as a regular column for date-based filtering/lookups.
    sch = sch.reset_index(drop=True)

    sch, curr_max_elec = applyDemandCharge(sch, demand_charge_rate, cost='Electricity Rate [$/kWh]', elec = 'Electricity:Facility [kW]', demandWindow='Demand Period', demandCost='Demand Cost', debug=False)

    total_cost_log.append(sch['Cost [kWh]'].sum()+ sum([a/4*b for a,b in zip(curr_max_elec,demand_charge_rate)]))

    i = 0
    n_small = 1
    iter_plot = False
    total_hours = len(sch.index)
    rate = 'Electricity Rate [$/kWh]'

    # -------------------------------------------
    # First loop to generate ideal schedule ignoring modes
    # -------------------------------------------
    # loop while there are still hours left to test
    # note that h contains the remaining hours from the previous run
    # each run, 1 hour is eliminated

    # If the number of hours sharing the current tied inc_cost value exceeds this threshold while
    # searching for a non-unavoidable expensive hour, treat the schedule as fully optimized (no more
    # meaningful improvements are distinguishable) and stop the outer loop, rather than looping
    # through a large tied block that can never advance past an already-unavoidable low-index hour.
    HOURS_WITH_SAME_INCREMENTAL_COST_THRESHOLD = 100
    schedule_fully_optimized = False
    # Otherwise, it will loop thorugh all available hours
    # Note: added a /2 to speed up this loop, acknowledging where there are diminishing returns
    while (total_hours/2 > len(hours_tested)+1+len(unavoidable_hours)) & (i<total_hours/2):
        # 1. find most expensive hour
        expensive_hour = sch.loc[sch['inc_cost'] == sch['inc_cost'].nlargest(1).iloc[-1]]
        
        # print(expensive_hour)
        i_expensive_hour = expensive_hour.index.to_list()[0]
        # hours_tested.append(i_expensive_hour)
        skipped = 1
        while (i_expensive_hour in unavoidable_hours) & (skipped < total_hours):
            # print('Skipped expensive_hour index: ', i_expensive_hour)
            skipped += 1
            nlargest_val = sch['inc_cost'].nlargest(skipped).iloc[-1]
            matching_rows = sch.loc[sch['inc_cost'] == nlargest_val]

            # A large tied block means a huge fraction of remaining hours share the same incremental
            # cost -- there's no meaningful "most expensive hour" left to optimize, and this tie also
            # causes the loop to repeatedly re-select the same lowest-index row within the block
            # (since selection is by value, not position), which can never advance past an
            # already-unavoidable hour. Stop the outer loop in this case.
            if len(matching_rows.index) > HOURS_WITH_SAME_INCREMENTAL_COST_THRESHOLD:
                if debug:
                    print(f"Schedule considered fully optimized: {len(matching_rows.index)} hours tied at inc_cost={nlargest_val!r} (> {HOURS_WITH_SAME_INCREMENTAL_COST_THRESHOLD}); stopping optimization loop.")
                schedule_fully_optimized = True
                break

            expensive_hour = matching_rows
            prev_i_expensive_hour = i_expensive_hour
            i_expensive_hour = expensive_hour.index.to_list()[0]
            # if debug:
            #     print(f"DEBUG_SKIP: skipped={skipped}, nlargest_val={nlargest_val!r}, num_matching_rows={len(matching_rows.index)}, matching_indices={matching_rows.index.to_list()[:10]}, prev_i_expensive_hour={prev_i_expensive_hour}, new_i_expensive_hour={i_expensive_hour}, unchanged={prev_i_expensive_hour == i_expensive_hour}")
        if schedule_fully_optimized:
            break
        if debug and skipped >= total_hours - 1:
            print(f"DEBUG_SKIP: Inner skip loop hit safety bound skipped={skipped} >= total_hours-1={total_hours-1}. Final i_expensive_hour={i_expensive_hour}, still in unavoidable_hours={i_expensive_hour in unavoidable_hours}")

        # 2. calculate incremental cost in prior hours

        # 2.1: look at just the hours up to 24 hours before the most expensive hour

        # Get datetime of most expensive hour
        datetime_value = expensive_hour['datetime'].iloc[0]

        # Convert datetime_value to a pandas Timestamp if it's not already
        if not isinstance(datetime_value, pd.Timestamp):
            datetime_value = pd.to_datetime(datetime_value)

        # Calculate the time range (24 hours before the datetime)
        start_time = datetime_value - pd.Timedelta(hours=24)
        end_time = datetime_value

        if debug:
            print('Expensive hour: ', i_expensive_hour, expensive_hour['datetime'].iloc[0])
            print('Search range: ', start_time, ' - ', end_time)
        
        # Filter the dataframe for rows within this time range
        h = sch[(sch['datetime'] >= start_time) & (sch['datetime'] < end_time)].copy()
        
        # ignore hours we already used
        for hrr in hours_tested:
            if hrr in h.index:
                h.drop(hrr, inplace=True)
        if debug: print('Remaining indices: ', h.index)
        # if there are no hours left, stop this loop
        if len(h.index) <= 1: 
            if debug: print('Warning: no valid hours to shift to, from hour: ', i_expensive_hour, '  ', end_time)
            unavoidable_hours.append(i_expensive_hour)
            if debug: print('unavoidable_hours =', unavoidable_hours, '  num hours_tested = ', len(hours_tested))
            n_small += 1
            continue
        
        # 2.2 COP if the system were in charge mode 
        h['COP_c'] = getCOP((h['Thermal Load [kW]'] + info['charge_rate']) , -3.8, info)

        # 2.3: incremental cost, demand charges
        h['inc_demand'] = 0.0
        for idc in range(len(demand_charge_rate)-1):
            # the minimum amount of charging for that hour won't cause new demand charge
            # min amt charging is 15 min (probably shouldn't be hardcoded)
            h.loc[(h['Demand Period']==idc) & ((h['Electricity Consumption']+ info['charge_rate']/4/h['COP_c']) >= curr_max_elec[idc]), 'inc_demand'] += demand_charge_rate[idc]
        # if the minimum unit of charging would set a new max electric consumption, set a higher cost
        h.loc[(h['Electricity Consumption']+ info['charge_rate']/15/h['COP_c']) >= curr_max_elec[-1], 'inc_demand'] += demand_charge_rate[-1]

        # Incremental cost = (1/COP) * (P_kWh + P_demand + P_standby)
        h['inc_cost'] = 1/h['COP_c'] * ( h[rate] + h['inc_demand'])# + standbyLosses(h, 'compare')) #removed standbyLosses as test 20250930, plots_Bakersfield_Debug_5-nostandby
        # Note: having standby losses makes sense in theory, but it tends to push charging from overnight to during the day (closer to peak hours) which then increases demand charges. 

        # 3. find the cheapest hour in horizon
        # v2 algorithm to splice over multiple hours
        cheap_hours = h.sort_values(by='inc_cost', ascending=True).copy()
        # remaining_load_expensive_hour = expensive_hour['Thermal Load [kW]'].iloc[0]
        remaining_load_expensive_hour = expensive_hour['Cooling'].iloc[0] # suspect it should be Cooling in case load was shifted in or out on a prior iteration
        # IF this hour had previously been set to charge, could set it back to Normal
        was_charging = False
        if expensive_hour['Cooling'].iloc[0] > expensive_hour['Thermal Load [kW]'].iloc[0]+1:
            was_charging = True
            remaining_load_expensive_hour = int(expensive_hour['Cooling'].iloc[0] - expensive_hour['Thermal Load [kW]'].iloc[0])
            if debug: print(f"Expensive hour was charging, so use {expensive_hour['Cooling'].iloc[0]} - {expensive_hour['Thermal Load [kW]'].iloc[0]} = {remaining_load_expensive_hour}")

        # duplicate schedule
        sch2 = sch.copy(deep=True)
        amt_to_shift = [0]*len(h.index)
        c = 0
        while (c < len(cheap_hours.index)) and (cheap_hours['inc_cost'].iloc[c] < expensive_hour['inc_cost'].iloc[0]) and (remaining_load_expensive_hour > 0):
            cheap_hour = cheap_hours.iloc[c]
            remaining_chiller_cap = info['design_capacity_kW']*info['num_chillers'] - cheap_hours['Cooling'].iloc[c]
            remaining_above_hourly_demand_charge = (curr_max_elec[cheap_hours['Demand Period'].iloc[c]] - cheap_hours['Electricity Consumption'].iloc[c]) * cheap_hours['COP_c'].iloc[c]
            remaining_above_overall_demand_charge = (curr_max_elec[-1] - cheap_hours['Electricity Consumption'].iloc[c]) * cheap_hours['COP_c'].iloc[c]
            # Need to check hours between cheap_hour and expensive_hour, because suppose SOC went up and down again
            # between cheap_hours[c] and expensive_hour
            # Done using sch2 (continually updated)
            remaining_TES_cap = info['usable_TES_capacity'] - sch2.loc[(sch2['datetime'] >= cheap_hours['datetime'].iloc[c]) & (sch2['datetime'] < end_time), 'Storage'].max()
            if debug: 
                print('cheap_hour: ', cheap_hour['datetime'])#cheap_hours['datetime'].iloc[c])
                print('max storage in range: ', sch2.loc[(sch2['datetime'] >= cheap_hours['datetime'].iloc[c]) & (sch2['datetime'] < end_time), 'Storage'].max())
            # print('remaining_TES_cap =' , remaining_TES_cap)
            # problem is charge_rate doesn't account for prior charging assigned to hour
            curr_charge_c = cheap_hours['Cooling'].iloc[c] - cheap_hours['Thermal Load [kW]'].iloc[c]
            remaining_charge_c = info['charge_rate'] - curr_charge_c
            if debug: print(f"remaining_charge_c = {remaining_charge_c}, remaining_load_expensive_hour = {remaining_load_expensive_hour}, remaining_chiller_cap = {remaining_chiller_cap}, remaining_TES_cap = {remaining_TES_cap}, remaining_above_hourly_demand_charge = {remaining_above_hourly_demand_charge}, remaining_above_overall_demand_charge = {remaining_above_overall_demand_charge}")

            if demand_charge_rate[cheap_hours['Demand Period'].iloc[c]] > demand_charge_rate[expensive_hour['Demand Period'].iloc[0]]:
                amt_to_shift[c] = max(min(remaining_chiller_cap, remaining_above_hourly_demand_charge, remaining_above_overall_demand_charge, remaining_load_expensive_hour, remaining_charge_c, info['discharge_rate'], remaining_TES_cap),0) # added max condition to ensure this isn't negative
            else:
                amt_to_shift[c] = max(min(remaining_chiller_cap, remaining_load_expensive_hour, remaining_charge_c, info['discharge_rate'], remaining_TES_cap),0)

            # Increase cost for future runs if it would set a new demand charge to run more operation at this hour again
            if amt_to_shift[c] >= remaining_above_hourly_demand_charge:
                cheap_hours.iloc[c, cheap_hours.columns.get_loc('inc_cost')] += demand_charge_rate[cheap_hours['Demand Period'].iloc[c]]
            if amt_to_shift[c] >= remaining_above_overall_demand_charge:
                cheap_hours.iloc[c, cheap_hours.columns.get_loc('inc_cost')] += demand_charge_rate[-1]
            # if cost due to demand charge becomes higher than what was previously next least expensive hour that is available,
            if (c + 1 < len(cheap_hours)) and (cheap_hours['inc_cost'].iat[c + 1] < cheap_hours['inc_cost'].iat[c]):
                # restrict max to demand charge limits
                amt_to_shift[c] = max(min(remaining_above_hourly_demand_charge, remaining_above_overall_demand_charge, remaining_chiller_cap, remaining_load_expensive_hour, remaining_charge_c, info['discharge_rate'], remaining_TES_cap),0)
            
            amt_to_shift[c] = float(amt_to_shift[c])
            # Calculate this at the end, to avoid mistakes
            # Should this be Thermal Load [kW] or Cooling???
            # remaining_load_expensive_hour = expensive_hour['Thermal Load [kW]'].iloc[0] - sum(amt_to_shift)
            # Depends on whether it was charging before or not. 
            remaining_load_expensive_hour = expensive_hour['Cooling'].iloc[0] - sum(amt_to_shift)
            if was_charging:
                remaining_load_expensive_hour = max(expensive_hour['Cooling'].iloc[0] - expensive_hour['Thermal Load [kW]'].iloc[0] - sum(amt_to_shift), 0)
            if remaining_load_expensive_hour < 0:
                print('Warning: remaining_load_expensive_hour =', remaining_load_expensive_hour)
            # remove this cheap_hour from consideration if it is not feasible to shift more load to this hour.
            # without the if condition, if it only increased load to part of the max due to discharge_rate or
            #  remaining_load_expensive_hour, then it would eliminate the hour from future use when it could
            #  still be used
            if amt_to_shift[c] >= min(remaining_chiller_cap, remaining_above_hourly_demand_charge, remaining_above_overall_demand_charge, remaining_charge_c, remaining_TES_cap):
                hours_tested.append(int(cheap_hour.name))
            
            # Edit sch2 now, so we can use it for future stuff
            # check for issues
            if amt_to_shift[c] < 0:
                print('Warning: Negative amt_to_shift[',c,'] =', amt_to_shift[c])
                print('at cheap hour: ', cheap_hour['datetime'])

            # increase storage for all subsequent hours - EDIT: only the ones up to the expensive hour!
            sch2.loc[(sch2.index > cheap_hour.name) & (sch2.index < i_expensive_hour), 'Storage'] += amt_to_shift[c]
            if len(sch2.loc[(sch2.index > cheap_hour.name) & (sch2['Storage']> info['usable_TES_capacity'])].index)>0 : print('Warning: Storage capacity exceeded for:', sch2.loc[(sch2.index > cheap_hour.name) & (sch2['Storage']> info['usable_TES_capacity']), ['datetime', 'Storage']])
            sch2.loc[sch2.index == cheap_hour.name, 'Cooling'] += amt_to_shift[c]
            sch2.loc[sch2.index == cheap_hour.index.to_list()[0], 'Electricity Consumption'] = sch2.loc[sch2.index == cheap_hour.index.to_list()[0], 'Cooling'] / cheap_hour['COP_c']
            sch2.loc[sch2.index == cheap_hour.index.to_list()[0], 'Cost [kWh]'] = sch2.loc[sch2.index == cheap_hour.index.to_list()[0], rate] * sch2.loc[sch2.index == cheap_hour.index.to_list()[0], 'Electricity Consumption'] 
            # update COP
            sch2.loc[sch2.index == cheap_hour.index.to_list()[0], 'COP'] = cheap_hour['COP_c']

            # decrease cost on adjacent hours to current charging
            cheap_hours = cheap_hours.sort_values(by='inc_cost', ascending=True).copy()
            
            c += 1

        # if sum(amt_to_shift) > expensive_hour['Thermal Load [kW]'].iloc[0]:
        if debug: print('amt_to_shift =', amt_to_shift)

        # 4. Execute shifting
        # editing cheap hours was moved to prior loop
        
        # move counter modification here I think
        i += 1
        # Modify expensive hour 
        # decrease storage all subsequent hours - NO! Instead, 
        # sch2.loc[sch2.index > i_expensive_hour, 'Storage'] -= round(sum(amt_to_shift), 2)
        # reduce load
        # if debug:
        #     print(f"DEBUG_SHIFT: expensive_hour Cooling before = {sch2.loc[sch2.index == i_expensive_hour, 'Cooling'].iloc[0]}, sum(amt_to_shift) = {sum(amt_to_shift)}, round(sum(amt_to_shift),1) = {round(sum(amt_to_shift), 1)}")
        rounded_shift = round(sum(amt_to_shift), 1)
        sch2.loc[sch2.index == i_expensive_hour, 'Cooling'] -= rounded_shift # cooling vs thermal load?
        # if debug:
        #     print(f"DEBUG_SHIFT: expensive_hour Cooling after = {sch2.loc[sch2.index == i_expensive_hour, 'Cooling'].iloc[0]}")

        # Detect tiny shifts that may cause errors: if the total shift rounds down to 0, the expensive hour's Cooling was not
        # actually reduced (even though amt_to_shift may have nonzero raw values). Without this,
        # the same expensive/cheap hour pair can be reselected indefinitely (up to total_hours times)
        # since neither hour gets marked as tested/unavoidable in that scenario, causing a
        # semi-infinite loop. Treat this expensive hour as unavoidable and move to the next iteration.
        if rounded_shift == 0:
            print(f"Warning: Shift to expensive hour {i_expensive_hour} ({expensive_hour['datetime'].iloc[0]}) rounded to 0 (raw sum(amt_to_shift)={sum(amt_to_shift)}); marking as unavoidable and skipping to avoid infinite loop.")
            unavoidable_hours.append(i_expensive_hour)
            continue
        # check issues
        if sch2.loc[sch2.index == i_expensive_hour, 'Cooling'].iloc[0] < 0:
            if sch2.loc[sch2.index == i_expensive_hour, 'Cooling'].iloc[0] < -1:
                print('ERROR: sch2.loc[sch2.index == i_expensive_hour, \'Cooling\'] < 0')
                print(sch2.loc[sch2.index == i_expensive_hour])
                print('at iter =', i, ', expensive hour index:', i_expensive_hour, ' expensive_hour =')
                print(expensive_hour)
                print('amt_to_shift =', amt_to_shift)
                print('Cheap hours:')
                print(cheap_hours.iloc[0:c])
                print('remaining_load_expensive_hour =', remaining_load_expensive_hour)
                print('Terminating loop via break')
                break
            if debug: print('WARNING: Negative cooling at expensive hour: ',  sch2.loc[sch2.index == i_expensive_hour, 'Cooling'].iloc[0], ' -> Rounding error, resetting to 0')
            sch2.loc[sch2.index == i_expensive_hour, 'Cooling'] = 0
            
        # recalc COP for expensive hour. T_cw now 10degC for discharging
        sch2.loc[sch2.index == i_expensive_hour, 'COP'] = getCOP(sch2.loc[sch2.index == i_expensive_hour, 'Cooling'], 10, info) 
        sch2.loc[sch2.index == i_expensive_hour, 'Electricity Consumption'] = sch2.loc[sch.index == i_expensive_hour, 'Cooling'] / sch2.loc[sch2.index == i_expensive_hour, 'COP']
        sch2.loc[sch2.index == i_expensive_hour, 'Cost [kWh]'] = sch2.loc[sch.index == i_expensive_hour, rate] * sch2.loc[sch2.index == i_expensive_hour, 'Electricity Consumption']


        # recompute demand charge (inc_cost also recalculated as part of the applyDemandCharge function)
        sch2, curr_max_elec2 = applyDemandCharge(sch2, demand_charge_rate, cost='Electricity Rate [$/kWh]', elec = 'Electricity Consumption', demandWindow='Demand Period', demandCost='Demand Cost', debug=False) # check variable mapping!
        totalcost1 = sch['Cost [kWh]'].sum()+ sum([a/4*b for a,b in zip(curr_max_elec,demand_charge_rate)])
        totalcost2 = sch2['Cost [kWh]'].sum()+ sum([a/4*b for a,b in zip(curr_max_elec2,demand_charge_rate)])
        # if debug:
        #     sch_equal = sch.equals(sch2)
        #     print(f"DEBUG_COST: iter={i}, totalcost1={totalcost1!r}, totalcost2={totalcost2!r}, diff={totalcost1-totalcost2!r}, sch.equals(sch2)={sch_equal}, i_expensive_hour={i_expensive_hour}, i_expensive_hour in hours_tested BEFORE update = {i_expensive_hour in hours_tested}, len(hours_tested)={len(hours_tested)}, len(unavoidable_hours)={len(unavoidable_hours)}")

        # Detect errors
        if sch2.loc[sch2.index == i_expensive_hour, 'Electricity Consumption'].iloc[0] < 0:
            print('ERROR: sch2.loc[sch2.index == i_expensive_hour, \'Electricity Consumption\'] < 0')
            print('Value = ', sch2.loc[sch2.index == i_expensive_hour])
            print('at iter =', i, ', expensive hour index:', i_expensive_hour)
            print(expensive_hour)
            print('Terminating loop via break')
            break
        if sch2['Cooling'].min() < 0:
            print('ERROR: Negative values in sch2')
            print(sch2)
            print('at iter =', i, ', expensive hour index:', i_expensive_hour)
            print('expensive_hour datetime', expensive_hour['datetime'])
            print('Terminating loop via break')
            break

        # if new schedule would save money
        if totalcost1 >= totalcost2:
            sch = sch2
            curr_max_elec = curr_max_elec2
            if iter_plot: df_plot(sch, 'datetime', ['Storage', 'Thermal Load [kW]', 'Cooling', 'Electricity Consumption'], ['inc_cost'], includelast=True, plottype=['smooth', 'step', 'step', 'step', 'step', 'step', 'step'], xlabel='Date', saveas='plots/loadshiftdemo_'+str(i), ylabel='Thermal or Electrical Energy [kW]', y2label='Incremental Cost of Each Hour [$]')
            total_cost_log.append(totalcost2)
            # remove duplicates from hours_tested
            hours_tested = list(set(hours_tested))
            unavoidable_hours = list(set(unavoidable_hours))
            for iex in [1,2,3,4]:
                if i_expensive_hour + iex in unavoidable_hours: unavoidable_hours.remove(i_expensive_hour + iex)
        else: #new schedule is more expensive
            unavoidable_hours.append(i_expensive_hour)
            print('Warning: Changing operation from ', i_expensive_hour, ' to ',cheap_hours.iloc[0].index[0],  ' would increase cost')
            total_cost_log.append(totalcost1)
            n_small += 1

    if debug: 
        sch['mode_temp'] = np.sign(sch['Cooling'] - sch['Thermal Load [kW]'])
        print('BEFORE consolidate_charging_hours()')
        print(sch['mode_temp'].value_counts())

    # Consolidate charging hours
    sch = consolidate_charging_hours(sch, demand_charge_rate)

    if debug: 
        sch['mode_temp'] = np.sign(sch['Cooling'] - sch['Thermal Load [kW]'])
        print('AFTER consolidate_charging_hours()')
        print(sch['mode_temp'].value_counts())

    # ------------------------------------------
    # Second loop to generate schedule for charging and discharging periods and set charging temperatures
    # -------------------------------------------

    dms = sch[['datetime', 'Thermal Load [kW]', rate, 'Dry Bulb Temperature','Demand Period', 'COP', 'Cooling','Cost [kWh]', 'Electricity Consumption', 'Storage']].copy()

    previous_state = 10 # starting at 6.7 can cause spike in first timestep
    timesteps_per_hour = int(3600/info["original_timestep_s"]) # 30 = 2 minutes # MUST BE DIVISIBLE BY 4
    info['timesteps_per_hour'] = timesteps_per_hour
    last_charge_time = datetime.datetime(1987,1,1,0,0) # arbitrary initial value for tracking cooling, must be before start of simulation

    min_operation_increment = float(info['min_plr']) * info['design_capacity_kW'] / timesteps_per_hour
    # print('min_operation_increment =', min_operation_increment)

    chiller_mode_schedule = [0] * (len(sch.index) * timesteps_per_hour)

    charge_temperature_schedule = [6] * (len(sch.index) * timesteps_per_hour)  # Added. Default needs to be the starting interpolation temperature. 

    # assume charge rate gets decreased linearly
    # Note that < -3.8 seems to get overwritten by some other constraint
    min_charge_temp = -3.8 # degC

    # These are tuned for 15-min timesteps. Other timesteps would need to rework
    # tuning was mostly trial and error 
    charge_start_sequence = [4.4,2,0,-1.5, -2, -2.5, -3, -3.5, -3.8] + [min_charge_temp] *timesteps_per_hour #degC. after -1.5, decreases by 0.5 per timestep
    charge_start_sequence_normal = [3.6,0.7,-0.8,-2, -3, -3.8] + [min_charge_temp] *timesteps_per_hour #degC.
    charge_start_sequence_discharge = [6.7,5.9,3,0.2,-1.5, -2.5, -3.3, -3.7] + [min_charge_temp] *timesteps_per_hour #degC.
    charge_start_sequence_high_base_load = [6.6, 5.8,3,1,-0.5,-1.3,-2,-2.5,-2.75,-3,-3.2,-3.4,-3.6,-3.8] + [min_charge_temp] *timesteps_per_hour
    charge_deramp_rate = 0.10 # degC

    load30 = dms['Thermal Load [kW]'].quantile(0.80)
    dms.loc[:, 'Load Rank'] = dms['Thermal Load [kW]'].rank(pct=True)
    max_load = dms['Thermal Load [kW]'].max()

    i = 2 # if starting at 0, causes mystery consumption spike at timestep 0. This also makes it easier to do a look backward algorithm
    i_prev = 0
    repeat_count = 0
    while (i < len(sch.index)): # and (repeat_count < 2*len(sch.index)):
        cooling = dms['Cooling'].iloc[i]
        # if no cooling in that hour, keep system at idle and move on
        load = dms['Thermal Load [kW]'].iloc[i]
        # if load <= 0.001: # this might be a bug
        #     i += 1
        #     continue
        demand_period = dms['Demand Period'].iloc[i]
        wsch = []

        # figure out infinite loop issue with the fudge factor
        if i == i_prev:
            repeat_count += 1
            if repeat_count > 3:
                print("Hit repeat_count limit, stopping to avoid infinite loop")
                break
        else:
            repeat_count = 0
        i_prev = i

        if (cooling < load+2.22) & (load > 2.22): # + min_operation_increment:
            
            # Fudge factor: start charge 1 hour early
            # if next hour exists
            if i < (len(sch.index) - 1):
                # if current hour is not a peak load or peak price
                if (load < dms['Thermal Load [kW]'].max()) and (demand_period <= 1):
                    # if next hour will charge
                    if i < (len(sch.index) - 1):
                        # if (dms['Cooling'].iloc[i+1] - dms['Thermal Load [kW]'].iloc[i+1] > 0) and (dms['Cooling'].iloc[i+1] + min_operation_increment > dms['Thermal Load [kW]'].iloc[i+1]) and (dms['Demand Period'].iloc[i+1] < len(demand_charge_rate)-2):
                        if (dms['Cooling'].iloc[i+1] > dms['Thermal Load [kW]'].iloc[i+1] + 0.1) and (dms['Cooling'].iloc[i+1] > min_operation_increment) and (dms['Demand Period'].iloc[i] < len(demand_charge_rate)-2) and (load + dms['Cooling'].iloc[i+1] - dms['Thermal Load [kW]'].iloc[i+1] > min_operation_increment):
                            if debug: print(f"begin charge early instead of Discharge: {i}, original cooling {dms['Cooling'].iloc[i]} kWh")
                            # make this hour charge
                            next_hr_diff = dms['Cooling'].iloc[i+1] - dms['Thermal Load [kW]'].iloc[i+1]
                            actual_index = dms.index[i]
                            dms.loc[actual_index, 'Cooling'] = load + next_hr_diff #+ min_operation_increment
                            if debug: print(f"Next hour will charge {next_hr_diff} kWh. Set cooling to {dms['Cooling'].iloc[i]} = {load + next_hr_diff} kWh")
                            continue # redo this hour
            # else:# discharge # don't need else because of continue statement
            chiller_mode_schedule[i*timesteps_per_hour:(i+1)*timesteps_per_hour] = [-1] * timesteps_per_hour
            previous_state = 10
            
        # elif (cooling > load + min_operation_increment)& (demand_period < len(demand_charge_rate)-2):
        elif (cooling > load) & (cooling>min_operation_increment) & (demand_period < len(demand_charge_rate)-2):
            # ^^^ added condition to not charge in highest demand cost periods
            # charge
            remaining_chiller_cap = info['design_capacity_kW']*info['num_chillers'] - load
            full_charge_effect = min(remaining_chiller_cap , info['charge_rate'])
            # print('full_charge_effect =', full_charge_effect)
            charge_amt = cooling - load
            # print('target charge_amt =', charge_amt)
            ratio = charge_amt/full_charge_effect  #(cooling-load) / design_capacity_kW
            ratio = min(ratio, 1) # cap ratio at 1
            # assume linear between (ratio, T) of (0, -1) and (1, -3.8) (probably not a perfect assumption, may need to revisit)
            # rounding to 4 decimal places is mostly for readability
            target_T = round(float(ratio * (min_charge_temp + 1) - 1), 4)
            # print(f"target_T = {target_T}")
            # mod target_T --> not really needed
            # if dms['Load Rank'].iloc[i] > 

            # Look back and ahead to avoid short-term changes in charging temperature
            if (target_T > previous_state) and (i < (len(sch.index) - 1)): # temps are negative, so greater Target T means less cooling req
                # if next hour would also charge
                if (dms['Cooling'].iloc[i+1] > dms['Thermal Load [kW]'].iloc[i+1] + 0.1) and (dms['Cooling'].iloc[i+1] > min_operation_increment) and (dms['Demand Period'].iloc[i] == 0) and (load + dms['Cooling'].iloc[i+1] - dms['Thermal Load [kW]'].iloc[i+1] > min_operation_increment):
                    # if that next hour cooling is greater than this hour's
                    if cooling < dms['Cooling'].iloc[i+1]:
                        # don't decrease target_T vs previous_state
                        if debug: print(f"avoid chiller dips override: target_T was = {target_T} °C, previous_state = {previous_state} °C. cooling: [{dms['Cooling'].iloc[i-1]}, {cooling}, {dms['Cooling'].iloc[i+1]}]")
                        target_T = min(target_T, previous_state)
            if load > 0.75 * max_load:
                pct_of_max_load =  load / max_load
                # assuming charge rate is proportional 
                # eg 100% of max load --> reduce to whatever we set as the "min" value 
                # 0.4 * -2.8 - 1
                target_T_limit = round(float((pct_of_max_load - 0.60) * (min_charge_temp + 1) - 1), 4) 
                if debug: print(f"limit target_T to smaller of {target_T_limit} or {target_T} °C due to high base load {round(load,2)} kW, {round(pct_of_max_load,3)} %")


            # This was an experiment to change charge start sequence based on base load. Didn't help in v15. Trying again with less extreme temp diffs in v16
            if load > load30:
                if debug: print(f"activating high_base_load mode. base_load = {load} kW")
                charge_start_sequence = charge_start_sequence_high_base_load
                if previous_state > 6:
                    chiller_mode_schedule[i*timesteps_per_hour:(i+1)*timesteps_per_hour] = [0] + [1] * (timesteps_per_hour-1)
                else:
                    chiller_mode_schedule[i*timesteps_per_hour:(i+1)*timesteps_per_hour] = [1] * timesteps_per_hour
            elif previous_state > 8: # was discharge
                charge_start_sequence = charge_start_sequence_discharge
                chiller_mode_schedule[i*timesteps_per_hour:(i+1)*timesteps_per_hour] = [0] + [1] * (timesteps_per_hour - 1)
            else: # was normal
                charge_start_sequence = charge_start_sequence_normal
                chiller_mode_schedule[i*timesteps_per_hour:(i+1)*timesteps_per_hour] = [1] * timesteps_per_hour

            if previous_state > target_T:
                c = 0
                while charge_start_sequence[c] > previous_state:
                    c += 1
                charge_temp = charge_start_sequence[c:c+timesteps_per_hour]
                for d in range(len(charge_temp)):
                    if charge_temp[d] < target_T:
                        # print(f"T = {charge_temp[d]} exceeds target {target_T}, set back to target") 
                        charge_temp[d] = target_T
            elif previous_state < target_T: # ramp down gradually, not abruptly
                charge_temp = [target_T] * timesteps_per_hour
                for d in range(timesteps_per_hour):
                    previous_state = round(previous_state + charge_deramp_rate, 4 )
                    charge_temp[d] = min(previous_state, target_T) #the smaller of either the prior state or target T, to avoid sudden temperature increase (load decrease)
            else:
                charge_temp = [target_T] * timesteps_per_hour

            charge_temperature_schedule[i*timesteps_per_hour:(i+1)*timesteps_per_hour] = charge_temp

            # chiller_mode_schedule[i*timesteps_per_hour:(i+1)*timesteps_per_hour] = [1] * timesteps_per_hour

            # previous_state = max(target_T, charge_temp[-1]) # the larger of target temperature or the final charge temperature setting in the sequence
            # no, because that would break the ramp gradually
            # might just need to be the most recent temperature
            previous_state = charge_temp[-1]

            if debug: print(f"{dms['datetime'].loc[dms.index[0] + i]}\t target charge = {charge_amt} kWh\t target_T = {target_T}\t charge_temp = {charge_temp}")

        else: #Normal mode. the charge_temperature_schedule is already 0 by default, so just need to reset previous_state
            
            # Fudge factor: start charge 1 hour early
            # if next hour exists
            if i < (len(sch.index) - 1):
                # if next hour will charge
                # if (dms['Cooling'].iloc[i+1] - dms['Thermal Load [kW]'].iloc[i+1] > 0) and (dms['Cooling'].iloc[i+1] + min_operation_increment > dms['Thermal Load [kW]'].iloc[i+1]) and (dms['Demand Period'].iloc[i+1] < len(demand_charge_rate)-2):
                if (dms['Cooling'].iloc[i+1] > dms['Thermal Load [kW]'].iloc[i+1]) and (dms['Cooling'].iloc[i+1] > min_operation_increment) and (dms['Demand Period'].iloc[i] ==0) and (load + dms['Cooling'].iloc[i+1] - dms['Thermal Load [kW]'].iloc[i+1] > min_operation_increment):
                    # print(f"fudge factor b active: {i}, original cooling {dms['Cooling'].iloc[i]} kWh")
                    # make this hour charge
                    next_hr_diff = dms['Cooling'].iloc[i+1] - dms['Thermal Load [kW]'].iloc[i+1]
                    if debug: print(f"begin charge early instead of Normal mode: {i}, original cooling {dms['Cooling'].iloc[i]} kWh, next_hr_diff = {next_hr_diff}")
                    # dms['Cooling'].iloc[i] = dms['Thermal Load [kW]'].iloc[i] + next_hr_diff
                    # dms.at[i, 'Cooling'] = load + next_hr_diff
                    # FIX: Assign using .loc with the actual index label of the i-th row
                    actual_index = dms.index[i]
                    dms.loc[actual_index, 'Cooling'] = load + next_hr_diff # + min_operation_increment
                    # cooling = dms.at[i, 'Cooling']
                    if debug: print(f"Next hour will charge {next_hr_diff} kWh. Set cooling to {dms['Cooling'].iloc[i]} = {load + next_hr_diff} kWh")
                    # continue # redo this hour
                    i -= 1 # sloppier way to redo this hour to try to fix infinite loop issues
                
                # If hours before and after are discharge, keep this one at discharge
                elif (previous_state == 10) and (dms['Cooling'].iloc[i+1] < dms['Thermal Load [kW]'].iloc[i+1] + 2.22) and (dms['Thermal Load [kW]'].iloc[i+1] > 2.22):
                    # discharge
                    chiller_mode_schedule[i*timesteps_per_hour:(i+1)*timesteps_per_hour] = [-1] * timesteps_per_hour
                    previous_state = 10

            # If none of the above overrides apply, then it's actually in Normal mode.
            previous_state = 6.7
            
            # previous_state = 6.7
        # check
        # if len(wsch) != timesteps_per_hour: 
        #     print('WARNING: len(wsch) != timesteps_per_hour ')
        #     print('cooling =', cooling)
        #     print('load = ', load)
        #     print('wsch =', wsch)
        i += 1
        # repeat_count += 1

    # Variables that should be interpolated
    dms1 = (dms.assign(datetime=pd.to_datetime(dms['datetime']))
            .set_index('datetime')
            .reindex(pd.date_range(dms['datetime'].min(),
                                    dms['datetime'].max() +
                                    pd.Timedelta(minutes=60-(60/timesteps_per_hour)),
                                    freq=f"{int(60/timesteps_per_hour)}min"))
            .interpolate('linear')
            .reset_index()
            .rename(columns={'index': 'datetime'}))
    dms1['mode'] = chiller_mode_schedule
    dms1['charge_temperature'] = charge_temperature_schedule

    # Forward fill for variables that should not be interpolated
    dms2 = (dms.assign(datetime=pd.to_datetime(dms['datetime']))
            .set_index('datetime')
            .reindex(pd.date_range(dms['datetime'].min(),
                                    dms['datetime'].max() +
                                    pd.Timedelta(minutes=60-(60/timesteps_per_hour)),
                                    freq=f"{int(60/timesteps_per_hour)}min"))
            .ffill()
            .reset_index()
            .rename(columns={'index': 'datetime'}))

    dms1[rate] = dms2[rate]
    dms1['Demand Period'] = dms2['Demand Period']

    if debug: 
        print(dms.shape)
        print(dms1['mode'].value_counts())

    output_path = os.path.join(baseline_run_path, "..", "..", "dynamic_charge_schedule.csv")

    generate_schedule_file(dms1,info,output_path)
    print(f"[dynamic_charge_controls] Dynamic charge schedule saved to: {output_path}")

    return output_path
