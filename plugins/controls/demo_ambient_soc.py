# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause

from pyenergyplus.plugin import EnergyPlusPlugin
from case_details import MODE_SCHEDULE_TYPE, MODE_SCHEDULE_NAME, Mode

class AmbientSoc(EnergyPlusPlugin):

    def actuate(self, state, x):
        self.api.exchange.set_actuator_value(state, self.data['mode_actuator'], x)

    def on_begin_zone_timestep_before_init_heat_balance(self, state) -> int:
        if 'mode_actuator' not in self.data:
            self.data['mode_actuator'] = self.api.exchange.get_actuator_handle(
                state, MODE_SCHEDULE_TYPE, "Schedule Value", MODE_SCHEDULE_NAME
            )
            if self.data['mode_actuator'] == -1:
                self.api.runtime.issue_severe(state, "Could not get actuator handle to TES mode schedule")
                return 1
            
            self.data['oat_handle'] = self.api.exchange.get_variable_handle(state,
                                        "Site Outdoor Air Drybulb Temperature", "Environment")
            if self.data['oat_handle'] == -1:
                self.api.runtime.issue_severe(state, "Could not get handle to outdoor air drybulb temperature")
                return 1
            
            self.data['mode_schedule'] = self.api.exchange.get_variable_handle(state, "Schedule Value", MODE_SCHEDULE_NAME)
            if self.data['mode_schedule'] == -1:
                self.api.runtime.issue_severe(state, "Could not get variable handle to TES mode schedule")
                return 1
            
            self.data['soc'] = self.api.exchange.get_global_handle(state, "soc")
            if self.data['soc'] == -1:
                self.api.runtime.issue_severe(state, "Could not get global handle to state of charge variable")
                return 1
        
        # Get values
        oat = self.api.exchange.get_variable_value(state, self.data['oat_handle'])
        mode = self.api.exchange.get_variable_value(state, self.data['mode_schedule'])
        soc = self.api.exchange.get_global_value(state, self.data['soc'])

        month = self.api.exchange.month(state)
        day_of_month = self.api.exchange.day_of_month(state)
        if month == 7 and day_of_month == 7:
            if mode == Mode.DISCHARGE.value:
                if oat <= 30.0 or soc <= 0.3:
                    self.actuate(state, Mode.IDLE.value)

        return 0
