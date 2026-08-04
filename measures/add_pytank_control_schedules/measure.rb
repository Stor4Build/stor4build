# *******************************************************************************
# OpenStudio(R), Copyright (c) 2008-2025, Alliance for Energy Innovation, LLC and contributors
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# (1) Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# (2) Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distributiono.
#
# (3) Neither the name of the copyright holder nor the names of any contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission from the respective party.
#
# (4) Other than as required in clauses (1) and (2), distributions in any form
# of modifications or other derivative works may not use the "OpenStudio"
# trademark, "OS", "os", or any other confusingly similar designation without
# specific prior written permission from Alliance for Energy Innovation, LLC.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE
# UNITED STATES GOVERNMENT, OR THE UNITED STATES DEPARTMENT OF ENERGY, NOR ANY OF
# THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# *******************************************************************************

# start the measure
class AddPyTankControlSchedules < OpenStudio::Measure::EnergyPlusMeasure

  # human readable name
  def name
    return 'Add Python Tank Control Schedules'
  end

  # human readable description
  def description
    return 'This measure will add the Python tank model control schedules.'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'This measure will add the python tank model control schedules.'
  end

  # define the arguments that the user will input
  def arguments(ws)

    # create empty argument vector to add arguments to
    args = OpenStudio::Measure::OSArgumentVector.new

    # create argument for charge start time
    chrg_start = OpenStudio::Measure::OSArgument.makeStringArgument(
      'chrg_start',
      false
    )
    chrg_start.setDefaultValue('21:00')
    args << chrg_start

    # create argument for charge end time
    chrg_end = OpenStudio::Measure::OSArgument.makeStringArgument(
      'chrg_end',
      false
    )
    chrg_end.setDefaultValue('07:00')
    args << chrg_end

    # create argument for discharge start time
    dchrg_start = OpenStudio::Measure::OSArgument.makeStringArgument(
      'dchrg_start',
      false
    )
    dchrg_start.setDefaultValue('12:00')
    args << dchrg_start

    # create argument for discharge end time
    dchrg_end = OpenStudio::Measure::OSArgument.makeStringArgument(
      'dchrg_end',
      false
    )
    dchrg_end.setDefaultValue('18:00')
    args << dchrg_end

    # create argument for charge temperature
    chrg_temp = OpenStudio::Measure::OSArgument.makeDoubleArgument(
      'chrg_temp',
      false
    )
    chrg_temp.setDefaultValue(-3.8)
    chrg_temp.setUnits('C')
    args << chrg_tempe

    return args
  end

  # define what happens when the measure is run
  def run(ws, runner, usr_args)

    # call the parent class method
    super(ws, runner, usr_args)

    # use the built-in error checking
    return false unless runner.validateUserArguments(arguments(ws), usr_args)

    # assign user arguments to variables
    chrg_start = runner.getStringArgumentValue('chrg_start', usr_args)
    chrg_end = runner.getStringArgumentValue('chrg_end', usr_args)
    dchrg_start = runner.getStringArgumentValue('dchrg_start', usr_args)
    dchrg_end = runner.getStringArgumentValue('dchrg_end', usr_args)
    chrg_temp = runner.getDoubleArgumentValue('chrg_temp', usr_args)

    # add discharge start time schedule
    ot = 'Schedule_Constant'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Discharge Start Time')
    no.setString(1, 'Any Number')
    dchrg_start_hr = dchrg_start.split(':')[0].to_f
    dchrg_start_min = dchrg_start.split(':')[1].to_f
    no.setDouble(2, dchrg_start_hr + (dchrg_start_min / 60))
    ws.addObject(no)

    # add discharge start time schedule output variable
    ot = 'Output_Variable'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Discharge Start Time')
    no.setString(1, 'Schedule Value')
    no.setString(2, 'Timestep')
    ws.addObject(no)

    # add discharge end time schedule
    ot = 'Schedule_Constant'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Discharge End Time')
    no.setString(1, 'Any Number')
    dchrg_end_hr = dchrg_end.split(':')[0].to_f
    dchrg_end_min = dchrg_end.split(':')[1].to_f
    no.setDouble(2, dchrg_end_hr + (dchrg_end_min / 60))
    ws.addObject(no)

    # add discharge end time schedule output variable
    ot = 'Output_Variable'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Discharge End Time')
    no.setString(1, 'Schedule Value')
    no.setString(2, 'Timestep')
    ws.addObject(no)

    # add chiller charge temperature schedule
    ot = 'Schedule_Constant'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Chrg Temp')
    no.setString(1, 'Any Number')
    no.setDouble(2, chrg_temp)
    ws.addObject(no)

    # add chiller charge temperature schedule output variable
    ot = 'Output_Variable'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Chrg Temp')
    no.setString(1, 'Schedule Value')
    no.setString(2, 'Timestep')
    ws.addObject(no)

    # add chiller trim temperature schedule
    #ot = 'Schedule_Constant'
    #no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    #no.setString(0, 'Trim Temp')
    #no.setString(1, 'Any Number')
    #no.setDouble(2, trim_temp)
    #ws.addObject(no)

    # add chiller trim temperature schedule output variable
    #ot = 'Output_Variable'
    #no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    #no.setString(0, 'Trim Temp')
    #no.setString(1, 'Schedule Value')
    #no.setString(2, 'Timestep')
    #ws.addObject(no)

    # add charge schedule
    ot = 'Schedule_Compact'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Charge Sch')
    no.setString(1, 'Any Number')
    no.setString(2, 'Through: 12/31')
    no.setString(3, 'For: AllDays')
    no.setString(4, "Until: #{chrg_end}")
    no.setDouble(5, 1)
    no.setString(6, "Until: #{dchrg_start}")
    no.setDouble(7, 0)
    no.setString(8, "Until: #{dchrg_end}")
    no.setDouble(9, -1)
    no.setString(10, "Until: #{chrg_start}")
    no.setDouble(11, 0)
    no.setString(12, 'Until: 24:00')
    no.setDouble(13, 1)
    ws.addObject(no)

    # add chiller temperature schedule
    #ot = 'Schedule_Compact'
    #no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    #no.setString(0, 'Chiller Temp Sch')
    #no.setString(1, 'Temperature')
    #no.setString(2, 'Through: 12/31')
    #no.setString(3, 'For: AllDays')
    #no.setString(4, 'Until: 24:00')
    #no.setDouble(5, 6.7)
    #ws.addObject(no)

    # add ice tank temperature schedule
    #ot = 'Schedule_Compact'
    #no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    #no.setString(0, 'Ice Tank Temp Sch')
    #no.setString(1, 'Temperature')
    #no.setString(2, 'Through: 12/31')
    #no.setString(3, 'For: AllDays')
    #no.setString(4, 'Until: 24:00')
    #no.setDouble(5, 6.7)
    #ws.addObject(no)

    return true
  end

end

# register the measure to be used by the application
AddPyTankControlSchedules.new.registerWithApplication
