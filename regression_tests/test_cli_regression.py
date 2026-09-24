# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import pytest

from .regression import (
    check_openstudio_toolchain,
    compare_outputs,
    format_regression_context,
    iter_cases,
    run_cli_case,
    select_cases,
)


CLI_CASES = list(iter_cases("cli"))


@pytest.mark.cli_regression
@pytest.mark.parametrize("case", CLI_CASES, ids=lambda case: case.name)
def test_cli_regression(case, regression_case_dir, request):
    selected = select_cases(
        CLI_CASES,
        request.config.getoption("--case"),
        shard_count=request.config.getoption("--shard-count"),
        shard_index=request.config.getoption("--shard-index"),
    )
    if case not in selected:
        pytest.skip("case is not in the selected regression shard")
    if not case.enabled:
        pytest.skip(case.reason or "CLI regression is disabled")
    if not case.expected.is_file():
        pytest.skip(f"approved CLI golden is missing: {case.expected.name}")

    output = regression_case_dir / case.expected.name
    run_dir = regression_case_dir / "run"
    openstudio = check_openstudio_toolchain(
        request.config.getoption("--openstudio"),
        allow_mismatch=request.config.getoption("--allow-toolchain-mismatch"),
    )
    print(format_regression_context(case, output, openstudio))
    run_cli_case(
        case,
        output,
        run_dir,
        openstudio.executable,
        request.config.getoption("--regression-timeout"),
    )
    compare_outputs(case.expected, output)
