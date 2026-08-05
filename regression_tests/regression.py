# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import csv
import io
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import httpx
import numpy as np
import pandas as pd

from stor4build import __version__


REGRESSION_DIR = Path(__file__).resolve().parent
REPO_DIR = REGRESSION_DIR.parent
CASES_FILE = REGRESSION_DIR / "cases.json"
DEFAULT_RTOL = 1.0e-6
DEFAULT_ATOL = 1.0e-6


@dataclass(frozen=True)
class RegressionCase:
    name: str
    adapter: str
    config: dict[str, Any]
    expected: Path
    enabled: bool = True
    reason: str | None = None


def load_manifest() -> dict[str, dict[str, Any]]:
    with CASES_FILE.open(encoding="utf-8") as fp:
        manifest = json.load(fp)
    if not isinstance(manifest, dict) or not manifest:
        raise ValueError(f"{CASES_FILE} must contain a non-empty JSON object")
    return manifest


def _cli_expected(config: dict[str, Any], name: str) -> Path:
    arguments = config.get("arguments")
    if not isinstance(arguments, list) or not all(isinstance(arg, str) for arg in arguments):
        raise ValueError(f'{name}.cli.arguments must be a list of strings')
    try:
        output_index = arguments.index("-o") + 1
        output_name = arguments[output_index]
    except (ValueError, IndexError) as exc:
        raise ValueError(f'{name}.cli.arguments must contain "-o" and an output filename') from exc
    return REGRESSION_DIR / output_name


def iter_cases(adapter: str) -> Iterable[RegressionCase]:
    if adapter not in {"cli", "api"}:
        raise ValueError(f"Unknown regression adapter: {adapter}")
    for name, definitions in load_manifest().items():
        if adapter not in definitions:
            continue
        config = definitions[adapter]
        if not isinstance(config, dict):
            raise ValueError(f"{name}.{adapter} must be a JSON object")
        enabled = config.get("enabled", True)
        reason = config.get("reason")
        if adapter == "cli":
            expected = _cli_expected(config, name)
        else:
            expected = REGRESSION_DIR / f"{name}_api.csv"
        yield RegressionCase(name, adapter, config, expected, enabled, reason)


def api_request(case: RegressionCase) -> dict[str, Any]:
    request = case.config.get("request")
    if not isinstance(request, dict):
        raise ValueError(f"{case.name}.api request must be a JSON object")
    return request


def validate_manifest() -> list[str]:
    problems: list[str] = []
    manifest = load_manifest()
    allowed_adapters = {"cli", "api"}
    for name, definitions in manifest.items():
        if not isinstance(name, str) or not name:
            problems.append("Every regression case must have a non-empty string ID")
            continue
        if not isinstance(definitions, dict):
            problems.append(f"{name} must be a JSON object")
            continue
        unknown = set(definitions) - allowed_adapters
        if unknown:
            problems.append(f"{name} has unknown adapters: {sorted(unknown)}")
        if not set(definitions) & allowed_adapters:
            problems.append(f"{name} does not define a CLI or API regression")

        cli = definitions.get("cli")
        if cli is not None:
            try:
                expected = _cli_expected(cli, name)
                arguments = cli["arguments"]
                if any(arg.startswith("-") and " " in arg for arg in arguments):
                    problems.append(f"{name}.cli contains a combined option/value instead of separate tokens")
                for argument in arguments:
                    if argument.endswith((".osm", ".epw")) and not (REPO_DIR / argument).is_file():
                        problems.append(f"{name}.cli input does not exist: {argument}")
                if expected.parent != REGRESSION_DIR:
                    problems.append(f"{name}.cli expected output must be in regression_tests")
            except (KeyError, TypeError, ValueError) as exc:
                problems.append(str(exc))

        api = definitions.get("api")
        if api is not None:
            if not isinstance(api, dict):
                problems.append(f"{name}.api must be a JSON object")
            else:
                if api.get("enabled", True) is False and not api.get("reason"):
                    problems.append(f"{name}.api is disabled without a reason")
                try:
                    request = api.get("request")
                    if not isinstance(request, dict):
                        problems.append(f"{name}.api request must be a JSON object")
                        continue
                    if not isinstance(request.get("storage"), dict):
                        problems.append(f"{name}.api request is missing storage")
                    if not isinstance(request.get("baseline"), dict):
                        problems.append(f"{name}.api request is missing baseline")
                except AttributeError:
                    problems.append(f"{name}.api request must be a JSON object")
    return problems


def select_case(case: RegressionCase, patterns: list[str]) -> bool:
    if not patterns:
        return True
    from fnmatch import fnmatch

    return any(fnmatch(case.name, pattern) for pattern in patterns)


def prepare_cli_arguments(case: RegressionCase, output: Path, run_dir: Path, openstudio: str) -> list[str]:
    arguments = list(case.config["arguments"])
    output_index = arguments.index("-o") + 1
    arguments[output_index] = str(output)
    arguments[1:1] = ["--openstudio", openstudio, "-r", str(run_dir)]
    return arguments


