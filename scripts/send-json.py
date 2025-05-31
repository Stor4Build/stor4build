# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import httpx
import time
import sys
import os
import json

inputs = {
    "baseline": {
        "blendedElectricityRate": 0.12,
        "blendedNaturalGasRate": 1,
        "building": "LargeOffice",
        "capitalCost": 20000,
        "climate": "CL_4A",
        "compressor": "SingleSpeed",
        "coolingCapacity": 30000,
        "coolingSetback": 80,
        "coolingSetpoint": 74,
        "createdAt": "2024-08-15T12:30:28.035Z",
        "economizer": "NoEconomizer",
        "eer": 10,
        "fan": "ConstantSpeed",
        "heating": "HeatPump",
        "heatingCop": 1,
        "heatingSetback": 65,
        "heatingSetpoint": 71,
        "id": "clzv9djuq000112dnird6fhyi",
        "maximumLimitDryBulb": 70,
        "minOaFraction": 0.1,
        "numberOfSpeeds": 1,
        "orientation": "South",
        "oversizeFactor": 1,
        "realDiscountRate": 5,
        "rtuLifetime": 15,
        "updatedAt": "2024-08-15T12:31:45.771Z",
        "userId": "2",
        "vintage": 2005,
        "window": "Medium",
        "zone": "Office",
        "__typename": "Input"
    },
    "createdAt": "2024-08-15T12:30:28.035Z",
    "demand": {
        "costs": [
            {
                "createdAt": "2024-08-15T12:30:28.035Z",
                "id": "clzv9djur000312dnwzk0vz67",
                "period": 1,
                "rate": 7,
                "tier": 1,
                "unit": "$/kW",
                "updatedAt": "2024-08-15T12:32:07.645Z",
                "userId": "2",
                "__typename": "Cost"
            },
            {
                "createdAt": "2024-08-15T12:30:28.035Z",
                "id": "clzv9djur000412dndlyyxf5n",
                "period": 2,
                "rate": 9.9,
                "tier": 1,
                "unit": "$/kW",
                "updatedAt": "2024-08-15T12:32:18.376Z",
                "userId": "2",
                "__typename": "Cost"
            },
            {
                "createdAt": "2024-08-15T12:30:28.035Z",
                "id": "clzv9djur000512dni9wy8evy",
                "period": 3,
                "rate": 50.1234,
                "tier": 1,
                "unit": "$/kW",
                "updatedAt": "2024-08-15T12:32:23.647Z",
                "userId": "2",
                "__typename": "Cost"
            }
        ],
        "createdAt": "2024-08-15T12:30:28.035Z",
        "schedule": {
            "months": [
                {
                    "unit": "hour",
                    "month": "All",
                    "periods": [
                        2,
                        2,
                        2,
                        2,
                        2,
                        1,
                        1,
                        1,
                        1,
                        1,
                        1,
                        1,
                        1,
                        1,
                        1,
                        1,
                        3,
                        3,
                        3,
                        3,
                        3,
                        3,
                        3,
                        3
                    ]
                }
            ]
        },
        "palette": "Violet",
        "id": "clzv9djur000212dnbnuw0uu2",
        "updatedAt": "2024-08-15T12:32:40.207Z",
        "userId": "2",
        "__typename": "Charge"
    },
    "energy": {
        "costs": [
            {
                "createdAt": "2024-08-15T12:30:28.035Z",
                "id": "clzv9djur000712dne4dr5yjq",
                "period": 1,
                "rate": 0.123,
                "tier": 1,
                "unit": "$/kWh",
                "updatedAt": "2024-08-15T12:30:48.705Z",
                "userId": "2",
                "__typename": "Cost"
            },
            {
                "createdAt": "2024-08-15T12:30:28.035Z",
                "id": "clzv9djur000812dnpw1z0amg",
                "period": 2,
                "rate": 0.9,
                "tier": 1,
                "unit": "$/kWh",
                "updatedAt": "2024-08-15T12:30:51.491Z",
                "userId": "2",
                "__typename": "Cost"
            },
            {
                "createdAt": "2024-08-15T12:30:28.035Z",
                "id": "clzv9djur000912dn4i2aquay",
                "period": 3,
                "rate": 3,
                "tier": 1,
                "unit": "$/kWh",
                "updatedAt": "2024-08-15T12:31:16.228Z",
                "userId": "2",
                "__typename": "Cost"
            }
        ],
        "createdAt": "2024-08-15T12:30:28.035Z",
        "schedule": {
            "months": [
                {
                    "unit": "hour",
                    "month": "All",
                    "periods": [
                        1,
                        1,
                        1,
                        1,
                        1,
                        1,
                        2,
                        2,
                        2,
                        2,
                        2,
                        3,
                        3,
                        3,
                        3,
                        3,
                        3,
                        3,
                        2,
                        2,
                        1,
                        1,
                        1,
                        1
                    ]
                }
            ]
        },
        "palette": "Vermilion",
        "id": "clzv9djur000612dneo48hv35",
        "updatedAt": "2024-08-15T12:31:30.351Z",
        "userId": "2",
        "__typename": "Charge"
    },
    "error": '',
    "id": "clzv9djuq000012dn0rtrbd67",
    "label": "",
    "metadata": {
    },
    "result": '',
    "schedule": {
        "createdAt": "2024-08-15T12:30:28.035Z",
        "fridayEnd": 18,
        "fridayStart": 6,
        "id": "clzv9djur000a12dn0o22q2b7",
        "label": '',
        "mondayEnd": 18,
        "mondayStart": 6,
        "saturdayEnd": 18,
        "saturdayStart": 6,
        "sundayEnd": 18,
        "sundayStart": 6,
        "thursdayEnd": 18,
        "thursdayStart": 6,
        "tuesdayEnd": 18,
        "tuesdayStart": 6,
        "updatedAt": "2024-08-15T12:30:28.035Z",
        "userId": "2",
        "wednesdayEnd": 18,
        "wednesdayStart": 6,
        "__typename": "Schedule"
    },
    "stage": "Created",
    "storage": {
        "capacity": 100,
        "createdAt": "2024-08-15T12:30:28.035Z",
        "id": "clzv9djur000b12dnp08vaxqs",
        "updatedAt": "2024-08-15T12:34:04.114Z",
        "userId": "2",
        "__typename": "Storage"
    },
    "updatedAt": "2024-08-15T12:30:28.035Z",
    "upgrade": {
        "blendedElectricityRate": 0.12,
        "blendedNaturalGasRate": 1,
        "building": "LargeOffice",
        "capitalCost": 20000,
        "climate": "CL_4A",
        "compressor": "SingleSpeed",
        "coolingCapacity": 30000,
        "coolingSetback": 80,
        "coolingSetpoint": 74,
        "createdAt": "2024-08-15T12:30:28.035Z",
        "economizer": "NoEconomizer",
        "eer": 10,
        "fan": "ConstantSpeed",
        "heating": "HeatPump",
        "heatingCop": 1,
        "heatingSetback": 65,
        "heatingSetpoint": 71,
        "id": "clzv9djus000c12dnci7q29i4",
        "maximumLimitDryBulb": 70,
        "minOaFraction": 0.1,
        "numberOfSpeeds": 1,
        "orientation": "South",
        "oversizeFactor": 1,
        "realDiscountRate": 5,
        "rtuLifetime": 15,
        "updatedAt": "2024-08-15T12:31:45.774Z",
        "userId": "2",
        "vintage": 2005,
        "window": "Medium",
        "zone": "Office",
        "__typename": "Input"
    },
    "userId": "2",
    "__typename": "Calculation"
}

if len(sys.argv) > 1:
    if os.path.exists(sys.argv[1]):
        with open(sys.argv[1], 'r') as fp:
            inputs =json.load(fp) #['request']['body']
    
start = time.time()
r = httpx.post('http://127.0.0.1:5000/simulate', json=inputs, timeout=None)
#r = httpx.post('http://127.0.0.1:5000/simple', json={'technology': {'type': 'icetank'}}, timeout=None)
delta = time.time() - start

print('Done! (%s seconds)' % delta)
print(r.status_code, r.text)

with open('result.csv', 'w') as fp:
    fp.write(r.text)


