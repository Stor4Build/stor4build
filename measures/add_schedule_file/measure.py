# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause

import openstudio


class AddScheduleFile(openstudio.measure.EnergyPlusMeasure):
    """An EnergyPlusMeasure."""

    def name(self):
        """Returns the human readable name.

        Measure name should be the title case of the class name.
        The measure name is the first contact a user has with the measure;
        it is also shared throughout the measure workflow, visible in the OpenStudio Application,
        PAT, Server Management Consoles, and in output reports.
        As such, measure names should clearly describe the measure's function,
        while remaining general in nature
        """
        return "Add Schedule File"

    def description(self):
        """Human readable description.

        The measure description is intended for a general audience and should not assume
        that the reader is familiar with the design and construction practices suggested by the measure.
        """
        return "Add schedule file"

    def modeler_description(self):
        """Human readable description of modeling approach.

        The modeler description is intended for the energy modeler using the measure.
        It should explain the measure's intent, and include any requirements about
        how the baseline model must be set up, major assumptions made by the measure,
        and relevant citations or references to applicable modeling resources
        """
        return "Add schedule file"

    def arguments(self, workspace: openstudio.Workspace):
        """Prepares user arguments for the measure.

        Measure arguments define which -- if any -- input parameters the user may set before running the measure.
        """
        args = openstudio.measure.OSArgumentVector()

        file_name = openstudio.measure.OSArgument.makeStringArgument('file_name', True)
        file_name.setDisplayName('Schedule file name')
        file_name.setDescription('The file name of CSV containing the schedule data.')
        args.append(file_name)

        sch_name = openstudio.measure.OSArgument.makeStringArgument('schedule_name', True)
        sch_name.setDisplayName('Schedule name')
        sch_name.setDescription('The schedule name.')
        args.append(sch_name)

        sch_col = openstudio.measure.OSArgument.makeIntegerArgument('schedule_column', True)
        sch_col.setDisplayName('Schedule column')
        sch_col.setDescription('The column of the CSV containing the schedule data.')
        args.append(sch_col)

        row_skip = openstudio.measure.OSArgument.makeIntegerArgument('row_skip', False)
        row_skip.setDisplayName('Rows to skip')
        row_skip.setDescription('The number of rows to skip at the top of the file.')
        row_skip.setDefaultValue(1)
        args.append(row_skip)

        timesteps_per_hour = openstudio.measure.OSArgument.makeIntegerArgument('timesteps_per_hour', False)
        timesteps_per_hour.setDisplayName('Timesteps per hour')
        timesteps_per_hour.setDescription('Number of simulation timesteps per hour')
        timesteps_per_hour.setDefaultValue(1)
        args.append(timesteps_per_hour)

        interp = openstudio.measure.OSArgument.makeBoolArgument('interpolate', False)
        interp.setDisplayName('Interpolate to timestep')
        interp.setDescription('Interpolate the variable to the timestep.')
        interp.setDefaultValue(False)
        args.append(interp)
        
        output_var = openstudio.measure.OSArgument.makeBoolArgument('output_var', False)
        output_var.setDisplayName('Create an output variable')
        output_var.setDescription('Create an output variable for the schedule.')
        output_var.setDefaultValue(False)
        args.append(output_var)

        return args

    def run(
        self,
        workspace: openstudio.Workspace,
        runner: openstudio.measure.OSRunner,
        user_arguments: openstudio.measure.OSArgumentMap,
    ):
        """Defines what happens when the measure is run."""
        super().run(workspace, runner, user_arguments)  # Do **NOT** remove this line

        if not (runner.validateUserArguments(self.arguments(workspace), user_arguments)):
            return False

        # assign the user inputs to variables
        file_name = runner.getStringArgumentValue('file_name', user_arguments)
        sch_name = runner.getStringArgumentValue('schedule_name', user_arguments)
        sch_col = runner.getIntegerArgumentValue('schedule_column', user_arguments)
        row_skip = runner.getIntegerArgumentValue('row_skip', user_arguments)
        tph = runner.getIntegerArgumentValue('timesteps_per_hour', user_arguments)
        output_var = runner.getBoolArgumentValue('row_skip', user_arguments)
        interp = runner.getBoolArgumentValue('interpolate', user_arguments)

        yes_no = {True:'Yes', False:'No'}
        mins = {1:60, 2:30, 3:20, 4:15, 5:12, 6:10, 10:6, 12:5, 15:4, 20:3, 60:1}

        # report initial condition of workspace
        # runner.registerInitialCondition(f'The building started with {len(zones)} zones.')

        object_type = openstudio.IddObjectType('Schedule_File')
        new_object = openstudio.IdfObject(object_type)

        new_object.setString(0, sch_name)       # Name of the schedule
        new_object.setString(1, 'Any Number')   # Schedule Type Limits Name
        new_object.setString(2, file_name)      # File name
        new_object.setInt(3, sch_col)           # Column Number
        new_object.setInt(4, row_skip)          # Rows to Skip at Top
        new_object.setString(5, '')             # Number of Hours of Data
        new_object.setString(6, '')             # Column Separator
        new_object.setString(7, yes_no[interp]) # Interpolate to Timestep
        new_object.setInt(8, mins[tph])         # Minutes per Item

        workspace.addObject(new_object)

        if output_var:
            # add an output variable
            object_type = openstudio.IddObjectType('Output_Variable')
            new_object = openstudio.IdfObject(object_type)
            new_object.setString(0, sch_name)
            new_object.setString(1, 'Schedule Value')
            new_object.setString(2, 'Timestep')
            workspace.addObject(new_object)

        #runner.registerInfo(f"A zone named '{new_zone.nameString()}' was added.")

        # report final condition of model
        #finishing_zones = workspace.getObjectsByType("Zone")
        #runner.registerFinalCondition(f"The building finished with {len(finishing_zones)} zones.")

        return True


# register the measure to be used by the application
AddScheduleFile().registerWithApplication()
