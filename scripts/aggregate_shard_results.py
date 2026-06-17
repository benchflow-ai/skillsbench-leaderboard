#!/usr/bin/env python3
"""Aggregate AgentBeats shard result artifacts without flattening rows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class AggregateError(ValueError):
    """Raised when shard artifacts cannot produce a publishable result."""


def aggregate_shard_results(*, shard_artifacts: Path, num_shards: int, scenario: Path) -> dict[str, Any]:
    shard_payloads = [_load_shard_payload(shard_artifacts, index) for index in range(num_shards)]
    envelopes = [envelope for payload in shard_payloads for envelope in _result_envelopes(payload)]
    participant = _scenario_participant(scenario) or _first_shard_participant(envelopes) or _first_shard_participant(shard_payloads)
    if not participant:
        raise AggregateError("participants.agent could not be resolved from scenario metadata or shard results")
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
            continue
        nested = item.get("results")
        if isinstance(nested, list):
            envelopes.append(item)
        elif "task_id" in item:
            direct_rows.append(item)

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
    try:
        payload = json.loads(scenario.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    metadata = payload.get("metadata") if isinstance(payload, dict) else None
    agentbeats_ids = metadata.get("agentbeats_ids") if isinstance(metadata, dict) else None
    if not isinstance(agentbeats_ids, dict):
        return None
    for key in ("baseline_agent", "agent", "agent_under_test"):
        value = agentbeats_ids.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _first_shard_participant(payloads: list[dict[str, Any]]) -> str | None:
    for payload in payloads:
        participants = payload.get("participants")
        if not isinstance(participants, dict):
            continue
        agent = participants.get("agent")
        if isinstance(agent, str) and agent.strip():
            return agent.strip()
    return None


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
