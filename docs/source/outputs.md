# Outputs

Stor4Build produces simulation outputs derived from EnergyPlus and post-processed into CSV files for comparison between baseline and thermal energy storage cases.

Common output workflows include:

- Writing a combined CSV with `--output`.
- Comparing baseline and TES cooling energy.
- Reading sizing information from command output or generated reports.
- Plotting daily results with `stor4build process`.

The combined CSV may include a metadata header describing the Stor4Build version, building type, climate zone, vintage, storage technology, sizing information, and control arguments. Hourly data follows the header.

The exact output variables depend on the storage technology:

- `ThermalTank-Ice` and `ThermalTank-ChilledWater` workflows use thermal tank output measures.
- `PackagedIceStorage` workflows use DX coil and packaged ice storage output measures.

More detailed output documentation should eventually define each generated column, expected units, and which command/API workflow produces it.