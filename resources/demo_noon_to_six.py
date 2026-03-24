# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause

from pyenergyplus.plugin import EnergyPlusPlugin
from case_details import MODE_SCHEDULE_TYPE, MODE_SCHEDULE_NAME, Mode

class NoonToSix(EnergyPlusPlugin):

    def actuate(self, state, x):
        self.api.exchange.set_actuator_value(state, self.data['mode_schedule'], x)

    def on_begin_timestep_before_predictor(self, state) -> int:
        if 'mode_schedule' not in self.data:
            self.data['mode_schedule'] = self.api.exchange.get_actuator_handle(
                state, MODE_SCHEDULE_TYPE, "Schedule Value", MODE_SCHEDULE_NAME
            )
            if self.data['mode_schedule'] == -1:
                self.api.runtime.issue_severe(state, "Could not get handle to TES mode schedule")
                return 1

        hour = self.api.exchange.hour(state)
        if hour < 12:
            self.actuate(state, Mode.CHARGE.value)
        elif 12 <= hour < 18:
            self.actuate(state, Mode.DISCHARGE.value)
        else:
            self.actuate(state, Mode.CHARGE.value)
        return 0
