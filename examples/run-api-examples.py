# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import httpx
import time
import sys
import os
import json

# Make some assumptions
examples_dir = os.path.abspath(os.path.dirname(__file__))
examples_file = os.path.join(examples_dir, 'examples.json')


output_path = '.'
if len(sys.argv) > 1:
    if os.path.exists(sys.argv[1]) and os.path.isdir(sys.argv[1]):
        output_path = sys.argv[1]

with open(examples_file, 'r') as fp:
    inputs =json.load(fp)

for name,input in inputs.items():
    start = time.time()
    r = httpx.post('http://127.0.0.1:5000/simulate', json=input, timeout=None)
    delta = time.time() - start
    print(f'Done with "{name}"! ({delta} seconds)')
    output_csv = os.path.join(output_path, name + '.csv')
    with open(output_csv, 'w') as fp:
        fp.write(r.text)

