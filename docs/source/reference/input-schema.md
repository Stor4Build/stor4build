# Input Schema Reference

The checked-in schema is generated from the Marshmallow schema definitions used by the current API implementation.

Regenerate it with:

```console
hatch run python scripts/print-schema.py > schema/stor4build.json
```

```{literalinclude} ../../../schema/stor4build.json
:language: json
```