# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause

import openstudio


class AddPathToPluginPaths(openstudio.measure.EnergyPlusMeasure):
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
        return "Add Path To Plugin Paths"

    def description(self):
        """Human readable description.

        The measure description is intended for a general audience and should not assume
        that the reader is familiar with the design and construction practices suggested by the measure.
        """
        return "Add the specified path to the PythonPlugin:SearchPaths object."

    def modeler_description(self):
        """Human readable description of modeling approach.

        The modeler description is intended for the energy modeler using the measure.
        It should explain the measure's intent, and include any requirements about
        how the baseline model must be set up, major assumptions made by the measure,
        and relevant citations or references to applicable modeling resources
        """
        return "Add the specified path to the PythonPlugin:SearchPaths object."

    def arguments(self, workspace: openstudio.Workspace):
        """Prepares user arguments for the measure.

        Measure arguments define which -- if any -- input parameters the user may set before running the measure.
        """
        args = openstudio.measure.OSArgumentVector()

        arg = openstudio.measure.OSArgument.makeStringArgument("path", True)
        arg.setDisplayName("Path")
        arg.setDescription("Path to add to the Python search path.")
        args.append(arg)

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
        path_name = runner.getStringArgumentValue("path", user_arguments)

        # check the zone_name for reasonableness
        if not path_name:
            runner.registerError("Empty path was entered.")
            return False

        # get all thermal zones in the starting workspace
        objs = workspace.getObjectsByType("PythonPlugin_SearchPaths")
        if objs:
            runner.registerInitialCondition(f"The model started with a PythonPlugin:SearchPaths object.")
            i = objs[0].numFields()
            objs[0].setString(i, path_name)
        else:
            runner.registerInitialCondition("The model started without a PythonPlugin:SearchPaths object.")
            new_object_string = f'''
PythonPlugin:SearchPaths,
    PyPaths,     !- Name
    Yes,         !- Add Current Working Directory to Search Path
    Yes,         !- Add Input File Directory to Search Path
    No,          !- Add epin Environment Variable to Search Path
    {path_name}; !- Search Path 1
'''
            idfObject_: openstudio.OptionalIdfObject = openstudio.IdfObject.load(new_object_string)
            idfObject: openstudio.IdfObject = idfObject_.get()
            #wsObject: openstudio.OptionalWorkspaceObject = workspace.addObject(idfObject)
            workspace.addObject(idfObject)

        runner.registerInfo(f"Added path '{path_name}' to PythonPlugin:SearchPaths.")

        # report final condition of model
        runner.registerFinalCondition("The model finished with a PythonPluginSearchPaths object.")

        return True


# register the measure to be used by the application
AddPathToPluginPaths().registerWithApplication()
