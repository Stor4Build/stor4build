"""insert your copyright here.

# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/
"""

import typing

import openstudio


class AddDXCoilOutputs(openstudio.measure.ModelMeasure):
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
        return "Add DX Coil Outputs"

    def description(self):
        """Human readable description.

        The measure description is intended for a general audience and should not assume
        that the reader is familiar with the design and construction practices suggested by the measure.
        """
        return "Add the output variables needed to compare to the DX coil TES system"

    def modeler_description(self):
        """Human readable description of modeling approach.

        The modeler description is intended for the energy modeler using the measure.
        It should explain the measure's intent, and include any requirements about
        how the baseline model must be set up, major assumptions made by the measure,
        and relevant citations or references to applicable modeling resources
        """
        return "Add the output variables needed to compare to the DX coil TES system"

    def arguments(self, model: typing.Optional[openstudio.model.Model] = None):
        """Prepares user arguments for the measure.

        Measure arguments define which -- if any -- input parameters the user may set before running the measure.
        """
        args = openstudio.measure.OSArgumentVector()

        #example_arg = openstudio.measure.OSArgument.makeStringArgument("space_name", True)
        #example_arg.setDisplayName("New space name")
        #example_arg.setDescription("This name will be used as the name of the new space.")
        #args.append(example_arg)

        return args

    def run(
        self,
        model: openstudio.model.Model,
        runner: openstudio.measure.OSRunner,
        user_arguments: openstudio.measure.OSArgumentMap,
    ):
        """Defines what happens when the measure is run."""
        super().run(model, runner, user_arguments)  # Do **NOT** remove this line

        runner.registerInitialCondition(f'The model started with {len(model.getOutputMeters())} output meters.')

        # Output:Meter,Electricity:Facility,Timestep;
        # Output:Meter,Electricity:Building,Timestep;
        # Output:Meter,Electricity:HVAC,Timestep;
        # Output:Meter,Cooling:Electricity,Timestep;
        # Output:Meter,Fans:Electricity,Timestep;

        meter_names = ['Electricity:Facility', 'Electricity:Building', 'Electricity:HVAC', 'Cooling:Electricity']

        for name in meter_names:
            meter = openstudio.model.OutputMeter(model)
            meter.setName(name)
            meter.setMeterFileOnly(False)
            meter.setReportingFrequency("Timestep")
            runner.registerInfo(f'Added "{name}" output meter.')

        # report final condition of model
        runner.registerFinalCondition(f"The building finished with {len(model.getOutputMeters())} output meters.")

        return True


# register the measure to be used by the application
AddDXCoilOutputs().registerWithApplication()
