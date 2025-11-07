# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import typing
import os

import openstudio

thermaltank_custom_module = '''# This file is generated code, modify at your own risk.
from enum import Enum

class Mode(Enum):
    CHARGE = 1
    IDLE = 0
    DISCHARGE = -1

MODE_SCHEDULE_TYPE = 'Schedule:Compact'
MODE_SCHEDULE_NAME = 'Something'
'''


class AddDemoNoonToSix(openstudio.measure.ModelMeasure):
    """A ModelMeasure."""

    def name(self):
        """Returns the human readable name.

        Measure name should be the title case of the class name.
        The measure name is the first contact a user has with the measure;
        it is also shared throughout the measure workflow, visible in the OpenStudio Application,
        PAT, Server Management Consoles, and in output reports.
        As such, measure names should clearly describe the measure's function,
        while remaining general in nature
        """
        return "Add Demo Noon to Six"

    def description(self):
        """Human readable description.

        The measure description is intended for a general audience and should not assume
        that the reader is familiar with the design and construction practices suggested by the measure.
        """
        return "Add the demo Python plugin that runs a TES system (via a schedule) from noon until 6PM."

    def modeler_description(self):
        """Human readable description of modeling approach.

        The modeler description is intended for the energy modeler using the measure.
        It should explain the measure's intent, and include any requirements about
        how the baseline model must be set up, major assumptions made by the measure,
        and relevant citations or references to applicable modeling resources
        """
        return "Add the demo Python plugin that runs a TES system (via a schedule) from noon until 6PM."

    def arguments(self, model: typing.Optional[openstudio.model.Model] = None):
        """Prepares user arguments for the measure.

        Measure arguments define which -- if any -- input parameters the user may set before running the measure.
        """
        args = openstudio.measure.OSArgumentVector()

        types = ['ThermalTank-Ice', 'ThermalTank-ChilledWater', 'PackagedIceStorage']
        arg = openstudio.measure.OSArgument.makeChoiceArgument("tes_type", types, True)
        arg.setDisplayName("TES type")
        arg.setDescription("The TES system that is to be simulated.")
        arg.setDefaultValue('ThermalTank-Ice')
        args.append(arg)

        arg = openstudio.measure.OSArgument.makeStringArgument("output_directory", True)
        arg.setDisplayName("Python plugin output directory")
        arg.setDescription("The directory to place the case-specific Python plugin file.")
        arg.setDefaultValue('.')
        args.append(arg)

        return args

    def run(
        self,
        model: openstudio.model.Model,
        runner: openstudio.measure.OSRunner,
        user_arguments: openstudio.measure.OSArgumentMap,
    ):
        """Defines what happens when the measure is run."""
        super().run(model, runner, user_arguments)  # Do **NOT** remove this line

        if not (runner.validateUserArguments(self.arguments(model), user_arguments)):
            return False

        # assign the user inputs to variables
        tes_type = runner.getChoiceArgumentValue("tes_type", user_arguments)
        output_directory = runner.getStringArgumentValue("output_directory", user_arguments)

        # check the args for reasonableness
        if not os.path.exists(output_directory):
            runner.registerError(f'Output directory "{output_directory}" does not exist.')
            return False

        # report initial condition of model
        runner.registerInitialCondition(f'Applying control schedule for "{tes_type}".')

        # write out the system-specific details
        if tes_type in ['ThermalTank-Ice', 'ThermalTank-ChilledWater']:
            txt = thermaltank_custom_module
        else:
            pass

        with open('case_details.py', 'w') as fp:
            fp.write(txt)

        # Add Python plugin stuff here

        # report final condition of model
        runner.registerFinalCondition(f'Control schedule for "{tes_type}" applied.')

        return True


# register the measure to be used by the application
AddDemoNoonToSix().registerWithApplication()
