# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import subprocess
import json

def run_workflow(openstudio_exe, full_run_path, osw_json, measures_only=False):
    if not os.path.exists(full_run_path):
        os.makedirs(full_run_path, exist_ok=True)
    args = [openstudio_exe,
            'run',
            '--show-stdout']
    if measures_only:
        args.append('--measures_only')
    args.extend(['-w',
                 's4b.osw'])
    with open(os.path.join(full_run_path, 's4b.osw'), 'w') as fp:
        json.dump(osw_json, fp, indent=4)
    subprocess.run(args, cwd=full_run_path)

