# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Sustainable Energy, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
import json
from stor4build.schema import InputDataSchema
from stor4build import __version__ as s4b_version

spec = APISpec(
    title="stor4build",
    version=s4b_version,
    openapi_version="3.0.2",
    info=dict(description="The stor4build API for TES calculations"),
    plugins=[MarshmallowPlugin()],
)

spec.components.schema("InputData", schema=InputDataSchema)
print(json.dumps(spec.to_dict(), indent=2))

