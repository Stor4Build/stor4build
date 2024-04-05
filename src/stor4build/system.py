# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause

class System:
    def run(self, osm, epw, run_dir, output_dir, measures_dir, measures_only=False, run_baseline=False, **kwargs):
        raise NotImplementedError('System object must implement the "run" method')
