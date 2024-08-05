import httpx
import time

inputs = {'type': 'LargeOffice',
          'cz': '4A',
          'vintage': '2007',
          'technology': {'type': 'icetank',
                         'num_tanks': 2}}

start = time.time()
r = httpx.post('http://127.0.0.1:5000/simple', json=inputs, timeout=None)
delta = time.time() - start

print('Done! (%s seconds)' % delta)
print(r.status_code, r.text)

