# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import contextlib
import datetime
import os
import tempfile

import stor4build

from .settings import APISettings
from ..schema import InputData, SimulationRequest


class MissingConfig(Exception):
    pass


class APIError(Exception):
    def __init__(self, status_code: int, error: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.error = error
        self.message = message


@contextlib.contextmanager
def managed_directory(run_dir):
    if run_dir is None:
        tmp = tempfile.TemporaryDirectory()
        try:
            yield tmp.name
        finally:
            tmp.cleanup()
    else:
        yield run_dir


def build_resultsdb(settings: APISettings):
    return stor4build.ResultsDatabase(
        database=settings.timescale_db,
        user=settings.timescale_username,
        password=settings.timescale_password,
        host=settings.timescale_host,
        port=settings.timescale_port,
        cases_table="baseline_cases",
        results_table="baseline_results",
        weather_table="weather",
        verbose=True,
    )


def _model_measure(name, measure_dir_name, arguments=None):
    return stor4build.ModelMeasure(name, measure_dir_name, arguments or {})


def _reporting_measure(name, measure_dir_name, arguments=None):
    return stor4build.ReportingMeasure(name, measure_dir_name, arguments or {})


def run_simulation_request(request: SimulationRequest, settings: APISettings) -> str:
    return run_simulation(request.to_domain(), settings, detailed_header=request.detailed_header)


def run_simulation(inputs: InputData, settings: APISettings, detailed_header: bool = True) -> str:
    measures_dir = settings.resolved_measures_directory
    if not os.path.exists(measures_dir):
        raise MissingConfig(f'Cannot find measures directory "{measures_dir}", cannot continue.')

    oldest_acceptable = None
    if settings.oldest_acceptable is not None:
        oldest_acceptable = datetime.datetime.fromisoformat(settings.oldest_acceptable)

    openstudio_exe = settings.openstudio
    debug_run_dir = settings.resolved_run_directory
    noisy = settings.noisy
    resultsdb = build_resultsdb(settings)

    building_type = inputs.baseline.type
    climate_string = inputs.baseline.climate
    climate_zone = f"ASHRAE 169-2006-{climate_string}"
    vintage_to_use = stor4build.map_to_vintage(inputs.baseline.vintage)

    if not stor4build.validate_template(building_type, vintage_to_use):
        raise APIError(
            400,
            "Bad request",
            f'The requested vintage ({inputs.baseline.vintage}) is not supported for "{building_type}" buildings',
        )

    argument_keys = ["charge_start", "charge_end", "discharge_start", "discharge_end"]
    if inputs.energy is not None:
        energy_sch = inputs.energy.schedule.months["All"].periods
        if len(energy_sch) != 24:
            raise APIError(400, "Bad request", "Energy cost schedule is not the correct length in input.")
        arguments = {key: value for key, value in zip(argument_keys, stor4build.process_energy_schedule(energy_sch))}
    else:
        arguments = {}

    baseline_post = []
    technology_post = []
    technology_object_factory = None

    if inputs.storage.charge_interval is not None:
        arguments["charge_start"] = "%02d:00" % inputs.storage.charge_interval.begin.hour
        arguments["charge_end"] = "%02d:00" % inputs.storage.charge_interval.end.hour
    if inputs.storage.discharge_interval is not None:
        arguments["discharge_start"] = "%02d:00" % inputs.storage.discharge_interval.begin.hour
        arguments["discharge_end"] = "%02d:00" % inputs.storage.discharge_interval.end.hour

    if inputs.storage.type in ["ThermalTank-Ice", "ThermalTank-ChilledWater"]:
        if building_type not in stor4build.thermaltank_supported:
            raise APIError(400, "Bad request", f'Building type "{building_type}" is not supported for this TES type.')

        arguments["peak_reduction"] = inputs.storage.capacity
        arguments["store_ice"] = {"ThermalTank-Ice": True, "ThermalTank-ChilledWater": False}[inputs.storage.type]
        arguments["size_fraction"] = inputs.storage.size_fraction
        arguments["storage_medium"] = inputs.storage.medium

        technology_object_factory = stor4build.IceTank.size
        baseline_post = [
            _model_measure("Add ThermalTank Outputs", "add_thermaltank_outputs"),
            _model_measure("Run Cooling Season Only", "run_cooling_season_only"),
        ]
        technology_post = [
            _model_measure("Add ThermalTank Outputs", "add_thermaltank_outputs", {"baseline": False}),
            _model_measure("Run Cooling Season Only", "run_cooling_season_only"),
        ]
    elif inputs.storage.type == "PackagedIceStorage":
        if building_type not in stor4build.dxcoil_supported:
            raise APIError(400, "Bad request", f'Building type "{building_type}" is not supported for this TES type.')

        technology_object_factory = stor4build.DxCoil.size
        baseline_post = [
            _model_measure("Add DX Coil Outputs", "add_dx_coil_outputs", {"baseline": True}),
            _model_measure("Run Cooling Season Only", "run_cooling_season_only"),
        ]
        technology_post = [
            _model_measure("Add DX Coil Outputs", "add_dx_coil_outputs", {"baseline": False}),
            _model_measure("Run Cooling Season Only", "run_cooling_season_only"),
            _reporting_measure("Get DX Coil Sizes", "get_dx_coil_sizes"),
        ]
    else:
        raise APIError(400, "UnknownTechnologyType", f'Technology type "{inputs.storage.type}" is unknown.')

    response_txt = ""
    with managed_directory(debug_run_dir) as run_dir:
        run_path = os.path.abspath(run_dir)

        epw = os.path.join(run_dir, "weather.epw")
        epw_file = resultsdb.get_weather(epw, climate_string)
        if epw_file is None:
            raise APIError(500, "UnknownWeather", f'Failed to find weather file for climate zone "{climate_string}".')

        osm = os.path.join(run_dir, "baseline.osm")
        building_id = resultsdb.get_model(
            osm,
            building_type=building_type,
            climate_zone=climate_string,
            vintage=vintage_to_use,
        )
        if building_id is None:
            raise APIError(
                400,
                "UnknownBaseline",
                f"Baseline for inputs {building_type}, {climate_string}, {vintage_to_use} is unknown.",
            )

        baseline_path = os.path.join(run_dir, "baseline", "run")
        baseline_csv = os.path.join(baseline_path, "eplusout.csv")
        found_results = False
        if settings.cache_baseline:
            found_results = resultsdb.get_results(
                building_id,
                output_path=baseline_path,
                filename="eplusout.csv",
                oldest_acceptable=oldest_acceptable,
            )
        if not found_results:
            baseline = stor4build.Simulation("baseline", post_steps=baseline_post)
            osw = baseline.osw(osm, measures_dir, epw)
            stor4build.run_workflow(openstudio_exe, os.path.join(run_path, baseline.tag()), osw, measures_only=False)
            stor4build.fix_csv(baseline_csv, verbose=noisy)
            if settings.cache_baseline and settings.store_missing_results:
                resultsdb.set_results(building_id, baseline_csv)

        technology_object = technology_object_factory("tes", baseline_path, post_steps=technology_post, **arguments)
        osw = technology_object.osw(osm, measures_dir, epw)
        stor4build.run_workflow(openstudio_exe, os.path.join(run_path, technology_object.tag()), osw, measures_only=False)

        if detailed_header:
            response_txt += f"version,{stor4build.__version__}\n"
            response_txt += f'building_type,"{building_type}"\n'
            response_txt += f'climate_zone,"{climate_zone}"\n'
            response_txt += f'vintage,"{vintage_to_use}"\n'
            response_txt += f'storage,"{inputs.storage.type}"\n'
            if inputs.storage.type == "PackagedIceStorage":
                sizing_report_path = os.path.join(run_dir, "tes", "reports", "get_dx_coil_sizes_report.csv")
                with open(sizing_report_path, "r") as fp:
                    names = next(fp).strip()
                    values = next(fp).strip()
                response_txt += "packaged_ice_object_names," + names + "\n"
                response_txt += "packaged_ice_capacities," + values + "\n"
                replacement_report_path = os.path.join(run_dir, "tes", "reports", "add_packaged_ice_storage_report.txt")
                with open(replacement_report_path, "r") as fp:
                    lines = fp.read().splitlines()
                names_upper = [element.strip().upper() for element in names.split(",")]
                if len(lines) % 2 == 0:
                    lookup = {}
                    iterator = iter([line.strip() for line in lines])
                    for original, new in zip(iterator, iterator):
                        lookup[new.upper()] = original.upper()
                    replaced = [lookup[element] for element in names_upper]
                    response_txt += "replaced_object_names," + ",".join(replaced) + "\n"
                else:
                    response_txt += "Unable to determine new-to-old object mapping"
            else:
                response_txt += f'storage_medium,"{inputs.storage.medium}"\n'
            for key, value in technology_object.sizing.items():
                response_txt += '%s,"%s"\n' % (key, str(value))
            for key, value in arguments.items():
                response_txt += 'argument: %s,"%s"\n' % (key, str(value))

        tech_csv = os.path.join(run_dir, "tes", "run", "eplusout.csv")
        stor4build.fix_csv(tech_csv, verbose=noisy)
        if inputs.demand is not None:
            rates = [cost.rate for cost in inputs.demand.costs.values()]
            rates.sort()
            response_txt += "demand rates," + ",".join([str(element) for element in rates]) + "\n"
        response_txt += stor4build.combine_single_frequency_csv(
            baseline_csv,
            tech_csv,
            "Hourly",
            energy_data=inputs.energy,
            demand_data=inputs.demand,
        )

    return response_txt
