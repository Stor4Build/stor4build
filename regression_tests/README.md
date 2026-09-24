# Regression testing

The regression suite has two adapters over one case inventory in `cases.json`:

- `cli_regression` runs the installed `stor4build` command through the package entry point. It is the generally portable regression tier, provided the canonical OpenStudio toolchain and the repository's model, weather, and measure inputs are available.
- `api_regression` sends the same kind of simulation request to a separately configured API and compares the response with the approved CLI golden for the same case. It is intended only for systems on which that service and its full simulation environment are available.

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

Large regression runs may be divided into deterministic, zero-based shards. Case patterns are applied first, and the remaining case IDs are sorted before round-robin assignment:

```console
hatch run test-cli --openstudio /path/to/openstudio --shard-count 6 --shard-index 0
```

Run every index from zero through `--shard-count - 1` to cover the complete selected inventory. The two shard options must be supplied together.

Run API regressions against an already-running service:

```console
hatch run test-api --api-url http://localhost:5000
```

`STOR4BUILD_API_URL` may be used instead of `--api-url`. Both regression scripts also accept `--case`, `--regression-timeout`, and `--regression-output`. Without `--regression-output`, generated files use pytest temporary directories. With it, each case is retained in its own directory for diagnosis. The harness never overwrites approved files in `regression_tests`.

## Generating candidate goldens

Golden generation runs exclusively through the CLI and requires the canonical OpenStudio version declared in `toolchain.json`. Generate all candidates into a new or empty directory outside `regression_tests`:

```console
hatch run generate-goldens --output ../stor4build-candidate-goldens --openstudio /path/to/openstudio
```

`STOR4BUILD_OPENSTUDIO` may be used instead of `--openstudio`. Select cases with one or more shell-style patterns and adjust the per-case timeout when needed:

```console
hatch run generate-goldens \
  --output ../stor4build-candidate-goldens \
  --case "*packaged_ice*" \
  --timeout 10800
```

The generator refuses to write anywhere inside `regression_tests` and refuses a non-empty candidate directory. It never modifies approved goldens. Each successful candidate is classified as `match`, `changed`, or `new`; execution failures are recorded as `failed`, and generation continues with the remaining cases. `generation.json` records the canonical and detected toolchain, host environment, original case arguments, per-case status, and comparison details. The command exits nonzero if any case fails to execute.

Review candidate files and `generation.json` before replacing approved goldens. Promotion is deliberately a separate manual action.

## Continuous integration

GitHub Actions runs the portable suite across every supported host-Python version. Six parallel CLI jobs run the regression inventory under Python 3.12, with one deterministic shard per job. The CLI jobs use the digest-pinned OpenStudio container declared in `toolchain.json`; changing the canonical OpenStudio release therefore requires updating the toolchain record rather than copying the container reference into the workflow.

## Failures

The GitHub Actions CLI regression jobs were investigated in September 2026 but remain deferred because all six shards fail in the Actions environment. Local CLI regression testing with the supported OpenStudio installation is known to work. The unsuccessful GitHub Actions work is recorded here so that it can be resumed without repeating the same investigation.

The workflow used the digest-pinned OpenStudio container from `toolchain.json` and divided the inventory into six deterministic shards. The following CI infrastructure issues were found and corrected before investigating the simulations themselves:

- `actions/setup-python` pip caching was removed from the container job because its pip wrapper referred to a host tool-cache path that did not exist inside the container.
- The checkout, Python setup, and artifact upload actions were updated to releases using the current GitHub Actions Node.js runtime.
- Failure artifacts were expanded to include generated CSV files, `run.log`, `stdout-energyplus`, `eplusout.err`, `eplusout.end`, and `out.osw`.

The remaining thermal-tank failure is a native EnergyPlus crash. Baseline simulations complete, but the sized thermal-tank simulations terminate with signal 11 immediately after EnergyPlus adds the Hatch environment and plugin directories to the embedded Python search path. EnergyPlus does not write a Python exception, an `eplusout.end` file, or a useful message to `stdout-energyplus`. Enabling `PYTHONFAULTHANDLER` and Python import timing produced no additional embedded-interpreter diagnostics. The following environment alignments did not resolve the crash:

- NumPy and SciPy were changed from the versions initially resolved in CI (NumPy 2.5.3 and SciPy 1.18.1) to the versions in the locally working environment (NumPy 2.3.5 and SciPy 1.16.3).
- The Actions host interpreter was changed from Python 3.12.14 to Python 3.12.2 to match the interpreter used to build the paired EnergyPlus executable.

The packaged-ice/DX-coil simulations in shard 0 complete successfully on Actions, but their Ubuntu results do not pass the point-by-point comparison against the checked-in goldens generated on Windows. The observed differences were:

- `RetailStandalone_5A_2016_packaged_ice_specified_schedule` had a maximum hourly absolute difference of 157,576 J and a maximum nonzero relative difference of 4.67%. It would pass with `rtol=0.05`. Its largest relative difference in an annual column total was 0.000282%.
- `MediumOffice_5A_2004_packaged_ice_defaults` had a maximum hourly absolute difference of 9,462,012 J, three zero/nonzero disagreements, 54 nonzero values differing by more than 5%, and a maximum nonzero relative difference of 53.3%. With the current comparison implementation it required approximately `rtol=0.05` and `atol=9.5e6` J to pass. Its largest relative difference in an annual column total was only 0.00218%.

These results suggest platform-dependent changes in the timing or allocation of hourly loads rather than material differences in annual energy totals. The global comparison tolerances were not relaxed because the tolerance required by the MediumOffice case could conceal meaningful regressions. If CI regression testing is revisited, preferred approaches are to generate and approve goldens on the declared canonical platform or to design a separate cross-platform comparison combining hourly checks with strict period-integrated totals.

## Comparisons

Generated CSV output must have the expected metadata, columns in the same order, timestamps, row count, and finite numeric data. The historical package version recorded in an approved golden is informational; newly generated output must report the current package version. Numeric values use `rtol=1e-6` and `atol=1e-6`.
