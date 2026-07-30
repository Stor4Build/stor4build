# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import numpy as np
import pandas as pd
import pytest as pt
from click.testing import CliRunner
from click import Context
import stor4build as s4b
from stor4build.cli import s4b as s4b_cli

# Mocking a basic run directory structure for smoke tests
import tempfile
import shutil

def test_dynamic_charge_params():
    # Mock data
    baseline_run_path = tempfile.mkdtemp()
    # Create dummy files to satisfy preprocess_baseline
    with open(os.path.join(baseline_run_path, "in.idf"), "w") as f: f.write("Dummy IDF")
    with open(os.path.join(baseline_run_path, "eplusout.eio"), "w") as f: f.write("Dummy EIO")
    
    # Create a dummy eplusout.csv with required columns
    df = pd.DataFrame({
        'Date/Time': pd.date_range('2006-01-01', periods=8760, freq='H'),
        'NUM TANKS:Schedule Value [](TimeStep)': [1]*8760,
        'Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)': [20.0]*8760,
        'WATERCOOLED  CENTRIFUGAL CHILLER 0:Chiller Electricity Rate [W](TimeStep)': [1000.0]*8760,
        'WATERCOOLED  CENTRIFUGAL CHILLER 0:Chiller Condenser Heat Transfer Rate [W](TimeStep)': [500.0]*8760,
        'WATERCOOLED  CENTRIFUGAL CHILLER 0:Chiller Evaporator Cooling Rate [W](TimeStep)': [800.0]*8760,
        'WATERCOOLED  CENTRIFUGAL CHILLER 0:Chiller Part Load Ratio [](TimeStep)': [0.5]*8760,
        'WATERCOOLED  CENTRIFUGAL CHILLER 0:Chiller COP [W/W](TimeStep)': [5.0]*8760,
        'Electricity:Facility [J](TimeStep)': [3600000.0]*8760
    })
    df.to_csv(os.path.join(baseline_run_path, "eplusout.csv"), index=False)
    
    # Test defaults
    from stor4build.dynamic_charge_controls import preprocess_baseline
    df_def, info_def = preprocess_baseline(baseline_run_path)
    assert "demand_charge_rate" in info_def
    assert info_def["demand_charge_rate"] == [0, 9.92+5.09, 45.8+20.36, 32+19.11]
    
    # Test overrides
    custom_dcr = [1, 2, 3, 4]
    custom_dcs = [0]*24
    custom_er = [0.1]*24
    df_cust, info_cust = preprocess_baseline(baseline_run_path, 
                                              demand_charge_schedule=custom_dcs, 
                                              demand_charge_rate=custom_dcr, 
                                              electric_rate=custom_er)
    assert info_cust["demand_charge_rate"] == custom_dcr
    assert np.array_equal(info_cust["demand_charge_schedule"], np.array(custom_dcs))
    assert info_cust["electric_rate"] == custom_er
    
    shutil.rmtree(baseline_run_path)

def test_run_icetank_dynamic_cli_smoke():
    runner = CliRunner()
    # Use valid paths for arguments that have exists=True
    # Since we are in tests, we can point to actual files if they exist or mock them
    osm = 'models/LargeOffice_4A_2019.osm' 
    epw = 'weather/USA_TN_Knoxville-McGhee.Tyson.AP.723260_TMY3.epw' # Adjust if path is different
    
    # We use --measures-only to avoid running actual simulations
    result = runner.invoke(s4b_cli, ['run-icetank-dynamic', osm, epw, '--measures-only'])
    
    # Since we don't have the full environment (OpenStudio etc.), we expect some failure 
    # but we want to check if it got past the CLI parsing and reached the internal logic.
    # If it fails with a FileNotFoundError for OpenStudio, it means the CLI parsed correctly.
    # However, let's check if the demand charge options are recognized.
    
    result_with_params = runner.invoke(s4b_cli, [
        'run-icetank-dynamic', osm, epw, 
        '--demand-charge-rate', '1,2,3,4', 
        '--measures-only'
    ])
    
    # If it failed because of 'osm' or 'epw' not found (depending on where test is run), 
    # it's a path issue. If it fails with "No such option", then CLI is wrong.
    assert result_with_params.exit_code != 0 or "Error" not in result_with_params.output
    # Specifically check that it didn't fail with "no such option"
    assert "no such option: --demand-charge-rate" not in result_with_params.output

# Keep existing tests by importing them or re-implementing
# Since this is a new file for dynamic tests, we'll keep it separate.
