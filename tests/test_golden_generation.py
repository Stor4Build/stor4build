# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import json
import subprocess
from pathlib import Path

import pytest

from regression_tests.generate_goldens import generate_goldens
from regression_tests.regression import OpenStudioToolchain, REGRESSION_DIR, RegressionCase
from stor4build import __version__


def _write_output(path: Path, value: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"version,{__version__}\n"
        'building_type,"LargeOffice"\n'
        "Date/Time,Load [W](Hourly)\n"
        f" 2006-01-01T00:00:00,{value}\n",
        encoding="utf-8",
    )


def _case(name: str, expected: Path) -> RegressionCase:
    return RegressionCase(
        name,
        "cli",
        {"arguments": ["size-icetank", "-o", expected.name, "model.osm", "weather.epw"]},
        expected,
    )


def _mock_toolchain(monkeypatch) -> None:
    monkeypatch.setattr(
        "regression_tests.generate_goldens.check_openstudio_toolchain",
        lambda executable: OpenStudioToolchain("/opt/openstudio", "3.11.0", "3.11.0", "3.11.0"),
    )


def test_generate_goldens_reports_match_change_and_new(monkeypatch, scratch_dir):
    approved = scratch_dir / "approved"
    matching = _case("matching", approved / "matching.csv")
    changed = _case("changed", approved / "changed.csv")
    new = _case("new", approved / "new.csv")
    _write_output(matching.expected, 100.0)
    _write_output(changed.expected, 100.0)
    monkeypatch.setattr(
        "regression_tests.generate_goldens.iter_cases",
        lambda adapter: [matching, changed, new],
    )
    _mock_toolchain(monkeypatch)

    def generate(case, output, run_dir, openstudio, timeout):
        _write_output(output, 120.0 if case.name == "changed" else 100.0)
        return subprocess.CompletedProcess([], 0, "", "")

    monkeypatch.setattr("regression_tests.generate_goldens.run_cli_case", generate)
    output = scratch_dir / "candidates"

    summary = generate_goldens(output)

    assert summary["counts"] == {"match": 1, "changed": 1, "new": 1, "failed": 0}
    assert [entry["status"] for entry in summary["cases"]] == ["match", "changed", "new"]
    assert (output / "generation.json").is_file()
    assert json.loads((output / "generation.json").read_text(encoding="utf-8"))["counts"] == summary["counts"]


def test_generate_goldens_applies_case_selection(monkeypatch, scratch_dir):
    cases = [_case("selected_case", scratch_dir / "selected.csv"), _case("other_case", scratch_dir / "other.csv")]
    monkeypatch.setattr("regression_tests.generate_goldens.iter_cases", lambda adapter: cases)
    _mock_toolchain(monkeypatch)
    observed = []

    def generate(case, output, run_dir, openstudio, timeout):
        observed.append(case.name)
        _write_output(output, 100.0)
        return subprocess.CompletedProcess([], 0, "", "")

    monkeypatch.setattr("regression_tests.generate_goldens.run_cli_case", generate)

    summary = generate_goldens(scratch_dir / "candidates", patterns=["selected*"])

    assert observed == ["selected_case"]
    assert [entry["case"] for entry in summary["cases"]] == ["selected_case"]


def test_generate_goldens_continues_after_case_failure(monkeypatch, scratch_dir):
    cases = [_case("failed_case", scratch_dir / "failed.csv"), _case("new_case", scratch_dir / "new.csv")]
    monkeypatch.setattr("regression_tests.generate_goldens.iter_cases", lambda adapter: cases)
    _mock_toolchain(monkeypatch)

    def generate(case, output, run_dir, openstudio, timeout):
        if case.name == "failed_case":
            raise AssertionError("simulation failed")
        _write_output(output, 100.0)
        return subprocess.CompletedProcess([], 0, "", "")

    monkeypatch.setattr("regression_tests.generate_goldens.run_cli_case", generate)

    summary = generate_goldens(scratch_dir / "candidates")

    assert summary["counts"]["failed"] == 1
    assert summary["counts"]["new"] == 1
    assert [entry["status"] for entry in summary["cases"]] == ["failed", "new"]


def test_generate_goldens_rejects_approved_and_nonempty_directories(scratch_dir):
    with pytest.raises(ValueError, match="outside"):
        generate_goldens(REGRESSION_DIR / "candidate-goldens")

    output = scratch_dir / "not-empty"
    output.mkdir()
    (output / "keep.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError, match="not empty"):
        generate_goldens(output)
