# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
import json
import subprocess

import pytest

from stor4build.run import run_workflow


def test_run_workflow_requires_openstudio(monkeypatch, scratch_dir):
    monkeypatch.setattr("stor4build.run.shutil.which", lambda executable: None)

    with pytest.raises(FileNotFoundError, match="Cannot find OpenStudio executable"):
        run_workflow("missing-openstudio", scratch_dir / "run", {})


def test_run_workflow_propagates_process_failures(monkeypatch, scratch_dir):
    monkeypatch.setattr("stor4build.run.shutil.which", lambda executable: "/opt/openstudio")

    def fail(command, **kwargs):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr("stor4build.run.subprocess.run", fail)
    run_dir = scratch_dir / "run"

    with pytest.raises(subprocess.CalledProcessError):
        run_workflow("openstudio", run_dir, {"seed_file": "model.osm"})

    assert json.loads((run_dir / "s4b.osw").read_text()) == {"seed_file": "model.osm"}


def test_run_workflow_returns_completed_process(monkeypatch, scratch_dir):
    monkeypatch.setattr("stor4build.run.shutil.which", lambda executable: "/opt/openstudio")
    completed = subprocess.CompletedProcess([], 0)
    observed = {}

    def succeed(command, **kwargs):
        observed["command"] = command
        observed.update(kwargs)
        return completed

    monkeypatch.setattr("stor4build.run.subprocess.run", succeed)
    run_dir = scratch_dir / "run"

    result = run_workflow("openstudio", run_dir, {}, measures_only=True)

    assert result is completed
    assert observed["command"] == [
        "/opt/openstudio",
        "run",
        "--show-stdout",
        "--measures_only",
        "-w",
        "s4b.osw",
    ]
    assert observed["cwd"] == run_dir
    assert observed["check"] is True
