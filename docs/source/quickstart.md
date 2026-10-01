# Quickstart

The quickest way to use Stor4Build is through the CLI. The package currently includes commands for running baseline OpenStudio workflows, adding thermal tank systems, sizing ice tank systems, running packaged ice storage cases, and plotting hourly output CSV files.

Show the available commands:

```console
stor4build --help
```

Show help for a specific command:

```console
stor4build size-icetank --help
```

A typical thermal tank sizing workflow needs an OpenStudio model, an EnergyPlus weather file, and the repository's OpenStudio measures:

```console
stor4build size-icetank models/LargeOffice_5A_pre1980.osm weather/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw --measures-dir measures --output output.csv
```

The exact model, weather file, storage technology, and control settings should match the scenario being studied. See the CLI reference for the full command surface.