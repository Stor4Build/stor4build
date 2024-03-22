import csv

page = '''<!doctype html>
<html lang="en">
  <head>
    <title>Chart.js example</title>
  </head>
  <body>
    <div style="width: 800px;"><canvas id="graph1"></canvas></div>
    <div style="width: 800px;"><canvas id="graph2"></canvas></div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
(async function() {
  const data = [
%s
  ];

  new Chart(
    document.getElementById('graph1'),
    {
      type: 'line',
      data: {
        labels: data.map(row => row.minute),
        datasets: [
          {
            label: 'soc',
            data: data.map(row => row.soc),
            tension: 0,
            yAxisID: 'A'
          },
          {
            label: 'chiller',
            data: data.map(row => row.chiller),
            tension: 0,
            yAxisID: 'B'
          }
        ]
      },
      options: {
        scales: {
          yAxes: [{
            id: 'A',
            type: 'linear',
            position: 'left',
            ticks: { max: 1 }
          }, {
            id: 'B',
            type: 'linear',
            position: 'right',
          }]
        }
      }
    }
  );

  new Chart(
    document.getElementById('graph2'),
    {
      type: 'line',
      data: {
        labels: data.map(row => row.minute),
        datasets: [
          {
            label: 'soc',
            data: data.map(row => row.soc),
            tension: 0,
            yAxisID: 'A'
          },
          {
            label: 'chiller',
            data: data.map(row => row.chiller),
            tension: 0,
            yAxisID: 'B'
          }
        ]
      },
      options: {
        scales: {
          yAxes: [{
            id: 'A',
            type: 'linear',
            position: 'left',
            ticks: { max: 1 }
          }, {
            id: 'B',
            type: 'linear',
            position: 'right',
          }]
        }
      }
    }
  );
})();
    </script>
  </body>
</html>'''


file = 'tank.csv'

titles = {'soc': 'soc:PythonPlugin:OutputVariable [](TimeStep)',
          'chiller': '90.1-2007 WATERCOOLED  CENTRIFUGAL CHILLER 1 374TONS 0.6KW/TON:Chiller Electricity Rate [W](TimeStep)'}

variables = list(titles.keys())

timestamps = []
values = []
for var in titles.keys():
    values.append([])
N = len(values)
        
with open(file, 'r') as fp:
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

with open('out.html', 'w') as fp:
    fp.write(page % txt)

    
    
