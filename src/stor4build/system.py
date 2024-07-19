# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import os

class System:
    def name(self):
    	raise NotImplementedError('System object must implement the "name" method')
    def osw(self, osw, **kwargs):
    	# Implement this one if the system is a one-shot through deal
        return None
    def run(self, runner, osm, epw, run_dir, output_dir, measures_dir, measures_only=False, run_baseline=False, **kwargs):
        return None
        
class Baseline(System):
    def name(self):
    	return 'baseline'
    def osw(self, osw_src, **kwargs):
        osw = osw_src()
        #osw['run_directory'] = os.path.join(osw['run_directory'], 'baseline')
        return osw
