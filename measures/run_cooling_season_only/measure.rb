# insert your copyright here

# see the URL below for information on how to write OpenStudio measures
# http://nrel.github.io/OpenStudio-user-documentation/reference/measure_writing_guide/

# start the measure
class AddOutputVariables < OpenStudio::Measure::ModelMeasure
  # human readable name
  def name
    # Measure name should be the title case of the class name.
    return 'Run Cooling Season Only'
  end

  # human readable description
  def description
    return 'Run cooling season only.'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'Run cooling season only.'
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

    # get the RunPeriod object
    rp = model.getRunPeriod()

    # report initial condition of model
    runner.registerInitialCondition("The model was to be run from #{rp.getBeginMonth()}/#{rp.getBeginDayOfMonth()} to #{rp.getEndMonth()}/#{rp.getEndDayOfMonth()}.")

    rp.setBeginDayOfMonth(1)
    rp.setBeginMonth(4)
    rp.setEndDayOfMonth(30)
    rp.setEndMonth(9)

    # report final condition of model
    runner.registerInitialCondition("The model now be run from #{rp.getBeginMonth()}/#{rp.getBeginDayOfMonth()} to #{rp.getEndMonth()}/#{rp.getEndDayOfMonth()}.")

    return true
  end
end

# register the measure to be used by the application
AddOutputVariables.new.registerWithApplication
