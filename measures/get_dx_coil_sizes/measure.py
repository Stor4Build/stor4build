# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause

from pathlib import Path

import openstudio


class GetDXCoilSizes(openstudio.measure.ReportingMeasure):
    """An ReportingMeasure."""

    def name(self):
        """Returns the human readable name.

        Measure name should be the title case of the class name.
        The measure name is the first contact a user has with the measure;
        it is also shared throughout the measure workflow, visible in the OpenStudio Application,
        PAT, Server Management Consoles, and in output reports.
        As such, measure names should clearly describe the measure's function,
        while remaining general in nature
        """
        return "Get DX Coil Sizes"

    def description(self):
        """Human readable description.

        The measure description is intended for a general audience and should not assume
        that the reader is familiar with the design and construction practices suggested by the measure.
        """
        return "Get the DX Coil ice capacities."

    def modeler_description(self):
        """Human readable description of modeling approach.

        The modeler description is intended for the energy modeler using the measure.
        It should explain the measure's intent, and include any requirements about
        how the baseline model must be set up, major assumptions made by the measure,
        and relevant citations or references to applicable modeling resources
        """
        return "Get the DX Coil ice capacities."

    def arguments(self, model: openstudio.model.Model):
        """Prepares user arguments for the measure.

        Measure arguments define which -- if any -- input parameters the user may set before running the measure.
        """
        args = openstudio.measure.OSArgumentVector()

        return args

    def outputs(self):
        """Define the outputs that the measure will create."""
        outs = openstudio.measure.OSOutputVector()

        # this measure does not produce machine readable outputs with registerValue, return an empty list

        return outs

    def energyPlusOutputRequests(
        self, runner: openstudio.measure.OSRunner, user_arguments: openstudio.measure.OSArgumentMap
    ):
        """Returns a vector of IdfObject's to request EnergyPlus objects needed by the run method."""
        super().energyPlusOutputRequests(runner, user_arguments)  # Do **NOT** remove this line

        result = openstudio.IdfObjectVector()

        return result

    def run(self, runner: openstudio.measure.OSRunner, user_arguments: openstudio.measure.OSArgumentMap):
        """Defines what happens when the measure is run."""
        super().run(runner, user_arguments)

        # get the last model and sql file
        model = runner.lastOpenStudioModel()
        if not model.is_initialized():
            runner.registerError("Cannot find last model.")
            return False
        model = model.get()

        # use the built-in error checking (need model)
        if not runner.validateUserArguments(self.arguments(model), user_arguments):
            return False

        # load sql file
        sql_file = runner.lastEnergyPlusSqlFile()
        if not sql_file.is_initialized():
            runner.registerError("Cannot find last sql file.")
            return False

        sql_file = sql_file.get()
        model.setSqlFile(sql_file)
        
        # select CompName, Value from ComponentSizes where CompType='Coil:Cooling:DX:SingleSpeed:ThermalStorage' and Description='Ice Storage Capacity';
        names = sql_file.execAndReturnVectorOfString("select CompName from ComponentSizes where CompType='Coil:Cooling:DX:SingleSpeed:ThermalStorage' and Description='Ice Storage Capacity';")
        if names.is_initialized():
            names = names.get()
        else:
            names = []
        values = sql_file.execAndReturnVectorOfString("select Value from ComponentSizes where CompType='Coil:Cooling:DX:SingleSpeed:ThermalStorage' and Description='Ice Storage Capacity';")
        if values.is_initialized():
            values = values.get()
        else:
            values = []
        
        out_path = Path("./report.csv").absolute()
        with open(out_path, "w") as fp:
            fp.write(','.join(names) + '\n')
            fp.write(','.join(values) + '\n')

        return True


# register the measure to be used by the application
GetDXCoilSizes().registerWithApplication()
