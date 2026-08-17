# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from collections import Counter
from pathlib import Path

from .regression import iter_cases, validate_manifest, validate_toolchain


def test_regression_manifest():
    assert validate_manifest() == []
    assert list(iter_cases("cli"))
    assert list(iter_cases("api"))


def test_regression_toolchain():
    assert validate_toolchain() == []


def test_every_model_has_one_cli_case():
    model_references = []
    for case in iter_cases("cli"):
        referenced = [Path(argument).name for argument in case.config["arguments"] if argument.endswith(".osm")]
        assert len(referenced) == 1, case.name
        model_references.extend(referenced)

    model_dir = Path(__file__).resolve().parents[1] / "models"
    expected = {path.name for path in model_dir.glob("*.osm")}
    counts = Counter(model_references)

    assert set(counts) == expected
    assert all(count == 1 for count in counts.values())


def test_at_least_half_of_cli_cases_specify_schedules():
    schedule_options = {"--charge-start", "--charge-end", "--discharge-start", "--discharge-end"}
    cases = list(iter_cases("cli"))
    explicit = 0
    for case in cases:
        present = schedule_options.intersection(case.config["arguments"])
        assert present in (set(), schedule_options), case.name
        explicit += present == schedule_options

    assert explicit * 2 >= len(cases)
