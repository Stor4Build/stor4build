# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import os
import shutil
import tempfile
import uuid
from pathlib import Path

import pytest


def pytest_addoption(parser):
    group = parser.getgroup("stor4build regression")
    group.addoption("--run-cli-regression", action="store_true", help="Run OpenStudio CLI regressions")
    group.addoption("--run-api-regression", action="store_true", help="Run configured API regressions")
    group.addoption("--case", action="append", default=[], metavar="GLOB", help="Run matching regression case IDs")
    group.addoption(
        "--shard-count",
        type=int,
        default=None,
        help="Divide selected regression cases into this many deterministic shards",
    )
    group.addoption(
        "--shard-index",
        type=int,
        default=None,
        help="Run this zero-based regression shard; requires --shard-count",
    )
    group.addoption(
        "--openstudio",
        default=os.environ.get("STOR4BUILD_OPENSTUDIO", "openstudio"),
        help="OpenStudio executable for CLI regressions",
    )
    group.addoption(
        "--api-url",
        default=os.environ.get("STOR4BUILD_API_URL", "http://127.0.0.1:5000"),
        help="Base URL for API regressions",
    )
    group.addoption(
        "--regression-output",
        type=Path,
        default=None,
        help="Directory in which to preserve generated regression artifacts",
    )
    group.addoption(
        "--regression-timeout",
        type=float,
        default=7200.0,
        help="Per-case timeout in seconds",
    )
    group.addoption(
        "--allow-toolchain-mismatch",
        action="store_true",
        help="Allow a non-canonical OpenStudio version for an exploratory CLI regression run",
    )


def pytest_configure(config):
    from .regression import validate_shard

    try:
        validate_shard(config.getoption("--shard-count"), config.getoption("--shard-index"))
    except ValueError as exc:
        raise pytest.UsageError(str(exc)) from exc
    config.addinivalue_line("markers", "cli_regression: requires a configured OpenStudio installation")
    config.addinivalue_line("markers", "api_regression: requires a configured stor4build API")


def pytest_collection_modifyitems(config, items):
    cli_skip = pytest.mark.skip(reason="use --run-cli-regression to run CLI regressions")
    api_skip = pytest.mark.skip(reason="use --run-api-regression to run API regressions")
    for item in items:
        if "cli_regression" in item.keywords and not config.getoption("--run-cli-regression"):
            item.add_marker(cli_skip)
        if "api_regression" in item.keywords and not config.getoption("--run-api-regression"):
            item.add_marker(api_skip)


def _temporary_test_directory(prefix):
    path = Path(tempfile.gettempdir()) / f"{prefix}-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    return path


@pytest.fixture
def scratch_dir():
    path = _temporary_test_directory("stor4build-test")
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def regression_case_dir(request):
    configured = request.config.getoption("--regression-output")
    if configured is None:
        path = _temporary_test_directory("stor4build-regression")
        try:
            yield path
        finally:
            shutil.rmtree(path, ignore_errors=True)
        return
    path = configured.resolve() / request.node.name
    path.mkdir(parents=True, exist_ok=True)
    yield path
