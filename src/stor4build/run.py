# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import subprocess
import json
import shutil

def run_workflow(openstudio_exe, full_run_path, osw_json, measures_only=False):
    resolved_exe = shutil.which(openstudio_exe)
    if resolved_exe is None and os.path.isfile(openstudio_exe):
        resolved_exe = os.path.abspath(openstudio_exe)
    if resolved_exe is None:
        raise FileNotFoundError(f'Cannot find OpenStudio executable "{openstudio_exe}"')
    if not os.path.exists(full_run_path):
        os.makedirs(full_run_path, exist_ok=True)
    args = [resolved_exe,
            'run',
            '--show-stdout']
    if measures_only:
        args.append('--measures_only')
    args.extend(['-w',
                 's4b.osw'])
    with open(os.path.join(full_run_path, 's4b.osw'), 'w') as fp:
        json.dump(osw_json, fp, indent=4)
    return subprocess.run(args, cwd=full_run_path, check=True)

