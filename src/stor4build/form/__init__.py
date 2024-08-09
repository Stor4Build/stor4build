# SPDX-FileCopyrightText: 2024-present TBD
#
# SPDX-License-Identifier: BSD-3-Clause
import click
import os
import csv
import tempfile
import stor4build
from flask import Flask, request

from ..__about__ import __version__

# Make some assumptions to get the default locations
this_dir = os.path.abspath(os.path.dirname(__file__))
default_measures_dir = os.path.join(this_dir, '..', '..', '..', 'measures')
default_weather_dir = os.path.join(this_dir, '..', '..', '..', 'resources')

def create_app(config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        OPENSTUDIO='openstudio',
        MEASURES_DIR=default_measures_dir,
        WEATHER_DIR=default_weather_dir
    )

    if config is None:
        app.config.from_prefixed_env()
    else:
        app.config.from_mapping(config)
    
    openstudio_exe = app.config['OPENSTUDIO']
    measures_dir = os.path.abspath(app.config['MEASURES_DIR'])
    weather_dir = os.path.abspath(app.config['WEATHER_DIR'])

    #
    #@app.route('/prototype', methods=['GET', 'POST'])
    #def prototype_route():
    #    # POST request
    #    if request.method == 'POST':
    #        prototype = request.form.get('prototype')
    #        cz = 'ASHRAE 169-2006-%s' % request.form.get('cz')
    #        vintage = request.form.get('vintage')
    #        epw = stor4build.weather_lookup(cz)
    #        osw = {
    #            'created_at': '20200127T205012Z',
    #            'measure_paths': [ os.path.abspath(app.config['MEASURES_DIR']) ],
    #            'run_directory': os.path.join(app.instance_path, 'run'),
    #            'seed_file': '',
    #            'steps': [
    #                {
    #                    'arguments' : {
    #                        'building_type': prototype,
    #                        'climate_zone': cz,
    #                        'template': vintage
    #                        },
    #                    'measure_dir_name' : 'create_doe_prototype_building_extended',
    #                    'name' : 'Create DOE Prototype Building Extended'
    #                }
    #            ],
    #            'updated_at': '20200127T213540Z',
    #            'weather_file': os.path.join(app.config['WEATHER_DIR'], epw)
    #        }
    #        stor4build.run(app.config['OPENSTUDIO'], app.instance_path, osw)
#
#            return '''
#<h1>%s</h1>
#<h2>Climate zone: %s</h2>
#<h2>Vintage: %s</h2>
#''' % (prototype, cz, vintage)

        # GET request
        #return '''
