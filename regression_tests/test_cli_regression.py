# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import pytest

from .regression import compare_outputs, iter_cases, run_cli_case, select_case


CLI_CASES = list(iter_cases("cli"))


@pytest.mark.cli_regression
@pytest.mark.parametrize("case", CLI_CASES, ids=lambda case: case.name)
def test_cli_regression(case, regression_case_dir, request):
    if not select_case(case, request.config.getoption("--case")):
        pytest.skip("case does not match --case selection")
    if not case.enabled:
        pytest.skip(case.reason or "CLI regression is disabled")
    if not case.expected.is_file():
        pytest.skip(f"approved CLI golden is missing: {case.expected.name}")

    output = regression_case_dir / case.expected.name
    run_dir = regression_case_dir / "run"
    run_cli_case(
        case,
        output,
        run_dir,
        request.config.getoption("--openstudio"),
        request.config.getoption("--regression-timeout"),
    )
    compare_outputs(case.expected, output)
