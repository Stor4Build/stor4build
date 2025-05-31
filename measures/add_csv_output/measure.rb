# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause

# Start the measure
class AddCSVOutput < OpenStudio::Measure::ModelMeasure

  # Define the name of the Measure.
  def name
    return 'Add CSV Output'
  end

  # Human readable description
  def description
    return 'Enable CSV outputs.'
  end

  # Human readable description of modeling approach
  def modeler_description
    return 'Enable CSV outputs.'
  end

  # Define the arguments that the user will input.
  def arguments(model)
    args = OpenStudio::Measure::OSArgumentVector.new
    return args
  end

  # Define what happens when the measure is run.
  def run(model, runner, user_arguments)
    super(model, runner, user_arguments)
    
    ocf = model.getOutputControlFiles()
    ocf.setOutputCSV(true)
    
    oct = model.getOutputControlTimestamp()
    oct.setISO8601Format(true)
    oct.setTimestampAtBeginningOfInterval(true)

    return true
  end

end

# this allows the measure to be used by the application
AddCSVOutput.new.registerWithApplication
