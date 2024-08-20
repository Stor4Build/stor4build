# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os

def seed_model(openstudio_exe, path, filename):
    cur_dir = os.getcwd()
    os.chdir(path)
    filepath = os.path.join(path, filename)
    os.system('%s -e "require \'openstudio\'; model = OpenStudio::Model::Model.new; out = OpenStudio::Path.new(\'%s\'); model.save(out,true)"' % (openstudio_exe, filepath))
    os.chdir(cur_dir)

def weather_lookup(climate_zone):
    # Cheat for now, all the world is 4A
    return 'USA_TN_Knoxville-McGhee.Tyson.AP.723260_TMY3.epw'

def prototype_lookup(type, climate_zone, vintage):
    # Cheat for now, all buildings are this one large office
    return 'LargeOffice.osm'
    
def process_energy_schedule(sch, peak=3):
    # Process the energy schedule and produce charge/discharge windows
    reverse_sch = list(reversed(sch)) # This is probably bad, just do it for now
    discharge_start_hour = sch.index(peak) + 1
    discharge_end_hour = len(sch) - reverse_sch.index(peak)
    charge_start_hour = discharge_end_hour + 1
    charge_end_hour = discharge_start_hour - 1
    if discharge_start_hour == 1:
        charge_end_hour = 24
    if discharge_end_hour == 24:
        charge_start_hour = 1
    return ('%02d:00' % charge_start_hour,
            '%02d:00' % charge_end_hour,
            '%02d:00' % discharge_start_hour,
            '%02d:00' % discharge_end_hour)
    

