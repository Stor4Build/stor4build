# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
from .system import Simulation
from .osmeasures import Step

class DxCoil(Simulation):
    def __init__(self, name, **kwargs):
        super().__init__(name)
        self.pre_steps = kwargs.get('pre_steps', [])
        self.post_steps = kwargs.get('post_steps', [])
        self.sizing = kwargs.get('sizing', {})
    @classmethod
    def size(cls, name, baseline_results, **kwargs):
        # Nothing much to do here right now
        pre_steps = kwargs.get('pre_steps', [])
        post_steps = kwargs.get('post_steps', [])
        # Package up the sizing info
        # sizing = {}
        # Remove any arguments that might intefere
        return cls(name, pre_steps=pre_steps, post_steps=post_steps, **kwargs)
    def osw(self, seed_file, measures_directory, epw_file, **kwargs):
        steps = self.pre_steps
        steps.append(Step("Add Packaged Ice Storage",
                          "add_packaged_ice_storage"))
        steps.extend(self.post_steps)
        osw = {
            'measure_paths': [ measures_directory ],
            'seed_file': seed_file,
            'steps': [ el.to_dict() for el in steps ],
            'weather_file': epw_file
        }
        return osw

