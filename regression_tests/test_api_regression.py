# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import pytest

from .regression import compare_outputs, format_regression_context, iter_cases, run_api_case, select_cases


API_CASES = list(iter_cases("api"))


@pytest.mark.api_regression
@pytest.mark.parametrize("case", API_CASES, ids=lambda case: case.name)
def test_api_regression(case, regression_case_dir, request):
    selected = select_cases(
        API_CASES,
        request.config.getoption("--case"),
    )
    if case not in selected:
        pytest.skip("case does not match the selected case patterns")
    if not case.enabled:
        pytest.skip(case.reason or "API regression is disabled")
    if not case.expected.is_file():
        pytest.skip(f"approved API golden is missing: {case.expected.name}")

    output = regression_case_dir / case.expected.name
    print(format_regression_context(case, output))
    run_api_case(
        case,
        output,
        request.config.getoption("--api-url"),
        request.config.getoption("--regression-timeout"),
    )
    compare_outputs(case.expected, output)
