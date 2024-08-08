import httpx
import time

inputs = {'type': 'LargeOffice',
          'cz': '4A',
          'vintage': '2007',
          'technology': {'type': 'icetank',
                         'charge_start': '21:00',
                         'charge_end': '07:00',
                         'discharge_start': '12:00',
                         'discharge_end': '18:00',
                         'peak_reduction': 100.0}}

start = time.time()
r = httpx.post('http://127.0.0.1:5000/simulate', json=inputs, timeout=None)
delta = time.time() - start

print('Done! (%s seconds)' % delta)
print(r.status_code, r.text)

