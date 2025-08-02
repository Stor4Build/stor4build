# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause

import typing

import openstudio


class AddThermalTankOutputs(openstudio.measure.ModelMeasure):
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
        return "Add ThermalTank Outputs"

    def description(self):
        """Human readable description.

        The measure description is intended for a general audience and should not assume
        that the reader is familiar with the design and construction practices suggested by the measure.
        """
        return "Add the variables needed for the ThermalTank"

    def modeler_description(self):
        """Human readable description of modeling approach.

        The modeler description is intended for the energy modeler using the measure.
        It should explain the measure's intent, and include any requirements about
        how the baseline model must be set up, major assumptions made by the measure,
        and relevant citations or references to applicable modeling resources
        """
        return "Add the variables needed for the ThermalTank"

    def arguments(self, model: typing.Optional[openstudio.model.Model] = None):
        """Prepares user arguments for the measure.

        Measure arguments define which -- if any -- input parameters the user may set before running the measure.
        """
        args = openstudio.measure.OSArgumentVector()

        baseline = openstudio.measure.OSArgument.makeBoolArgument("baseline", False)
        baseline.setDisplayName("Add variables for baseline simulation")
        baseline.setDescription("Setting this to false will add hourly variables for simulations with the ThermalTank implementd.")
        baseline.setDefaultValue(True)
        args.append(baseline)

        return args

    def run(self, model: openstudio.model.Model, runner: openstudio.measure.OSRunner, user_arguments: openstudio.measure.OSArgumentMap):

        # Defines what happens when the measure is run
        super().run(model, runner, user_arguments)  # Do **NOT** remove this line

        if not (runner.validateUserArguments(self.arguments(model), user_arguments)):
            return False

        # assign the user inputs to variables
        baseline = runner.getBoolArgumentValue("baseline", user_arguments)

        # report initial condition of model
        runner.registerInitialCondition(f"The model started with {len(model.getOutputVariables())} output variables.")

        # add hourly output variables
        # these are always added
        hourly_outputs = [('*', 'Chiller Electricity Rate'),
                          ('*', 'Chiller Electricity Energy'),
                          ('*', 'Chiller Evaporator Inlet Temperature'),
                          ('*', 'Chiller Evaporator Outlet Temperature'),
                          ('*', 'Chiller Evaporator Mass Flow Rate'),
                          ('*', 'Chiller Evaporator Cooling Energy')]
        
        # add more variables to the list if needed            
        if not baseline:
            hourly_outputs.append(('*', 'PythonPlugin:OutputVariable'))
            hourly_outputs.append(('Charge Sch', 'Schedule Value'))
        
        for key, var in hourly_outputs:
            ov = openstudio.model.OutputVariable(var, model)
            ov.setReportingFrequency('Hourly')
            ov.setKeyValue(key)
            runner.registerInfo(f'Added {var} output variable.')

        # report final condition of model
        runner.registerFinalCondition(f"The model finished with {len(model.getOutputVariables())} output variables.")

        return True


# register the measure to be used by the application
AddThermalTankOutputs().registerWithApplication()
