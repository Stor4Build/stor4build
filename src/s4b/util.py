# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import json

def seed_model(openstudio_exe, path, filename):
    cur_dir = os.getcwd()
    os.chdir(path)
    filepath = os.path.join(path, filename)
    os.system('%s -e "require \'openstudio\'; model = OpenStudio::Model::Model.new; out = OpenStudio::Path.new(\'%s\'); model.save(out,true)"' % (openstudio_exe, filepath))
    os.chdir(cur_dir)