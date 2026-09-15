# Examples

The repository includes example inputs, demo controls, and sample output files that are useful starting points for new studies.

## Included Materials

- `examples/examples.json` contains sample web/API input payloads.
- `resources/` contains minimal and default JSON inputs.
- `docs/simple-control-demo.md` describes a simple EnergyPlus Python plugin control demonstration.
- `docs/demo-ambient-soc.ipynb` explores a state-of-charge control demonstration in notebook form.

## Example Categories

Future examples should be organized around user tasks rather than source files:

- Running a baseline model.
- Sizing a thermal tank for a target peak reduction.
- Running packaged ice storage.
- Providing utility energy and demand schedules.
- Comparing baseline and TES hourly outputs.
- Implementing a custom control measure or Python plugin.

Keeping examples task-oriented will make them survive API refactors more easily than examples that mirror internal class names.