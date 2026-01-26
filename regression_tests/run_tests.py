# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import httpx
import time
import sys
import os
import json
from click.testing import CliRunner
from stor4build.cli import s4b

# Make some assumptions
this_dir = os.path.abspath(os.path.dirname(__file__))
cases_file = os.path.join(this_dir, 'tests.json')


output_path = '.'
if len(sys.argv) > 1:
    if os.path.exists(sys.argv[1]) and os.path.isdir(sys.argv[1]):
        output_path = sys.argv[1]

with open(cases_file, 'r') as fp:
    inputs =json.load(fp)

for name,case in inputs.items():
    print(name)
    if 'MediumOffice' not in name:
        continue
    for type, info in case.items():
        if type == 'api':
            #print('   ', type)
            start = time.time()
            r = httpx.post('http://127.0.0.1:5000/simulate', json=info, timeout=None)
            delta = time.time() - start
            print(f'    Done with "{name}"! ({delta} seconds)')
            output_csv = os.path.join(output_path, name + '_api.csv')
            with open(output_csv, 'w') as fp:
                fp.write(r.text)
        elif type == 'cli':
            runner = CliRunner()
            argstring = ' '.join(info['arguments'])
            print(argstring)
            result = runner.invoke(s4b, argstring)
            print(result.output)
