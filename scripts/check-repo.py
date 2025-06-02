# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import glob
import os

# Make some assumptions
this_dir = os.path.abspath(os.path.dirname(__file__))
repo_dir = os.path.join(this_dir, '..')
measures_dir = os.path.join(repo_dir, 'measures')

python_files = glob.glob(os.path.join(repo_dir, '**', '*.py'), recursive=True)
ruby_files = glob.glob(os.path.join(repo_dir, '**', '*.rb'), recursive=True)

# The SPDX headers we know about
spdx_starters = [
    '# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory',
    '# SPDX-FileCopyrightText: 2023-present Alliance for Sustainable Energy'
]

# Alt headers we know about
alt_starters = ['''# *******************************************************************************
# OpenStudio(R), Copyright (c)'''
]

# Check for a license header
for file in python_files + ruby_files:
    with open(file, 'r') as fp:
        txt = fp.read()
    if txt.startswith('# SPDX-FileCopyrightText:'):
        for start in spdx_starters:
            if txt.startswith(start):
                break
        else:
            print(f'Unrecognized license header in "{file}"')
                
    else:
        for start in  alt_starters:
            if txt.startswith(start):
                break
        else:
            print(f'Missing license header in "{file}"')

# Check top level dirs for README.md
dirs = next(os.walk(repo_dir))[1]
for dir in dirs:
    if dir.startswith('.'):
        continue
    if dir in ['src', 'tests']:
        continue
    if not os.path.exists(os.path.join(repo_dir, dir, 'README.md')):
        print(f'Missing README.md in "{dir}"')

# Check the measures for a README.md and meaningful LICENSE.md
dirs = next(os.walk(measures_dir))[1]
for dir in dirs:
    if not os.path.exists(os.path.join(measures_dir, dir, 'README.md')):
        print(f'Missing README.md in measure "{dir}"')
    if not os.path.exists(os.path.join(measures_dir, dir, 'LICENSE.md')):
        print(f'Missing LICENSE.md in measure "{dir}"')
    else:
        size = os.path.getsize(os.path.join(measures_dir, dir, 'LICENSE.md'))
        if size < 50:
            print(f'LICENSE.md in measure "{dir}" is less than 50 bytes in size')
        #print(dir, size)
        #fp = open(os.path.join(measures_dir, dir, 'LICENSE.md'))
        #for i,line in enumerate(fp):
        #    if i > 3:
        #        break
        #else:
        #    print(f'LICENSE.md in measure "{dir}" is less than 3 lines long')
    