#<form method="POST">
#    <div><label>Prototype: <select id="prototype" name="prototype">
#        %s
#        </select></label></div>
#    <div><label>Climate Zone: <select id="cz" name="cz">
#        %s
#        </select></label></div>
#    <div><label>Vintage: <select id="vintage" name="vintage">
#        %s
#        </select></label></div>
#    <input type="submit" value="Submit">
#</form>''' % (''.join(['<option value="%s">%s</option>' % (el,el) for el in stor4build.prototypes_list]),
#              ''.join(['<option value="%s">%s</option>' % (el,el) for el in stor4build.climate_zone_list]),
#              ''.join(['<option value="%s">%s</option>' % (el,el) for el in stor4build.vintage_values]))
    #
    @app.route('/icetank/simulate', methods=['GET', 'POST'])
    def icetank_simulate_route():
        # POST request
        if request.method == 'POST':
            # Get the inputs
            prototype = request.form.get('prototype') # Unused for now
            cz = 'ASHRAE 169-2006-%s' % request.form.get('cz') # Unused for now
            vintage = request.form.get('vintage') # Unused for now
            arguments = {
                "charge_start" : request.form.get('charge_start'),
                "charge_end" : request.form.get('charge_end'),
                "discharge_start" : request.form.get('discharge_start'),
                "discharge_end" : request.form.get('discharge_end'),
                "charge_temp" : request.form.get('charge_temp'),
                "num_tanks" : request.form.get('ntanks'),
                "trim_temp" : request.form.get('trim_temp')
            }
            
            #osm = os.path.join(app.config['MODELS_DIR'], stor4build.prototype_lookup(prototype, cz, vintage))
            #epw = os.path.join(app.config['WEATHER_DIR'], stor4build.weather_lookup(cz))
            osm = os.path.abspath(os.path.join(weather_dir, 'LargeOffice.osm'))
            epw = os.path.abspath(os.path.join(weather_dir, 'USA_TN_Knoxville-McGhee.Tyson.AP.723260_TMY3.epw'))

            # Run the simulation
            with tempfile.TemporaryDirectory() as run_dir:
                runner = stor4build.Runner(osm, epw, openstudio_exe, run_dir, 'run', measures_dir)
                icetank = stor4build.IceTank('icetank', **arguments)
                osw = icetank.osw(osm, measures_dir, epw)
                runner.run(osw, icetank.tag())
            
                # Process the outputs
                csv_path = os.path.join(run_dir, icetank.tag(), 'run', 'eplusout.csv')
                if not os.path.exists(csv_path):
                    return '''
<h1>Simulation Failed</h1>
<h2>Failed to find eplusout.csv</h2>
<h2>Path: %s</h2>
''' % csv_path

                # Make a plot
                titles = {'soc': 'soc:PythonPlugin:OutputVariable [](TimeStep)',
                          'chiller': '90.1-2007 WATERCOOLED  CENTRIFUGAL CHILLER 1 374TONS 0.6KW/TON:Chiller Electricity Rate [W](TimeStep)'}

                variables = list(titles.keys())

                timestamps = []
                values = []
                for var in titles.keys():
                    values.append([])
                N = len(values)
                    
                with open(csv_path, 'r') as fp:
                    reader = csv.reader(fp)
                    header = next(reader)
                    indices = {}
                    for var in variables:
                        indices[var] = header.index(titles[var])

                    for line in reader:
                        timestamp = line[0]
                        if timestamp.startswith(' 07/15'):
                            timestamps.append(timestamp)
                            for i,var in enumerate(variables):
                                values[i].append(line[indices[var]])

            # Should process the timestamps, but whatever
            minutes = list(range(0, 24*60, 10))

            txt = ''
            for i in range(len(timestamps)):
                line = '    {minute: %d' % minutes[i]
                for j,var in enumerate(variables):
                    line += ', %s: %s' % (var, values[j][i])
                line += '},\n'
                txt += line
            
            return '''
<div style="width: 800px;"><canvas id="graph"></canvas></div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
(async function() { const data = [
%s
];
  
new Chart(
document.getElementById('graph'),
{
    type: 'line',
    data: {
    labels: data.map(row => row.minute),
    datasets: [
        {
            label: 'soc',
            data: data.map(row => row.soc),
            tension: 0,
            yAxisID: 'y'
        },
        {
            label: 'chiller',
            data: data.map(row => row.chiller),
            tension: 0,
            yAxisID: 'y1'
        }
    ]
    },
    options: {
    scales: {
        y: {
            type: 'linear',
            position: 'left',
            ticks: { max: 1 }
        }, 
        y1: {
            type: 'linear',
            position: 'right',
        }
    }
  }
}
);
})();
</script>
''' % txt

        # GET request
        return '''
<form method="POST">
    <div><label>Prototype (temporarily unused): <select id="prototype" name="prototype">
        %s
        </select></label></div>
    <div><label>Climate Zone (temporarily unused): <select id="cz" name="cz">
        %s
        </select></label></div>
    <div><label>Vintage (temporarily unused): <select id="vintage" name="vintage">
        %s
        </select></label></div>
    <div><label>Charge Start Time: <input type="time" id="charge_start" name="charge_start" min="00:00" max="24:00" value="21:00" required /></label></div>
    <div><label>Charge End Time: <input type="time" id="charge_end" name="charge_end" min="00:00" max="24:00" value="07:00" required /></label></div>
    <div><label>Discharge Start Time: <input type="time" id="discharge_start" name="discharge_start" min="00:00" max="24:00" value="12:00" required /></label></div>
    <div><label>Discharge End Time: <input type="time" id="discharge_end" name="discharge_end" min="00:00" max="24:00" value="18:00" required /></label></div>
    <div><label>Charge Temperature: <input type="number" id="charge_temp" name="charge_temp" min="-10.0" max="10.0" value="-3.8" step="any" required /></label></div>
    <div><label>Number of Tanks: <input type="number" id="ntanks" name="ntanks" min="1" step="1" max="50" value="1" required /></label></div>
    <div><label>Trim Temperature: <input type="number" id="trim_temp" name="trim_temp" min="0.0" max="20.0" value="10.0" step="any" required /></label></div>
    <input type="submit" value="Submit">
</form>''' % (''.join(['<option value="LargeOffice">Large Office</option>']),
              ''.join(['<option value="%s">%s</option>' % (el,el) for el in stor4build.climate_zone_list]),
              ''.join(['<option value="%s">%s</option>' % (el,el) for el in stor4build.vintage_values]))

    @app.route('/icetank/size', methods=['GET', 'POST'])
    def icetank_size_route():
        # POST request
        if request.method == 'POST':
            # Get the inputs
            prototype = request.form.get('prototype') # Unused for now
            cz = 'ASHRAE 169-2006-%s' % request.form.get('cz') # Unused for now
            vintage = request.form.get('vintage') # Unused for now
            arguments = {
                "charge_start" : request.form.get('charge_start'),
                "charge_end" : request.form.get('charge_end'),
                "discharge_start" : request.form.get('discharge_start'),
                "discharge_end" : request.form.get('discharge_end'),
                "charge_temp" : request.form.get('charge_temp'),
                "peak_reduction" : float(request.form.get('peak_reduction')),
                "trim_temp": 10.0
            }
            
            added = [{
                        "measure_dir_name" : "add_output_variables",
                        "name" : "Add Output Variables",
                        "arguments" : {}
                    }]
            
            #osm = os.path.join(app.config['MODELS_DIR'], stor4build.prototype_lookup(prototype, cz, vintage))
            #epw = os.path.join(app.config['WEATHER_DIR'], stor4build.weather_lookup(cz))
            osm = os.path.abspath(os.path.join(weather_dir, 'LargeOffice.osm'))
            epw = os.path.abspath(os.path.join(weather_dir, 'USA_TN_Knoxville-McGhee.Tyson.AP.723260_TMY3.epw'))

            # Run the simulation
            with tempfile.TemporaryDirectory() as run_dir:
                runner = stor4build.Runner(osm, epw, openstudio_exe, run_dir, 'run', measures_dir)
                
                # Baseline first
                baseline = stor4build.Simulation('baseline', added_steps=added)
                osw = baseline.osw(osm, measures_dir, epw)
                runner.run(osw, 'baseline')
                
                # Baseline results are in this directory
                baseline_path = os.path.join(run_dir, 'baseline', 'run')
                
                icetank = stor4build.IceTank.size('sized_icetank', baseline_path, **arguments)
                osw = icetank.osw(osm, measures_dir, epw)
                runner.run(osw, icetank.tag())
            
                # Process the outputs
                csv_path = os.path.join(run_dir, icetank.tag(), 'run', 'eplusout.csv')
                if not os.path.exists(csv_path):
                    return '''
<h1>Simulation Failed</h1>
<h2>Failed to find eplusout.csv</h2>
<h2>Path: %s</h2>
''' % csv_path

                # Make a plot
                titles = {'soc': 'soc:PythonPlugin:OutputVariable [](TimeStep)',
                          'chiller': '90.1-2007 WATERCOOLED  CENTRIFUGAL CHILLER 1 374TONS 0.6KW/TON:Chiller Electricity Rate [W](TimeStep)'}

                variables = list(titles.keys())

                timestamps = []
                values = []
                for var in titles.keys():
                    values.append([])
                N = len(values)
                    
                with open(csv_path, 'r') as fp:
                    reader = csv.reader(fp)
                    header = next(reader)
                    indices = {}
                    for var in variables:
                        indices[var] = header.index(titles[var])

                    for line in reader:
                        timestamp = line[0]
                        if timestamp.startswith(' 07/15'):
                            timestamps.append(timestamp)
                            for i,var in enumerate(variables):
                                values[i].append(line[indices[var]])

            # Should process the timestamps, but whatever
            minutes = list(range(0, 24*60, 10))

            txt = ''
            for i in range(len(timestamps)):
                line = '    {minute: %d' % minutes[i]
                for j,var in enumerate(variables):
                    line += ', %s: %s' % (var, values[j][i])
                line += '},\n'
                txt += line
            
            return '''
<div style="width: 800px;"><canvas id="graph"></canvas></div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
(async function() { const data = [
%s
];
  
new Chart(
document.getElementById('graph'),
{
    type: 'line',
    data: {
    labels: data.map(row => row.minute),
    datasets: [
        {
            label: 'soc',
            data: data.map(row => row.soc),
            tension: 0,
            yAxisID: 'y'
        },
        {
            label: 'chiller',
            data: data.map(row => row.chiller),
            tension: 0,
            yAxisID: 'y1'
        }
    ]
    },
    options: {
    scales: {
        y: {
            type: 'linear',
            position: 'left',
            ticks: { max: 1 }
        }, 
        y1: {
            type: 'linear',
            position: 'right',
        }
    }
  }
}
);
})();
</script>
''' % txt

        # GET request
        return '''
<form method="POST">
    <div><label>Prototype (temporarily unused): <select id="prototype" name="prototype">
        %s
        </select></label></div>
    <div><label>Climate Zone (temporarily unused): <select id="cz" name="cz">
        %s
        </select></label></div>
    <div><label>Vintage (temporarily unused): <select id="vintage" name="vintage">
        %s
        </select></label></div>
    <div><label>Charge Start Time: <input type="time" id="charge_start" name="charge_start" min="00:00" max="24:00" value="21:00" required /></label></div>
    <div><label>Charge End Time: <input type="time" id="charge_end" name="charge_end" min="00:00" max="24:00" value="07:00" required /></label></div>
    <div><label>Discharge Start Time: <input type="time" id="discharge_start" name="discharge_start" min="00:00" max="24:00" value="12:00" required /></label></div>
    <div><label>Discharge End Time: <input type="time" id="discharge_end" name="discharge_end" min="00:00" max="24:00" value="18:00" required /></label></div>
    <div><label>Charge Temperature: <input type="number" id="charge_temp" name="charge_temp" min="-10.0" max="10.0" value="-3.8" step="any" required /></label></div>
    <div><label>Peak Reduction: <input type="number" id="peak_reduction" name="peak_reduction" min="0.0" max="100.0" value="15.0" step="any" required /></label></div>
    <input type="submit" value="Submit">
</form>''' % (''.join(['<option value="LargeOffice">Large Office</option>']),
              ''.join(['<option value="%s">%s</option>' % (el,el) for el in stor4build.climate_zone_list]),
              ''.join(['<option value="%s">%s</option>' % (el,el) for el in stor4build.vintage_values]))

    return app

@click.command()
@click.option('--openstudio', show_default=True, default='openstudio', help='OpenStudio CLI to use.')
#@click.option('--instance-path', show_default=False, default=None, help='Instance folder path.')
@click.option('-m', '--measures-dir', type=click.Path(exists=True), show_default=True, default='.',
              help='Directory containing measures.')
@click.option('-w', '--weather-dir', type=click.Path(exists=True), show_default=True, default='.',
              help='Directory containing weather files.')
def icetank(openstudio, measures_dir, weather_dir):
    """
    Run the prototype-based demo app.
    """
    config = {
        'OPENSTUDIO': openstudio,
        'MEASURES_DIR': measures_dir,
        'WEATHER_DIR': weather_dir
    }
    app = create_app(config=config)
    app.run(host='127.0.0.1', port=5000, debug=True)

@click.group(context_settings={'help_option_names': ['-h', '--help']}, invoke_without_command=False)
@click.version_option(version=__version__, prog_name='s4b-api')
@click.pass_context
def s4b_form(ctx: click.Context):
    pass

s4b_form.add_command(icetank)