def run_cli_case(
    case: RegressionCase,
    output: Path,
    run_dir: Path,
    openstudio: str,
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    arguments = prepare_cli_arguments(case, output, run_dir, openstudio)
    command = [sys.executable, "-m", "stor4build", *arguments]
    result = subprocess.run(
        command,
        cwd=REPO_DIR,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode:
        raise AssertionError(
            f"CLI regression {case.name} failed with exit code {result.returncode}\n"
            f"Command: {command!r}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    if not output.is_file():
        raise AssertionError(f"CLI regression {case.name} did not create {output}")
    return result


def run_api_case(case: RegressionCase, output: Path, api_url: str, timeout: float) -> httpx.Response:
    output.parent.mkdir(parents=True, exist_ok=True)
    url = api_url.rstrip("/") + "/simulate"
    response = httpx.post(url, json=api_request(case), timeout=timeout)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "text/csv" not in content_type:
        raise AssertionError(f"API regression {case.name} returned content type {content_type!r}, not text/csv")
    output.write_text(response.text, encoding="utf-8")
    return response


def _read_output(path: Path) -> tuple[dict[str, list[str]], pd.DataFrame]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    header_index = next((index for index, line in enumerate(lines) if line.lstrip().startswith("Date/Time,")), None)
    if header_index is None:
        raise AssertionError(f"{path} does not contain a Date/Time CSV header")

    metadata: dict[str, list[str]] = {}
    for row in csv.reader(lines[:header_index]):
        if row:
            metadata[row[0].strip()] = [value.strip() for value in row[1:]]

    data_text = "\n".join(lines[header_index:])
    frame = pd.read_csv(io.StringIO(data_text), skipinitialspace=True)
    frame.columns = [str(column).strip() for column in frame.columns]
    return metadata, frame


def _as_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _compare_metadata(
    expected: dict[str, list[str]],
    actual: dict[str, list[str]],
    rtol: float,
    atol: float,
) -> None:
    expected_keys = set(expected) - {"version"}
    actual_keys = set(actual) - {"version"}
    if expected_keys != actual_keys:
        raise AssertionError(
            f"Metadata keys differ: missing={sorted(expected_keys - actual_keys)}, "
            f"unexpected={sorted(actual_keys - expected_keys)}"
        )
    for key in sorted(expected_keys):
        expected_values = expected[key]
        actual_values = actual[key]
        if len(expected_values) != len(actual_values):
            raise AssertionError(f"Metadata {key!r} has {len(actual_values)} values; expected {len(expected_values)}")
        for index, (expected_value, actual_value) in enumerate(zip(expected_values, actual_values)):
            expected_number = _as_float(expected_value)
            actual_number = _as_float(actual_value)
            if expected_number is not None and actual_number is not None:
                if not math.isclose(expected_number, actual_number, rel_tol=rtol, abs_tol=atol):
                    raise AssertionError(
                        f"Metadata {key!r}[{index}] is {actual_number}; expected {expected_number}"
                    )
            elif expected_value != actual_value:
                raise AssertionError(
                    f"Metadata {key!r}[{index}] is {actual_value!r}; expected {expected_value!r}"
                )


def compare_outputs(
    expected_path: Path,
    actual_path: Path,
    *,
    rtol: float = DEFAULT_RTOL,
    atol: float = DEFAULT_ATOL,
) -> None:
    expected_metadata, expected = _read_output(expected_path)
    actual_metadata, actual = _read_output(actual_path)
    _compare_metadata(expected_metadata, actual_metadata, rtol, atol)

    if "version" in actual_metadata and actual_metadata["version"] != [__version__]:
        raise AssertionError(
            f"Generated output reports version {actual_metadata['version']!r}; expected {[__version__]!r}"
        )
    if list(expected.columns) != list(actual.columns):
        missing = [column for column in expected.columns if column not in actual.columns]
        unexpected = [column for column in actual.columns if column not in expected.columns]
        raise AssertionError(f"CSV columns differ: missing={missing}, unexpected={unexpected}")
    if len(expected) != len(actual):
        raise AssertionError(f"CSV has {len(actual)} rows; expected {len(expected)}")

    timestamp_column = expected.columns[0]
    expected_timestamps = expected[timestamp_column].astype(str).str.strip()
    actual_timestamps = actual[timestamp_column].astype(str).str.strip()
    if not expected_timestamps.equals(actual_timestamps):
        mismatch = expected_timestamps.ne(actual_timestamps)
        index = int(mismatch[mismatch].index[0])
        raise AssertionError(
            f"Timestamp differs at row {index}: {actual_timestamps.iloc[index]!r}; "
            f"expected {expected_timestamps.iloc[index]!r}"
        )

    expected_values = expected.iloc[:, 1:].apply(pd.to_numeric, errors="raise")
    actual_values = actual.iloc[:, 1:].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(expected_values.to_numpy(dtype=float)).all():
        raise AssertionError(f"Expected output {expected_path} contains non-finite values")
    if not np.isfinite(actual_values.to_numpy(dtype=float)).all():
        raise AssertionError(f"Generated output {actual_path} contains non-finite values")
    pd.testing.assert_frame_equal(
        expected_values,
        actual_values,
        check_dtype=False,
        check_exact=False,
        rtol=rtol,
        atol=atol,
    )
