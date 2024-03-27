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

