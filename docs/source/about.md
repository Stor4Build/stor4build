# About stor4build

## Purpose

The stor4build package helps evaluate building-integrated thermal energy storage systems by coordinating EnergyPlus and OpenStudio simulations around repeatable storage workflows. It is designed to run baseline building models, add storage technologies, size storage for target scenarios, and compare resulting energy and demand impacts.

The package focuses on making thermal energy storage studies easier to create and reproduce. Inputs are represented with structured JSON data, simulations are run through standard OpenStudio and EnergyPlus tooling, and outputs are collected into CSV files for post-processing and comparison.

## Intended Users

The package is intended for researchers, engineers, analysts, and software developers studying thermal energy storage in commercial buildings. Typical users may want to compare storage technologies across building prototypes, climate zones, vintages, utility schedules, or control strategies.

The command line interface supports scripted studies and batch workflows. The Python package supports deeper integration into analysis pipelines. The web API supports service-oriented workflows where a client submits scenario data and receives simulation results.

## What Is Simulated

stor4build currently supports building energy simulations that compare a baseline model against a model with thermal energy storage. Supported storage workflows include thermal tank storage and packaged ice storage, with sizing and control options exposed through the CLI and API.

The included prototype models, weather files, measures, controls, schemas, and regression data provide starting points for repeatable studies. The exact supported building types, vintages, climate zones, and storage technologies are documented in the project reference material and may expand over time.

## Relationship to EnergyPlus and OpenStudio

The package does not replace EnergyPlus or OpenStudio nor does it provide a comprehensive interface to either package. It uses them as the simulation engine and workflow tool underneath the Python package. stor4build prepares workflows, applies measures, runs simulations, repairs or combines output files when needed, and exposes higher-level interfaces for common TES study patterns.

This means a working OpenStudio and EnergyPlus installation is still required for simulation workflows. The package adds structure around those tools so users can run comparable cases without manually assembling every workflow step.

## Current Scope and Limitations

stor4build is currently focused on cooling-oriented thermal energy storage studies using supported OpenStudio prototype buildings and selected TES technologies. Results depend on the assumptions embedded in the source models, measures, weather files, storage representations, and control strategies.

The Python API and web API are expected to evolve. User-facing documentation should therefore emphasize stable workflows, input data, CLI behavior, examples, supported scenarios, and output interpretation, while generated API reference pages track the implementation as it changes.