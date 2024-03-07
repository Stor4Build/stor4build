# *******************************************************************************
# OpenStudio(R), Copyright (c) 2008-2024, Alliance for Sustainable Energy, LLC.
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
# specific prior written permission from Alliance for Sustainable Energy, LLC.
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
class AddPyTank < OpenStudio::Measure::EnergyPlusMeasure

  # human readable name
  def name
    return 'Add Python Tank'
  end

  # human readable description
  def description
    return 'This measure will add the Python tank model.'
  end

  # human readable description of modeling approach
  def modeler_description
    return 'This measure will add the python tank model.'
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
    args << chrg_temp

    # create argument for number of tanks
    num_tanks = OpenStudio::Measure::OSArgument.makeDoubleArgument(
      'num_tanks',
      false
    )
    num_tanks.setDefaultValue(1)
    args << num_tanks

    # create argument for chiller trim temperature
    trim_temp = OpenStudio::Measure::OSArgument.makeDoubleArgument(
      'trim_temp',
      false
    )
    trim_temp.setDefaultValue(10)
    args << trim_temp

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
    num_tanks = runner.getDoubleArgumentValue('num_tanks', usr_args)
    trim_temp = runner.getDoubleArgumentValue('trim_temp', usr_args)

    # add num tanks schedule
    ot = 'Schedule_Constant'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Num Tanks')
    no.setString(1, 'Any Number')
    no.setDouble(2, num_tanks)
    ws.addObject(no)

    # add num tanks schedule output variable (for python plugin)
    ot = 'Output_Variable'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Num Tanks')
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
    ot = 'Schedule_Constant'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Trim Temp')
    no.setString(1, 'Any Number')
    no.setDouble(2, trim_temp)
    ws.addObject(no)

    # add chiller trim temperature schedule output variable
    ot = 'Output_Variable'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Trim Temp')
    no.setString(1, 'Schedule Value')
    no.setString(2, 'Timestep')
    ws.addObject(no)

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
    ot = 'Schedule_Compact'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Chiller Temp Sch')
    no.setString(1, 'Temperature')
    no.setString(2, 'Through: 12/31')
    no.setString(3, 'For: AllDays')
    no.setString(4, 'Until: 24:00')
    no.setDouble(5, 6.7)
    ws.addObject(no)

    # add ice tank temperature schedule
    ot = 'Schedule_Compact'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Ice Tank Temp Sch')
    no.setString(1, 'Temperature')
    no.setString(2, 'Through: 12/31')
    no.setString(3, 'For: AllDays')
    no.setString(4, 'Until: 24:00')
    no.setDouble(5, 6.7)
    ws.addObject(no)

    # add python plugin instances
    ot = 'PythonPlugin_Instance'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Ice Tank Set Prgm')
    no.setString(1, 'No')
    no.setString(2, 'icetes')
    no.setString(3, 'UsrDefPlntCmpSet')
    ws.addObject(no)
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Ice Tank Sim Prgm')
    no.setString(1, 'No')
    no.setString(2, 'icetes')
    no.setString(3, 'UsrDefPlntCmpSim')
    ws.addObject(no)

    # modify chilled water loop parameters to permit ice making
    ot = 'PlantLoop'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.getString(0, false).get == 'Chilled Water Loop'
        o.setDouble(5, 100)
        o.setDouble(6, -50)
      end
    end

    # add user-defined plant component
    ot = 'PlantComponent_UserDefined'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Ice Tank')
    no.setString(1, '')
    no.setInt(2,1)
    no.setString(3, '90.1-2007 WaterCooled  Centrifugal Chiller 0 374tons 0.6kW/ton Supply Outlet Water Node')
    no.setString(4, 'Ice Tank Outlet Node')
    no.setString(5, 'MeetsLoadWithNominalCapacityLowOutLimit')
    no.setString(6, 'NeedsFlowAndTurnsLoopOn')
    no.setString(7, 'Ice Tank Set Prgm')
    no.setString(8, 'Ice Tank Sim Prgm')
    (9..26).each {|i| no.setString(i, '')}
    no.setString(27, 'Ice Tank OA Inlet Node')
    no.setString(28, 'Ice Tank OA Outlet Node')
    (29..31).each {|i| no.setString(i, '')}
    ws.addObject(no)

    # add ice tank to cooling supply equipment branch
    ot = 'Branch'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.getString(0, false).get == 'Chilled Water Loop Supply Branch 1'
        o.setString(5, '90.1-2007 WaterCooled  Centrifugal Chiller 0 374tons 0.6kW/ton Supply Outlet Water Node')
        o.setString(6, 'PlantComponent:UserDefined')
        o.setString(7, 'Ice Tank')
        o.setString(8, '90.1-2007 WaterCooled  Centrifugal Chiller 0 374tons 0.6kW/ton Supply Outlet Water Node')
        o.setString(9, 'Ice Tank Outlet Node')
      end
    end

    # modify chiller outlet node and minimum temperature
    ot = 'Chiller_Electric_EIR'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.name.get == '90.1-2007 WaterCooled  Centrifugal Chiller 0 374tons 0.6kW/ton'
        o.setDouble(21, chrg_temp)
      end
    end

    # add chiller setpoint manager
    ot = 'SetpointManager_Scheduled'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Chilled Water Loop Chiller 1 Setpoint Manager')
    no.setString(1, 'Temperature')
    no.setString(2, 'Chiller Temp Sch')
    no.setString(3, '90.1-2007 WaterCooled  Centrifugal Chiller 0 374tons 0.6kW/ton Supply Outlet Water Node')
    ws.addObject(no)

    # add user-defined plant component OA node
    ot = 'OutdoorAir_Node'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Ice Tank OA Inlet Node')
    no.setDouble(1,0)
    ws.addObject(no)

    # add user-defined plant component setpoint manager
    ot = 'SetpointManager_Scheduled'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Ice Tank Setpoint Manager')
    no.setString(1, 'Temperature')
    no.setString(2, 'Ice Tank Temp Sch')
    no.setString(3, 'Ice Tank Outlet Node')
    ws.addObject(no)

    # modify plant equipment list
    ot = 'PlantEquipmentList'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.getString(0,false).get == 'Chilled Water Loop Cooling Equipment List'
        o.setString(5, 'PlantComponent:UserDefined')
        o.setString(6, 'Ice Tank')
      end
    end

    # remove cooling load operation scheme
    uv = OpenStudio::UUIDVector.new
    ot = 'PlantEquipmentOperation_CoolingLoad'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.name.get == 'Chilled Water Loop Cooling Operation Scheme'
        uv << o.handle
      end
    end
    ws.removeObjects(uv)

    # add a component setpoint operation scheme
    ot = 'PlantEquipmentOperation_ComponentSetpoint'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Chilled Water Loop Op Scheme')
    no.setString(1, 'Chiller:Electric:EIR')
    no.setString(2, '90.1-2007 WaterCooled  Centrifugal Chiller 0 374tons 0.6kW/ton')
    no.setString(3, '90.1-2007 WaterCooled  Centrifugal Chiller 0 374tons 0.6kW/ton Supply Inlet Water Node')
    no.setString(4, '90.1-2007 WaterCooled  Centrifugal Chiller 0 374tons 0.6kW/ton Supply Outlet Water Node')
    no.setString(5, 'Autosize')
    no.setString(6, 'Cooling')
    no.setString(7, 'PlantComponent:UserDefined')
    no.setString(8, 'Ice Tank')
    no.setString(9, '90.1-2007 WaterCooled  Centrifugal Chiller 0 374tons 0.6kW/ton Supply Outlet Water Node')
    no.setString(10, 'Ice Tank Outlet Node')
    no.setString(11, 'Autosize')
    no.setString(12, 'Cooling')
    ws.addObject(no)

    # modify plant equipment operation scheme
    ot = 'PlantEquipmentOperationSchemes'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.getString(0 ,false).get == 'Chilled Water Loop Operation Schemes'
        o.setString(1, 'PlantEquipmentOperation:ComponentSetpoint')
        o.setString(2, 'Chilled Water Loop Op Scheme')
      end
    end

    # add python plugin search paths
    ot = 'PythonPlugin_SearchPaths'
    if ws.getObjectsByType(ot.to_IddObjectType).empty?
      p = File.expand_path(File.dirname(File.dirname(File.dirname(__FILE__))))
      no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
      no.setString(0, 'PyPaths')
      no.setString(1, 'Yes')
      no.setString(2, 'Yes')
      no.setString(3, 'No')
      if (RUBY_PLATFORM =~ /linux/) != nil
        no.setString(
          4,
          '/usr/local/lib/python3.8/dist-packages'
      )
      elsif (RUBY_PLATFORM =~ /darwin/) != nil
        no.setString(
          4,
          '/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages'
        )
      elsif (RUBY_PLATFORM =~ /cygwin|mswin|mingw|bccwin|wince|emx/) != nil
        h = ENV['USERPROFILE'].to_s.gsub('\\', '/')
        no.setString(
          4,
          "#{h}/AppData/Local/Programs/Python/Python38/Lib/site-packages"
        )
      end
      no.setString(5, File.join(p, 'resources'))
      ws.addObject(no)
    end

    # add python global variables
    ot = 'PythonPlugin_Variables'
    if ws.getObjectsByType(ot.to_IddObjectType).empty?
      no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
      no.setString(0, 'PyVars')
      no.setString(1, 'soc')
      no.setString(2, 't_branch_in')
      no.setString(3, 't_branch_out')
      no.setString(4, 't_tank_out')
      no.setString(5, 'mdot_branch')
      no.setString(6, 'mdot_tank')
      ws.addObject(no)
    else
      ws.getObjectsByType(ot.to_IddObjectType).each do |o|
        i = o.numFields
        ['soc',
          't_branch_in',
          't_branch_out',
          't_tank_out',
          'mdot_branch',
          'mdot_tank'
        ].each do |v|
          o.setString(i,v)
          i+=1
        end
      end
    end

    # add python plugin output variables
    ['soc',
      't_branch_in',
      't_branch_out',
      't_tank_out',
      'mdot_branch',
      'mdot_tank'
    ].each do |v|
      ot = 'PythonPlugin_OutputVariable'
      no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
      no.setString(0, v)
      no.setString(1, v)
      no.setString(2, 'Averaged')
      no.setString(3, 'SystemTimestep')
      no.setString(4, '')
      ws.addObject(no)
      ot = 'Output_Variable'
      no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
      no.setString(0, v)
      no.setString(1, 'PythonPlugin:OutputVariable')
      no.setString(2, 'Timestep')
      ws.addObject(no)
    end

    # add output variables
    ['Charge Sch', 'Chiller Temp Sch', 'Ice Tank Temp Sch'].each do |v|
      ot = 'Output_Variable'
      no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
      no.setString(0,v)
      no.setString(1, 'Schedule Value')
      no.setString(2, 'Timestep')
      ws.addObject(no)
    end

    # remove extra setpoint operation scheme
    uv = OpenStudio::UUIDVector.new
    ot = 'PlantEquipmentOperation_ComponentSetpoint'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.getString(0, false).get[0, 44] == 'Plant Equipment Operation Component Setpoint'
        uv << o.handle
      end
    end
    ws.removeObjects(uv)

  end

end

# register the measure to be used by the application
AddPyTank.new.registerWithApplication
