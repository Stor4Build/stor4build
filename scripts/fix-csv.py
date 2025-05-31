# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import stor4build
import time
import sys
import os
import json

if len(sys.argv) != 2:
    print('usage: fix-cvs EPLUSOUT.CSV')

stor4build.fix_csv(sys.argv[1], verbose=True)

