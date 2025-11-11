# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from .system import Simulation
from .osmeasures import Step
from dataclasses import dataclass, field
from typing import List


class DxCoil(Simulation):
    def __init__(self, name, pre_steps=None, post_steps=None, hourly=False, **kwargs):
        # Get all the data first
        self.charge_start = kwargs.get('charge_start', None)
        self.charge_end = kwargs.get('charge_end', None)
        self.discharge_start = kwargs.get('discharge_start', None)
        self.discharge_end = kwargs.get('discharge_end', None)
        self.sizing = kwargs.get('sizing', {})
        self.hourly = hourly
        super().__init__(name, pre_steps=pre_steps, post_steps=post_steps)

    def required_steps(self):
        args = {'hourly': self.hourly,
                'ice_cap': 'AutoSize',
                'size_mult': '1',
                'ctl': 'ScheduledModes',
                'sched': 'Simple User Sched',
                'wknd': False}
        if self.charge_start is not None:
            args['charge_start'] = self.charge_start
        if self.charge_end is not None:
            args['charge_end'] = self.charge_end
        if self.discharge_start is not None:
            args['discharge_start'] = self.discharge_start
        if self.discharge_end is not None:
            args['discharge_end'] = self.discharge_end
        return [Step("Add Packaged Ice Storage", "add_packaged_ice_storage", arguments=args)]
    
    @classmethod
    def size(cls, name, baseline_results, **kwargs):
        # Nothing much to do here right now, just autosize for now
        # Package up the sizing info, add more later
        sizing = {'algorithm': 'autosize'}
        # Remove any arguments that might intefere (maybe later?)
        return cls(name, sizing=sizing, **kwargs)
