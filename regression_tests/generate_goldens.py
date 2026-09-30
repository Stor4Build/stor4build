# SPDX-FileCopyrightText: 2024-present Oak Ridge National Laboratory, managed by UT-Battelle, Alliance for Energy Innovation, LLC, and contributors
#
# SPDX-License-Identifier: BSD-3-Clause
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from stor4build import __version__

from .regression import (
    REGRESSION_DIR,
    RegressionCase,
    check_openstudio_toolchain,
    compare_outputs,
    format_regression_context,
    iter_cases,
    load_toolchain,
    run_cli_case,
    select_case,
)


SUMMARY_FILE = "generation.json"


def _prepare_output_directory(output: Path) -> Path:
    output = output.expanduser().resolve()
    regression_dir = REGRESSION_DIR.resolve()
    try:
        output.relative_to(regression_dir)
    except ValueError:
        pass
    else:
        raise ValueError(f"Candidate goldens must be written outside {regression_dir}")

    if output.exists():
        if not output.is_dir():
            raise FileExistsError(f"Candidate output path is not a directory: {output}")
        if any(output.iterdir()):
            raise FileExistsError(f"Candidate output directory is not empty: {output}")
    return output


def _select_cli_cases(patterns: list[str]) -> list[RegressionCase]:
    cases = [case for case in iter_cases("cli") if case.enabled and select_case(case, patterns)]
    if not cases:
        selection = ", ".join(patterns) if patterns else "the manifest"
        raise ValueError(f"No enabled CLI regression cases match {selection}")

    output_names = [case.expected.name for case in cases]
    duplicates = sorted(name for name in set(output_names) if output_names.count(name) > 1)
    if duplicates:
        raise ValueError(f"CLI cases have duplicate golden output names: {duplicates}")
    return cases


def _comparison_status(case: RegressionCase, candidate: Path) -> tuple[str, str | None]:
    if not case.expected.is_file():
        return "new", None
    try:
        compare_outputs(case.expected, candidate)
    except Exception as exc:
        return "changed", str(exc)
    return "match", None


def _write_summary(output: Path, summary: dict[str, Any]) -> None:
    path = output / SUMMARY_FILE
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def generate_goldens(
    output: Path,
    *,
    openstudio: str = "openstudio",
    patterns: list[str] | None = None,
    timeout: float = 7200.0,
) -> dict[str, Any]:
    """Generate CLI candidate goldens without modifying approved files."""
    patterns = patterns or []
    output = _prepare_output_directory(output)
    cases = _select_cli_cases(patterns)
    openstudio_toolchain = check_openstudio_toolchain(openstudio)
    output.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stor4build_version": __version__,
        "canonical_toolchain": load_toolchain(),
        "detected_toolchain": {
            "openstudio_executable": openstudio_toolchain.executable,
            "openstudio_version": openstudio_toolchain.detected_version,
            "version_output": openstudio_toolchain.version_output,
        },
        "host": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "selection": patterns,
        "cases": [],
    }

    for index, case in enumerate(cases, start=1):
        candidate = output / case.expected.name
        run_dir = output / "runs" / case.name
        print(f"[{index}/{len(cases)}] generating {case.name}")
        print(format_regression_context(case, candidate, openstudio_toolchain))
        entry: dict[str, Any] = {
            "case": case.name,
            "output": candidate.name,
            "approved_golden": case.expected.name,
            "arguments": case.config["arguments"],
        }
        try:
            run_cli_case(case, candidate, run_dir, openstudio_toolchain.executable, timeout)
        except Exception as exc:
            entry.update(status="failed", error=str(exc))
            print(f"FAILED: {case.name}: {exc}", file=sys.stderr)
        else:
            status, difference = _comparison_status(case, candidate)
            entry["status"] = status
            if difference is not None:
                entry["difference"] = difference
            print(f"{status.upper()}: {candidate}")
        summary["cases"].append(entry)

    statuses = [entry["status"] for entry in summary["cases"]]
    summary["counts"] = {
        status: statuses.count(status) for status in ("match", "changed", "new", "failed")
    }
    _write_summary(output, summary)
    print(f"Generation summary: {output / SUMMARY_FILE}")
    print(
        "Results: "
        + ", ".join(f"{status}={count}" for status, count in summary["counts"].items())
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate candidate regression goldens exclusively through the stor4build CLI."
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New or empty directory outside regression_tests for candidate outputs",
    )
    parser.add_argument(
        "--openstudio",
        default=os.environ.get("STOR4BUILD_OPENSTUDIO", "openstudio"),
        help="Canonical OpenStudio executable (default: STOR4BUILD_OPENSTUDIO or openstudio)",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        metavar="GLOB",
        help="Generate matching case IDs; may be supplied more than once",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=7200.0,
        help="Per-case timeout in seconds (default: 7200)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        summary = generate_goldens(
            args.output,
            openstudio=args.openstudio,
            patterns=args.case,
            timeout=args.timeout,
        )
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        parser.error(str(exc))
    return 1 if summary["counts"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
