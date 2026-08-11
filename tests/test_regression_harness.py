# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from pathlib import Path
import subprocess

import httpx
import pytest

from regression_tests.regression import (
    RegressionCase,
    check_openstudio_toolchain,
    compare_outputs,
    prepare_cli_arguments,
    run_api_case,
    run_cli_case,
)
from stor4build import __version__


def _write_output(path: Path, version: str, value: float) -> None:
    path.write_text(
        f"version,{version}\n"
        'building_type,"LargeOffice"\n'
        "Date/Time,Load [W](Hourly)\n"
        f" 2006-01-01T00:00:00,{value}\n",
        encoding="utf-8",
    )


def test_compare_outputs_allows_historical_golden_version(scratch_dir):
    expected = scratch_dir / "expected.csv"
    actual = scratch_dir / "actual.csv"
    _write_output(expected, "0.3.0", 100.0)
    _write_output(actual, __version__, 100.00001)

    compare_outputs(expected, actual)


def test_compare_outputs_reports_numeric_regression(scratch_dir):
    expected = scratch_dir / "expected.csv"
    actual = scratch_dir / "actual.csv"
    _write_output(expected, "0.3.0", 100.0)
    _write_output(actual, __version__, 120.0)

    with pytest.raises(AssertionError):
        compare_outputs(expected, actual)


def test_prepare_cli_arguments_redirects_outputs(scratch_dir):
    case = RegressionCase(
        "case",
        "cli",
        {"arguments": ["size-icetank", "-m", "measures", "-o", "golden.csv", "model.osm", "weather.epw"]},
        scratch_dir / "golden.csv",
    )

    arguments = prepare_cli_arguments(case, scratch_dir / "actual.csv", scratch_dir / "run", "openstudio-3.11")

    assert arguments[:5] == ["size-icetank", "--openstudio", "openstudio-3.11", "-r", str(scratch_dir / "run")]
    assert arguments[arguments.index("-o") + 1] == str(scratch_dir / "actual.csv")


def test_check_openstudio_toolchain_accepts_canonical_version(monkeypatch):
    monkeypatch.setattr("regression_tests.regression.shutil.which", lambda executable: "/opt/openstudio")
    monkeypatch.setattr(
        "regression_tests.regression.subprocess.run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "3.11.0\n", ""),
    )

    toolchain = check_openstudio_toolchain("openstudio")

    assert toolchain.executable == "/opt/openstudio"
    assert toolchain.expected_version == "3.11.0"
    assert toolchain.detected_version == "3.11.0"


def test_check_openstudio_toolchain_rejects_mismatch(monkeypatch):
    monkeypatch.setattr("regression_tests.regression.shutil.which", lambda executable: "/opt/openstudio")
    monkeypatch.setattr(
        "regression_tests.regression.subprocess.run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "3.10.0\n", ""),
    )

    with pytest.raises(RuntimeError, match="canonical regression toolchain requires 3.11.0"):
        check_openstudio_toolchain("openstudio")


def test_check_openstudio_toolchain_allows_explicit_override(monkeypatch):
    monkeypatch.setattr("regression_tests.regression.shutil.which", lambda executable: "/opt/openstudio")
    monkeypatch.setattr(
        "regression_tests.regression.subprocess.run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "OpenStudio 3.10.0\n", ""),
    )

    with pytest.warns(UserWarning, match="Continuing"):
        toolchain = check_openstudio_toolchain("openstudio", allow_mismatch=True)

    assert toolchain.detected_version == "3.10.0"


def test_run_cli_case_uses_package_entry_point(monkeypatch, scratch_dir):
    output = scratch_dir / "actual.csv"
    case = RegressionCase(
        "case",
        "cli",
        {"arguments": ["size-icetank", "-o", "golden.csv", "model.osm", "weather.epw"]},
        scratch_dir / "golden.csv",
    )
    observed = {}

    def succeed(command, **kwargs):
        observed["command"] = command
        observed.update(kwargs)
        output.write_text("Date/Time,Value\n 2006-01-01T00:00:00,1\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "complete", "")

    monkeypatch.setattr("regression_tests.regression.subprocess.run", succeed)

    run_cli_case(case, output, scratch_dir / "run", "openstudio-3.11", 30.0)

    assert observed["command"][1:3] == ["-m", "stor4build"]
    assert observed["cwd"].name == "stor4build"
    assert observed["timeout"] == 30.0


def test_run_api_case_checks_csv_response(monkeypatch, scratch_dir):
    case = RegressionCase(
        "case",
        "api",
        {"enabled": True, "request": {"storage": {}, "baseline": {}}},
        scratch_dir / "golden.csv",
    )
    observed = {}

    def respond(url, **kwargs):
        observed["url"] = url
        observed.update(kwargs)
        return httpx.Response(
            200,
            text="Date/Time,Value\n 2006-01-01T00:00:00,1\n",
            headers={"content-type": "text/csv; charset=utf-8"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr("regression_tests.regression.httpx.post", respond)
    output = scratch_dir / "actual.csv"

    run_api_case(case, output, "http://localhost:5000/", 30.0)

    assert observed["url"] == "http://localhost:5000/simulate"
    assert observed["timeout"] == 30.0
    assert output.is_file()
