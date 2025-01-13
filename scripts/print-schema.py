from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
import json
from stor4build.schema import InputDataSchema

spec = APISpec(
    title="TESSBeD",
    version="0.2.0",
    openapi_version="3.0.2",
    info=dict(description="The TESSBeD web app for TES calculations"),
    plugins=[MarshmallowPlugin()],
)

spec.components.schema("InputData", schema=InputDataSchema)
print(json.dumps(spec.to_dict(), indent=2))

