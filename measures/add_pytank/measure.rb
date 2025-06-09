# *******************************************************************************
# OpenStudio(R), Copyright (c) 2008-2025, Alliance for Sustainable Energy, LLC.
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

    # create argument for storage type
    storage_chs = OpenStudio::StringVector.new
    storage_chs << 'ice'
    storage_chs << 'chw'
    strg_type = OpenStudio::Measure::OSArgument.makeChoiceArgument(
      'strg_type',
      storage_chs,
      true
    )
    strg_type.setDefaultValue('ice')
    strg_type.setDescription('Options are ice or chw')
    args << strg_type

    # create argument for control type
    ctrl_type = OpenStudio::Measure::OSArgument.makeStringArgument(
      'ctrl_type',
      false
    )
    ctrl_type.setDefaultValue('sch')
    ctrl_type.setDescription('Options are sch or soc')
    args << ctrl_type

    # create argument for chiller downsizing
    size_frac = OpenStudio::Measure::OSArgument.makeDoubleArgument(
      'size_frac',
      false
    )
    size_frac.setDefaultValue(1)
    size_frac.setDescription('Chiller sizing factor')
    args << size_frac

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
    strg_type = runner.getStringArgumentValue('strg_type', usr_args)
    ctrl_type = runner.getStringArgumentValue('ctrl_type', usr_args)
    size_frac = runner.getDoubleArgumentValue('size_frac', usr_args)

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

    # add num tanks schedule
    ot = 'Schedule_Constant'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Num Tanks')
    no.setString(1, 'Any Number')
    no.setDouble(2, num_tanks)
    ws.addObject(no)

    # add chiller(s) electricity rate output variable
    ot = 'Output_Variable'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, '*')
    no.setString(1, 'Chiller Electricity Rate')
    no.setString(2, 'Timestep')
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
    ['Set', 'Sim'].each do |s|
      no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
      no.setString(0, "Ice Tank #{s} Prgm")
      no.setString(1, 'No')
      no.setString(2, "#{strg_type}tes_#{ctrl_type}ctrl")
      no.setString(3, "UsrDefPlntCmp#{s}")
      ws.addObject(no)
    end

    # add ethylene glycol
    ot = 'FluidProperties_GlycolConcentration'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'TES EG30')
    no.setString(1, 'EthyleneGlycol')
    no.setString(2, '')
    no.setDouble(3, 0.3)
    ws.addObject(no)

    # modify chilled water loop parameters to permit ice making
    ot = 'PlantLoop'
    plant_loop_name = 'Chilled Water Loop'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.getString(0, false).get == plant_loop_name
        o.setString(1, 'UserDefinedFluidType')
        o.setString(2, 'TES EG30')
        o.setDouble(5, 100)
        o.setDouble(6, -50)
      end
    end

    # adjust chiller minimum temperature and get info
    chiller_info = []
    ot = 'Chiller_Electric_EIR'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      o.setDouble(11, size_frac)
      o.setDouble(12, size_frac)
      o.setDouble(21, chrg_temp)
      chiller_info << [
        o.name.get,
        o.getString(9, false).get,
        o.getString(14, false).get,
        o.getString(15, false).get
      ]
    end

    # adjust chiller plr curve
    if size_frac != 1
      ot = 'Curve_Quadratic'
      ws.getObjectsByType(ot.to_IddObjectType).each do |o|
        if o.name.get == 'ChlrWtrCentPathAAllEIRRatio_fQRatio'
          if size_frac == 0.9
            o.setDouble(2, 0.5591)
            o.setDouble(3, 0.3172)
          elsif size_frac == 0.8
            o.setDouble(2, 0.6289)
            o.setDouble(3, 0.4014)
          elsif size_frac == 0.7
            o.setDouble(2, 0.7188)
            o.setDouble(3, 0.5243)
          elsif size_frac == 0.6
            o.setDouble(2, 0.8386)
            o.setDouble(3, 0.7136)
          elsif size_frac == 0.5
            o.setDouble(2, 1.0063)
            o.setDouble(3, 1.0276)
          end
        end
      end
    end

    # remove supply outlet pipe
    uv = OpenStudio::UUIDVector.new
    ot = 'Pipe_Adiabatic'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.name.get == "#{plant_loop_name} Supply Outlet"
        uv << o.handle
      end
    end
    ws.removeObjects(uv)

    # add ice tank to cooling supply outlet branch, get node names
    tank_in_node = ''
    tank_out_node = ''
    ot = 'Branch'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.name.get == "#{plant_loop_name} Supply Outlet Branch"
        # set component type
        o.setString(2, 'PlantComponent:UserDefined')

        # get node names
        tank_in_node = o.getString(4, false).get
        tank_out_node = o.getString(5, false).get

        # add user-defined plant component
        ot = 'PlantComponent_UserDefined'
        no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
        no.setString(0, 'Ice Tank')
        no.setString(1, '')
        no.setInt(2,1)
        no.setString(3, tank_in_node)
        no.setString(4, tank_out_node)
        no.setString(5, 'MeetsLoadWithNominalCapacityLowOutLimit')
        no.setString(6, 'NeedsFlowAndTurnsLoopOn')
        no.setString(7, 'Ice Tank Set Prgm')
        no.setString(8, 'Ice Tank Sim Prgm')
        (9..26).each {|i| no.setString(i, '')}
        no.setString(27, 'Ice Tank OA Inlet Node')
        no.setString(28, 'Ice Tank OA Outlet Node')
        (29..31).each {|i| no.setString(i, '')}
        ws.addObject(no)

        # set component name (on branch)
        o.setString(3, 'Ice Tank')
      end
    end

    # add chiller setpoint manager(s)
    ot = 'SetpointManager_Scheduled'
    chiller_info.each do |a|
      no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
      no.setString(0, "#{a[0]} Setpoint Manager")
      no.setString(1, 'Temperature')
      no.setString(2, 'Chiller Temp Sch')
      no.setString(3, a[3])
      ws.addObject(no)
    end

    # add user-defined plant component OA node
    ot = 'OutdoorAir_Node'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
    no.setString(0, 'Ice Tank OA Inlet Node')
    no.setDouble(1,0)
    ws.addObject(no)

    # modify plant equipment list
    ot = 'PlantEquipmentList'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.getString(0, false).get == "#{plant_loop_name} Cooling Equipment List"
        i = o.numFields
        o.setString(i, 'PlantComponent:UserDefined')
        o.setString(i + 1, 'Ice Tank')
      end
    end

    # remove cooling load operation scheme
    uv = OpenStudio::UUIDVector.new
    ot = 'PlantEquipmentOperation_CoolingLoad'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.name.get == "#{plant_loop_name} Cooling Operation Scheme"
        uv << o.handle
      end
    end
    ws.removeObjects(uv)

    # add a component setpoint operation scheme
    ot = 'PlantEquipmentOperation_ComponentSetpoint'
    no = OpenStudio::IdfObject.new(ot.to_IddObjectType); i=0
    no.setString(0, "#{plant_loop_name} Op Scheme"); i+=1
    chiller_info.each do |a|
      no.setString(i, 'Chiller:Electric:EIR'); i+=1
      no.setString(i, a[0]); i+=1
      no.setString(i, a[2]); i+=1
      no.setString(i, a[3]); i+=1
      no.setString(i, 'Autosize'); i+=1
      no.setString(i, 'Cooling'); i+=1
    end
    no.setString(i, 'PlantComponent:UserDefined'); i+=1
    no.setString(i, 'Ice Tank'); i+=1
    no.setString(i, tank_in_node); i+=1
    no.setString(i, tank_out_node); i+=1
    no.setString(i, 'Autosize'); i+=1
    no.setString(i, 'Cooling')
    ws.addObject(no)

    # modify plant equipment operation scheme
    ot = 'PlantEquipmentOperationSchemes'
    ws.getObjectsByType(ot.to_IddObjectType).each do |o|
      if o.getString(0 ,false).get == "#{plant_loop_name} Operation Schemes"
        o.setString(1, 'PlantEquipmentOperation:ComponentSetpoint')
        o.setString(2, "#{plant_loop_name} Op Scheme")
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

    # determine tank control variable
    ctrl_var = ''
    if strg_type == 'ice'
      ctrl_var = 'soc'
    elsif strg_type == 'chw'
      ctrl_var = 'tank_temp'
    end

    # define python global variables
    py_vars = [
      ctrl_var,
      't_branch_in',
      't_branch_out',
      't_tank_out',
      'mdot_branch',
      'mdot_tank'
    ]

    # add python global variables
    ot = 'PythonPlugin_Variables'
    if ws.getObjectsByType(ot.to_IddObjectType).empty?
      no = OpenStudio::IdfObject.new(ot.to_IddObjectType)
      no.setString(0, 'PyVars')
      i = 1
      py_vars.each do |v|
        no.setString(i, v)
        i+=1
      end
      ws.addObject(no)
    else
      ws.getObjectsByType(ot.to_IddObjectType).each do |o|
        i = o.numFields
        py_vars.each do |v|
          o.setString(i, v)
          i+=1
        end
      end
    end

    # add python plugin output variables and correspinding output variables
    py_vars.each do |v|
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

    # add other output variables
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

    return true
  end

end

# register the measure to be used by the application
AddPyTank.new.registerWithApplication
