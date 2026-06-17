#!/usr/bin/env python3
"""Validate AgentBeats result files stay compatible with DuckDB ingestion."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

AGENTBEATS_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")


def _fail(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path}: {message}")


def validate_result_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        return [f"{path}: invalid JSON: {exc}"]

    participants = data.get("participants")
    if not isinstance(participants, dict):
        _fail(errors, path, "missing participants object")
    else:
        agent = participants.get("agent")
        if not isinstance(agent, str) or not agent.strip():
            _fail(errors, path, "participants.agent must be a non-empty string")
        elif AGENTBEATS_UUID_RE.fullmatch(agent.strip()) is None:
            _fail(errors, path, "participants.agent must be a registered AgentBeats UUID")

    results = data.get("results")
    if not isinstance(results, list):
        _fail(errors, path, "results must be a list")
        return errors
    if not results:
        _fail(errors, path, "results must contain at least one shard result")

    row_count = 0
    for index, shard in enumerate(results):
        prefix = f"results[{index}]"
        if not isinstance(shard, dict):
            _fail(errors, path, f"{prefix} must be an object")
            continue
        if "task_id" in shard:
            _fail(errors, path, f"{prefix} uses legacy direct-row shape; wrap rows under {prefix}.results")
        nested = shard.get("results")
        if not isinstance(nested, list):
            _fail(errors, path, f"{prefix}.results must be a list")
            continue
        if not nested:
            _fail(errors, path, f"{prefix}.results must contain at least one task row")
            continue
        for row_index, row in enumerate(nested):
            row_count += 1
            row_prefix = f"{prefix}.results[{row_index}]"
            if not isinstance(row, dict):
                _fail(errors, path, f"{row_prefix} must be an object")
                continue
            if not isinstance(row.get("task_id"), str) or not row["task_id"].strip():
                _fail(errors, path, f"{row_prefix}.task_id must be a non-empty string")
            if not isinstance(row.get("score_eligible"), bool):
                _fail(errors, path, f"{row_prefix}.score_eligible must be boolean")
            if not isinstance(row.get("passed"), bool):
                _fail(errors, path, f"{row_prefix}.passed must be boolean")
            if "reward" not in row:
                _fail(errors, path, f"{row_prefix}.reward is required")
            elif not isinstance(row.get("reward"), int | float):
                _fail(errors, path, f"{row_prefix}.reward must be numeric")
            if "time_used" not in row:
                _fail(errors, path, f"{row_prefix}.time_used is required")
            elif row.get("time_used") is not None and not isinstance(row.get("time_used"), int | float):
                _fail(errors, path, f"{row_prefix}.time_used must be numeric or null")
            if "infra_failure_type" not in row:
                _fail(errors, path, f"{row_prefix}.infra_failure_type is required")
            elif row.get("infra_failure_type") is not None and not isinstance(row.get("infra_failure_type"), str):
                _fail(errors, path, f"{row_prefix}.infra_failure_type must be a string or null")
            if "category" not in row:
                _fail(errors, path, f"{row_prefix}.category is required")
            elif row.get("category") is not None and not isinstance(row.get("category"), str):
                _fail(errors, path, f"{row_prefix}.category must be a string or null")
            if "difficulty" not in row:
                _fail(errors, path, f"{row_prefix}.difficulty is required")
            elif row.get("difficulty") is not None and not isinstance(row.get("difficulty"), str):
                _fail(errors, path, f"{row_prefix}.difficulty must be a string or null")

    if row_count == 0 and isinstance(results, list) and results:
        _fail(errors, path, "results must contain at least one task row")
    return errors


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results")
    paths = sorted(root.glob("*.json"))
    errors: list[str] = []
    for path in paths:
        errors.extend(validate_result_file(path))

    if errors:
        print("AgentBeats result schema validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(paths)} result files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
