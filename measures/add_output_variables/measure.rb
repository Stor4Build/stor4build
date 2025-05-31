# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause

# start the measure
class AddOutputVariables < OpenStudio::Measure::ModelMeasure
  # human readable name
  def name
    # Measure name should be the title case of the class name.
    return 'Add Output Variables'
  end

  # human readable description
  def description
    return 'Add output variables.'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'Add output variables.'
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new

    return args
  end

  # define what happens when the measure is run
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)

    # use the built-in error checking
    if !runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end

    # report initial condition of model
    runner.registerInitialCondition("The model started with #{model.getOutputVariables.size} output variables.")

    # add hourly output variables
    hourly_vars = ["Chiller Electricity Rate",
                   "Chiller Electricity Energy",
                   "Chiller Evaporator Inlet Temperature",
                   "Chiller Evaporator Outlet Temperature",
                   "Chiller Evaporator Mass Flow Rate",
                   "Chiller Evaporator Cooling Energy"]

    hourly_vars.each{ |var|
      ov = OpenStudio::Model::OutputVariable.new(var, model)
      ov.setReportingFrequency("Hourly")
      ov.setKeyValue("*")
      runner.registerInfo("Added #{var} output variable.")
    }
    
    # add timestep output variables
    #timstp_vars = ["Chiller Electricity Rate",
    #               "Chiller Electricity Energy",
    #               "Chiller Evaporator Inlet Temperature",
    #               "Chiller Evaporator Outlet Temperature",
    #               "Chiller Evaporator Mass Flow Rate"]
    timstp_vars = []

    timstp_vars.each{ |var|
      ov = OpenStudio::Model::OutputVariable.new(var, model)
      ov.setReportingFrequency("Timestep")
      ov.setKeyValue("*")
      runner.registerInfo("Added #{var} output variable.")
    }

    # report final condition of model
    runner.registerFinalCondition("The model finished with #{model.getOutputVariables.size} output variables.")

    return true
  end
end

# register the measure to be used by the application
AddOutputVariables.new.registerWithApplication
