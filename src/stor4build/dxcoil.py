# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
from .system import Simulation
from .osmeasures import Step
from dataclasses import dataclass, field
from typing import List

@dataclass
class DxCoil(Simulation):
    name: str
    pre_steps: List[Step] = field(default_factory=list)
    post_steps: List[Step] = field(default_factory=list)
    sizing: dict = None
    hourly: bool = False
    charge_start: str = None
    charge_end: str = None
    discharge_start: str = None
    discharge_end: str = None

    def required_steps(self):
        args = {'hourly': self.hourly,
                'ice_cap': 'AutoSize',
                'size_mult': '1',
                'ctl': 'ScheduledModes',
                'sched': 'Simple User Sched',
                'wknd': false,
                'season': '06/01-09/30'}
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
