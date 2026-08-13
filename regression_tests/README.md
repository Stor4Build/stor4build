# Regression testing

The regression suite has two adapters over one case inventory in `cases.json`:

- `cli_regression` runs the installed `stor4build` command through the package entry point. It is the generally portable regression tier, provided the canonical OpenStudio toolchain and the repository's model, weather, and measure inputs are available.
- `api_regression` sends the same kind of simulation request to a separately configured API. It is intended only for systems on which that service and its full simulation environment are available.

Neither tier runs as part of the ordinary test suite unless it is explicitly enabled. The manifest and harness unit tests always run.

## Canonical simulation toolchain

[`toolchain.json`](toolchain.json) is the machine-readable authority for the OpenStudio version and build, its paired EnergyPlus and embedded Python versions, and the platform used to approve regression outputs. Read the current values from that file rather than copying them into other documentation.

The package's host-Python test matrix is a separate compatibility concern and should continue to cover all supported Python versions. It must include the Python version embedded in the canonical EnergyPlus release, but should not be limited to that version.

Install the version declared in `toolchain.json` from the [official OpenStudio releases](https://github.com/NatLabRockies/OpenStudio/releases). Use the package matching the declared canonical platform when producing approved goldens. The official [`nrel/openstudio` container tags](https://hub.docker.com/r/nrel/openstudio/tags) provide another reproducible option. Installers for other supported platforms may be used for exploratory and local runs.

Confirm the selected executable before running a simulation:

```console
openstudio openstudio_version
```

The CLI regression harness performs this OpenStudio check automatically. It does not separately test the EnergyPlus or embedded Python versions: the supported EnergyPlus release and its embedded Python are determined by the selected OpenStudio release. Those values are recorded as toolchain provenance rather than independent runtime variables. The harness rejects an OpenStudio semantic-version mismatch by default; the recorded build hash and platform identify the environment in which canonical goldens should be produced. `--allow-toolchain-mismatch` permits an exploratory run, but its output must not be approved as a canonical golden.

## Running the tiers

Run the portable unit, manifest, and harness checks:

```console
hatch run test
```

Run all currently runnable CLI regressions:

```console
hatch run test-cli --openstudio /path/to/openstudio
```

`STOR4BUILD_OPENSTUDIO` may be used instead of `--openstudio`. Select one or more cases with a shell-style name pattern:

```console
hatch run test-cli --openstudio /path/to/openstudio --case "*packaged_ice*"
```

Run API regressions against an already-running service:

```console
hatch run test-api --api-url http://localhost:5000
```

`STOR4BUILD_API_URL` may be used instead of `--api-url`. Both regression scripts also accept `--case`, `--regression-timeout`, and `--regression-output`. Without `--regression-output`, generated files use pytest temporary directories. With it, each case is retained in its own directory for diagnosis. The harness never overwrites approved files in `regression_tests`.

## Comparisons

Generated CSV output must have the expected metadata, columns in the same order, timestamps, row count, and finite numeric data. The historical package version recorded in an approved golden is informational; newly generated output must report the current package version. Numeric values use `rtol=1e-6` and `atol=1e-6`.
