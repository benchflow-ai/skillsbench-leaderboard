#!/usr/bin/env python3
"""Validate downloaded AgentBeats private proof bundles without printing contents."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any

REQUIRED_ROW_FIELDS = (
    "task_id",
    "trial_id",
    "score_eligible",
    "passed",
    "reward",
    "time_used",
    "infra_failure_type",
    "error_type",
)
BASE_REQUIRED_TASK_ARTIFACTS = (
    "agent/agentbeats_a2a.txt",
    "result.json",
    "trajectory/acp_trajectory.jsonl",
    "trajectory/a2a_trajectory.jsonl",
)
VERIFIER_REWARD_ARTIFACT = "verifier/reward.txt"
INFRA_FAILURE_ARTIFACT = "infra_failure.json"


class ProofError(Exception):
    pass


def verify_private_proofs(
    *,
    manifest_path: Path,
    proof_root: Path,
    require_a2a_evidence_tasks: Sequence[str] = (),
) -> dict[str, Any]:
    manifest = _load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ProofError("private proof ref manifest must be a JSON object")
    storage = _require_string(manifest, "private_proof_storage", "manifest")
    retention = _require_string(manifest, "private_proof_retention", "manifest")
    refs = manifest.get("private_proof_manifest_refs")
    if not isinstance(refs, list) or not refs:
        raise ProofError("manifest.private_proof_manifest_refs must be a non-empty list")
    if not all(isinstance(ref, str) and ref for ref in refs):
        raise ProofError("manifest.private_proof_manifest_refs must contain only non-empty strings")

    proof_files = sorted(proof_root.glob("**/proof.json"))
    if len(proof_files) != len(refs):
        raise ProofError(f"expected {len(refs)} downloaded proof.json file(s), found {len(proof_files)}")

    summaries: list[dict[str, Any]] = []
    for ref in refs:
        if not ref.startswith(storage.rstrip("/") + "/"):
            raise ProofError(f"proof ref is outside private_proof_storage: {ref}")
        if not ref.endswith("/proof.json"):
            raise ProofError(f"proof ref must end with /proof.json: {ref}")
        proof_id = ref.removesuffix("/proof.json").rstrip("/").rsplit("/", 1)[-1]
        matches = [path for path in proof_files if path.parent.name == proof_id]
        if len(matches) != 1:
            raise ProofError(f"expected one downloaded proof.json for proof_id {proof_id}, found {len(matches)}")
        summaries.append(
            _verify_proof(
                matches[0],
                proof_id=proof_id,
                retention=retention,
                require_a2a_evidence_tasks=set(require_a2a_evidence_tasks),
            )
        )

    return {"proof_count": len(summaries), "proofs": summaries}


def _verify_proof(
    path: Path,
    *,
    proof_id: str,
    retention: str,
    require_a2a_evidence_tasks: set[str],
) -> dict[str, Any]:
    proof = _load_json(path)
    if not isinstance(proof, dict):
        raise ProofError(f"{path}: proof must be a JSON object")
    if proof.get("schema_version") != "skillsbench.agentbeats.private_proof.v1":
        raise ProofError(f"{path}: unsupported schema_version")
    if proof.get("proof_id") != proof_id:
        raise ProofError(f"{path}: proof_id does not match manifest ref")
    if proof.get("retention") != retention:
        raise ProofError(f"{path}: retention does not match manifest ref")

    _require_string(proof, "task_set", str(path))
    _require_string(proof, "task_set_digest", str(path))
    _require_mapping(proof, "participants", str(path))
    _require_mapping(proof, "worker_meta", str(path))
    if not isinstance(proof.get("task_set_manifest"), dict):
        raise ProofError(f"{path}: task_set_manifest must be an object")
    private_refs = proof.get("private_proof_refs")
    if not isinstance(private_refs, list) or not private_refs:
        raise ProofError(f"{path}: private_proof_refs must be a non-empty list")

    rows = proof.get("public_rows")
    if not isinstance(rows, list) or not rows:
        raise ProofError(f"{path}: public_rows must be a non-empty list")
    rows_by_task = _validate_rows(path, rows)

    artifacts = proof.get("copied_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ProofError(f"{path}: copied_artifacts must be a non-empty list")
    artifacts_by_task = _validate_artifacts(path, proof_id=proof_id, artifacts=artifacts)
    for task_id, row in rows_by_task.items():
        rels = artifacts_by_task.get(task_id, set())
        required = list(BASE_REQUIRED_TASK_ARTIFACTS)
        if _row_requires_verifier_reward(row):
            required.append(VERIFIER_REWARD_ARTIFACT)
        else:
            required.append(INFRA_FAILURE_ARTIFACT)
        missing = [rel for rel in required if rel not in rels]
        if missing:
            raise ProofError(f"{path}: task {task_id} is missing required private artifact(s): {', '.join(missing)}")
        if task_id in require_a2a_evidence_tasks:
            _verify_a2a_evidence(path.parent / "artifacts" / task_id / "trajectory" / "a2a_trajectory.jsonl", task_id=task_id)

    return {
        "proof_id": proof_id,
        "task_set": proof["task_set"],
        "task_set_digest": proof["task_set_digest"],
        "public_row_count": len(rows),
        "task_count": len(rows_by_task),
        "copied_artifact_count": len(artifacts),
        "a2a_evidence_task_count": len(set(rows_by_task) & require_a2a_evidence_tasks),
        "task_ids_sha256": _sha256_text("\n".join(sorted(rows_by_task))),
    }


def _validate_rows(path: Path, rows: list[Any]) -> dict[str, dict[str, Any]]:
    rows_by_task: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ProofError(f"{path}: public_rows[{index}] must be an object")
        for field in REQUIRED_ROW_FIELDS:
            if field not in row:
                raise ProofError(f"{path}: public_rows[{index}].{field} is required")
        task_id = row["task_id"]
        if not isinstance(task_id, str) or not task_id:
            raise ProofError(f"{path}: public_rows[{index}].task_id must be a non-empty string")
        if not isinstance(row["trial_id"], str) or not row["trial_id"]:
            raise ProofError(f"{path}: public_rows[{index}].trial_id must be a non-empty string")
        if not isinstance(row["score_eligible"], bool):
            raise ProofError(f"{path}: public_rows[{index}].score_eligible must be boolean")
        if not isinstance(row["passed"], bool):
            raise ProofError(f"{path}: public_rows[{index}].passed must be boolean")
        if not isinstance(row["reward"], int | float):
            raise ProofError(f"{path}: public_rows[{index}].reward must be numeric")
        if row["time_used"] is not None and not isinstance(row["time_used"], int | float):
            raise ProofError(f"{path}: public_rows[{index}].time_used must be numeric or null")
        if row["score_eligible"] is False and (not isinstance(row["infra_failure_type"], str) or not row["infra_failure_type"]):
            raise ProofError(f"{path}: public_rows[{index}].infra_failure_type is required for non-scoreable rows")
        if row["score_eligible"] is True and row["infra_failure_type"] is not None:
            raise ProofError(f"{path}: public_rows[{index}].infra_failure_type must be null for scoreable rows")
        rows_by_task[task_id] = row
    return rows_by_task


def _row_requires_verifier_reward(row: dict[str, Any]) -> bool:
    return row["score_eligible"] is True or not isinstance(row["infra_failure_type"], str) or not row["infra_failure_type"]


def _validate_artifacts(path: Path, *, proof_id: str, artifacts: list[Any]) -> dict[str, set[str]]:
    artifacts_by_task: dict[str, set[str]] = {}
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            raise ProofError(f"{path}: copied_artifacts[{index}] must be an object")
        task_id = _require_string(artifact, "task_id", f"{path}: copied_artifacts[{index}]")
        relative_path = _require_string(artifact, "relative_path", f"{path}: copied_artifacts[{index}]")
        artifact_path = path.parent / "artifacts" / task_id / relative_path
        if not artifact_path.is_file():
            raise ProofError(f"{path}: copied artifact is missing from downloaded proof bundle: artifacts/{task_id}/{relative_path}")
        if relative_path.endswith(".jsonl"):
            _require_parseable_jsonl(artifact_path)
        elif relative_path.endswith(".json"):
            _load_json(artifact_path)
            if relative_path == INFRA_FAILURE_ARTIFACT:
                _validate_infra_failure_artifact(artifact_path, task_id=task_id)
        elif relative_path == "agent/agentbeats_a2a.txt":
            text = artifact_path.read_text(errors="replace")
            if "[agentbeats-a2a]" not in text:
                raise ProofError(f"{path}: agentbeats_a2a.txt does not contain bridge diagnostics")
        artifacts_by_task.setdefault(task_id, set()).add(relative_path)

    if path.parent.name != proof_id:
        raise ProofError(f"{path}: downloaded proof directory name does not match proof_id")
    return artifacts_by_task


def _validate_infra_failure_artifact(path: Path, *, task_id: str) -> None:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ProofError(f"{path}: infra_failure.json must be a JSON object")
    if payload.get("schema_version") != "skillsbench.agentbeats.infra_failure.v1":
        raise ProofError(f"{path}: unsupported infra_failure.json schema_version")
    if payload.get("task_id") != task_id:
        raise ProofError(f"{path}: infra_failure.json task_id does not match artifact task")
    if payload.get("score_eligible") is not False:
        raise ProofError(f"{path}: infra_failure.json score_eligible must be false")
    if not isinstance(payload.get("infra_failure_type"), str) or not payload["infra_failure_type"]:
        raise ProofError(f"{path}: infra_failure.json infra_failure_type must be non-empty")


def _require_parseable_jsonl(path: Path) -> None:
    lines = [line for line in path.read_text(errors="replace").splitlines() if line.strip()]
    if not lines:
        raise ProofError(f"{path}: JSONL artifact must not be empty")
    for line_no, line in enumerate(lines, start=1):
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProofError(f"{path}: invalid JSONL at line {line_no}: {exc}") from exc


def _load_jsonl(path: Path) -> list[Any]:
    lines = [line for line in path.read_text(errors="replace").splitlines() if line.strip()]
    if not lines:
        raise ProofError(f"{path}: JSONL artifact must not be empty")
    events: list[Any] = []
    for line_no, line in enumerate(lines, start=1):
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ProofError(f"{path}: invalid JSONL at line {line_no}: {exc}") from exc
    return events


def _verify_a2a_evidence(path: Path, *, task_id: str) -> None:
    events = _load_jsonl(path)
    if any(isinstance(event, dict) and event.get("type") == "a2a_error" for event in events):
        raise ProofError(f"{path}: task {task_id} contains an a2a_error event")

    receipts = [
        event.get("agent_under_test_receipt")
        for event in events
        if isinstance(event, dict) and event.get("type") == "a2a_response"
    ]
    receipts = [receipt for receipt in receipts if isinstance(receipt, dict)]
    if not receipts:
        raise ProofError(f"{path}: task {task_id} has no agent-under-test A2A response receipt")

    if _has_sandbox_file_a2a_evidence(events):
        if not any(_active_receipt_with_returned_files(receipt) for receipt in receipts):
            raise ProofError(
                f"{path}: task {task_id} has no receipt with event_count > 0 and returned_file_count > 0"
            )
        return

    if _has_terminal_protocol_a2a_evidence(events):
        if not any(_active_receipt(receipt) for receipt in receipts):
            raise ProofError(f"{path}: task {task_id} has no receipt with event_count > 0")
        return

    if _has_returned_file_a2a_evidence(events):
        if not any(_active_receipt_with_returned_files(receipt) for receipt in receipts):
            raise ProofError(
                f"{path}: task {task_id} has no receipt with event_count > 0 and returned_file_count > 0"
            )
        return

    raise ProofError(
        f"{path}: task {task_id} has neither sandbox_context file evidence, "
        "terminal-bench-shell-v1 exec evidence, nor returned-file evidence"
    )


def _has_sandbox_file_a2a_evidence(events: Sequence[Any]) -> bool:
    return any(
        isinstance(event, dict)
        and event.get("type") == "sandbox_context"
        and isinstance(event.get("files"), list)
        and event["files"]
        for event in events
    ) and any(
        isinstance(event, dict)
        and event.get("type") == "a2a_request"
        and isinstance(event.get("text"), str)
        and "<sandbox_file " in event["text"]
        for event in events
    )


def _has_terminal_protocol_a2a_evidence(events: Sequence[Any]) -> bool:
    return any(_is_terminal_task_request(event) for event in events) and any(
        isinstance(event, dict)
        and event.get("type") == "terminal_observation"
        and isinstance(event.get("action"), dict)
        and isinstance(event["action"].get("cmd"), str)
        and event["action"]["cmd"].strip()
        for event in events
    )


def _has_returned_file_a2a_evidence(events: Sequence[Any]) -> bool:
    return any(
        isinstance(event, dict)
        and event.get("type") == "returned_files"
        and _has_uploaded_file_evidence(event.get("uploaded"))
        for event in events
    )


def _has_uploaded_file_evidence(value: Any) -> bool:
    if not isinstance(value, list):
        return False
    return any(_is_uploaded_file_evidence(item) for item in value)


def _is_uploaded_file_evidence(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    target_path = value.get("target_path")
    if not isinstance(target_path, str) or not target_path.startswith("/"):
        return False
    target = PurePosixPath(target_path)
    if ".." in target.parts:
        return False
    bytes_value = value.get("bytes")
    if not _positive_number(bytes_value):
        return False
    sha256 = value.get("sha256")
    return isinstance(sha256, str) and len(sha256) == 64 and all(char in "0123456789abcdef" for char in sha256.lower())


def _is_terminal_task_request(event: Any) -> bool:
    if not isinstance(event, dict) or event.get("type") != "a2a_request":
        return False
    text = event.get("text")
    if not isinstance(text, str):
        return False
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return False
    return (
        isinstance(payload, dict)
        and payload.get("kind") == "task"
        and payload.get("protocol") == "terminal-bench-shell-v1"
        and isinstance(payload.get("instruction"), str)
        and bool(payload["instruction"].strip())
    )


def _active_receipt(receipt: dict[str, Any]) -> bool:
    return receipt.get("agent_under_test") is True and _positive_number(receipt.get("event_count"))


def _active_receipt_with_returned_files(receipt: dict[str, Any]) -> bool:
    return _active_receipt(receipt) and _positive_number(receipt.get("returned_file_count"))


def _positive_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and value > 0


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        raise ProofError(f"{path}: invalid JSON: {exc}") from exc


def _require_string(payload: dict[str, Any], key: str, context: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ProofError(f"{context}.{key} must be a non-empty string")
    return value


def _require_mapping(payload: dict[str, Any], key: str, context: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ProofError(f"{context}.{key} must be an object")
    return value


def _sha256_text(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--proof-root", type=Path, required=True)
    parser.add_argument(
        "--require-a2a-evidence-task",
        action="append",
        default=[],
        help="Task id that must have sandbox context and nonzero agent-under-test A2A activity.",
    )
    args = parser.parse_args()

    try:
        summary = verify_private_proofs(
            manifest_path=args.manifest,
            proof_root=args.proof_root,
            require_a2a_evidence_tasks=args.require_a2a_evidence_task,
        )
    except ProofError as exc:
        print(f"Private proof verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
