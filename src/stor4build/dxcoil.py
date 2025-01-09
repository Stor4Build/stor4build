# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
from .system import Simulation
from .osmeasures import Step

class DxCoil(Simulation):
    def __init__(self, name, pre_steps=None, post_steps=None, sizing=None):
        super().__init__(name, pre_steps=pre_steps, post_steps=post_steps)
        self.sizing = sizing
    def assemble_steps(self, pre_steps, post_steps):
        steps = pre_steps[:]
        steps.append(Step("Add Packaged Ice Storage",
                          "add_packaged_ice_storage"))
        steps.extend(post_steps)
        return steps
    @classmethod
    def size(cls, name, baseline_results, **kwargs):
        # Nothing much to do here right now, just autosize for now
        # Package up the sizing info, add more later
        sizing = {'algorithm': 'autosize'}
        # Remove any arguments that might intefere
        return cls(name, sizing=sizing, **kwargs)
