# *******************************************************************************
# OpenStudio(R), Copyright (c) Alliance for Sustainable Energy, LLC. and contributors
# See also https://openstudio.net/license
# *******************************************************************************

# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# start the measure
class SetTimestep < OpenStudio::Ruleset::ModelUserScript
  # human readable name
  def name
    return 'SetTimestep'
  end

  # human readable description
  def description
    return 'Sets the timestep for simulation'
  end

  # human readable description of modeling approach
  def modeler_description
    return ''
  end

  # define the arguments that the user will input
  def arguments(model)
    args = OpenStudio::Ruleset::OSArgumentVector.new

    timesteps_per_hour = OpenStudio::Ruleset::OSArgument.makeIntegerArgument('timesteps_per_hour', true)
    timesteps_per_hour.setDisplayName('Timesteps per hour')
    timesteps_per_hour.setDescription('Number of simulation timesteps per hour')
    args << timesteps_per_hour

    return args
  end

  # define what happens when the measure is run
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)

    # use the built-in error checking
    if !runner.validateUserArguments(arguments(model), user_arguments)
      return false
    end

    # assign the user inputs to variables
    timesteps_per_hour = runner.getIntegerArgumentValue('timesteps_per_hour', user_arguments)

    # check for reasonableness
    if timesteps_per_hour < 1
      runner.registerError('Timesteps per hour must be greater than or equal to 1')
      return false
    end

    model.getTimestep.setNumberOfTimestepsPerHour(timesteps_per_hour)

    return true
  end
end

# register the measure to be used by the application
SetTimestep.new.registerWithApplication
