# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import json

from stor4build.api import create_app

app = create_app()
print(json.dumps(app.openapi(), indent=2))
