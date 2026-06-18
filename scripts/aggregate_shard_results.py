#!/usr/bin/env python3
"""Aggregate AgentBeats shard result artifacts without flattening rows."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

AGENTBEATS_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")


class AggregateError(ValueError):
    """Raised when shard artifacts cannot produce a publishable result."""


def aggregate_shard_results(*, shard_artifacts: Path, num_shards: int, scenario: Path) -> dict[str, Any]:
    shard_payloads = [_load_shard_payload(shard_artifacts, index) for index in range(num_shards)]
    envelopes = [envelope for payload in shard_payloads for envelope in _result_envelopes(payload)]
    if not envelopes:
        raise AggregateError("no result envelopes found in shard artifacts")
    row_count = sum(len(envelope.get("results", [])) for envelope in envelopes if isinstance(envelope.get("results"), list))
    if row_count == 0:
        raise AggregateError("no task result rows found in shard artifacts")
    participant = _scenario_participant(scenario)
    return {
        "status": _aggregate_status(shard_payloads),
        "participants": {"agent": participant},
        "results": envelopes,
    }


def _load_shard_payload(shard_artifacts: Path, shard_index: int) -> dict[str, Any]:
    path = shard_artifacts / f"shard-{shard_index}" / "results.json"
    if not path.is_file():
        raise AggregateError(f"missing results for shard {shard_index}: {path}")
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise AggregateError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise AggregateError(f"{path} must contain a JSON object")
    return payload


def _result_envelopes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results")
    if not isinstance(results, list):
        raise AggregateError("shard payload results must be a list")

    envelopes: list[dict[str, Any]] = []
    direct_rows: list[dict[str, Any]] = []
    for item in results:
        if not isinstance(item, dict):
            raise AggregateError("shard payload results entries must be objects")
        nested = item.get("results")
        if isinstance(nested, list):
            envelopes.append(item)
        elif "task_id" in item:
            direct_rows.append(item)
        else:
            raise AggregateError("shard payload results entries must be result envelopes or task rows")

    if direct_rows:
        envelopes.append(
            {
                "status": payload.get("status", "completed"),
                "participants": payload.get("participants", {}),
                "results": direct_rows,
            }
        )
    return envelopes


def _scenario_participant(scenario: Path) -> str | None:
    payload = _load_scenario(scenario)
    metadata = payload.get("metadata") if isinstance(payload, dict) else None
    agentbeats_ids = metadata.get("agentbeats_ids") if isinstance(metadata, dict) else None
    if not isinstance(agentbeats_ids, dict):
        raise AggregateError("scenario metadata.agentbeats_ids is required")
    for key in ("baseline_agent", "agent", "agent_under_test"):
        value = agentbeats_ids.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        participant = value.strip()
        if AGENTBEATS_UUID_RE.fullmatch(participant) is None:
            raise AggregateError(f"scenario metadata.agentbeats_ids.{key} must be a registered AgentBeats UUID")
        return participant
    raise AggregateError("scenario metadata.agentbeats_ids must include a registered participant UUID")


def _load_scenario(scenario: Path) -> dict[str, Any]:
    try:
        raw = scenario.read_text()
    except OSError as exc:
        raise AggregateError(f"unable to read scenario metadata: {scenario}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = _load_json5_scenario(scenario)
    if not isinstance(payload, dict):
        raise AggregateError("scenario metadata must be a JSON object")
    return payload


def _load_json5_scenario(scenario: Path) -> Any:
    try:
        completed = subprocess.run(
            ["npx", "--yes", "json5", str(scenario)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AggregateError(f"unable to parse scenario as JSON or JSON5: {scenario}") from exc
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AggregateError(f"JSON5 parser returned invalid JSON for {scenario}: {exc}") from exc


def _aggregate_status(payloads: list[dict[str, Any]]) -> str:
    statuses = [payload.get("status") for payload in payloads]
    if statuses and all(status == "completed" for status in statuses):
        return "completed"
    if any(status == "completed" for status in statuses):
        return "partial"
    return "failed"


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard-artifacts", type=Path, required=True)
    parser.add_argument("--num-shards", type=int, required=True)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = aggregate_shard_results(
            shard_artifacts=args.shard_artifacts,
            num_shards=args.num_shards,
            scenario=args.scenario,
        )
    except AggregateError as exc:
        print(f"AgentBeats result aggregation failed: {exc}", file=sys.stderr)
        return 1
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
