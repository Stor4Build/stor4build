# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import json

def run(openstudio_exe, run_dir, osw_json):
    cur_dir = os.getcwd()
    os.chdir(run_dir)
    with open('s4b.osw', 'w') as fp:
        json.dump(osw_json, fp, indent=4)
    os.system('%s run -w s4b.osw' % (openstudio_exe, ))
    os.chdir(cur_dir)