# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from .regression import iter_cases, validate_manifest


def test_regression_manifest():
    assert validate_manifest() == []
    assert list(iter_cases("cli"))
    assert list(iter_cases("api"))
