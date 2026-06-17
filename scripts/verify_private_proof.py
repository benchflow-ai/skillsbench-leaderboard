#!/usr/bin/env python3
"""Validate downloaded AgentBeats private proof bundles without printing contents."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
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
REQUIRED_TASK_ARTIFACTS = (
    "agent/agentbeats_a2a.txt",
    "result.json",
    "trajectory/acp_trajectory.jsonl",
    "trajectory/a2a_trajectory.jsonl",
    "verifier/reward.txt",
)


class ProofError(Exception):
    pass


def verify_private_proofs(*, manifest_path: Path, proof_root: Path) -> dict[str, Any]:
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
        summaries.append(_verify_proof(matches[0], proof_id=proof_id, retention=retention))

    return {"proof_count": len(summaries), "proofs": summaries}


def _verify_proof(path: Path, *, proof_id: str, retention: str) -> dict[str, Any]:
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
    task_ids = _validate_rows(path, rows)

    artifacts = proof.get("copied_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ProofError(f"{path}: copied_artifacts must be a non-empty list")
    artifacts_by_task = _validate_artifacts(path, proof_id=proof_id, artifacts=artifacts)
    for task_id in task_ids:
        rels = artifacts_by_task.get(task_id, set())
        missing = [rel for rel in REQUIRED_TASK_ARTIFACTS if rel not in rels]
        if missing:
            raise ProofError(f"{path}: task {task_id} is missing required private artifact(s): {', '.join(missing)}")

    return {
        "proof_id": proof_id,
        "task_set": proof["task_set"],
        "task_set_digest": proof["task_set_digest"],
        "public_row_count": len(rows),
        "task_count": len(task_ids),
        "copied_artifact_count": len(artifacts),
        "task_ids_sha256": _sha256_text("\n".join(sorted(task_ids))),
    }


def _validate_rows(path: Path, rows: list[Any]) -> set[str]:
    task_ids: set[str] = set()
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
        task_ids.add(task_id)
    return task_ids


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
        elif relative_path == "agent/agentbeats_a2a.txt":
            text = artifact_path.read_text(errors="replace")
            if "[agentbeats-a2a]" not in text:
                raise ProofError(f"{path}: agentbeats_a2a.txt does not contain bridge diagnostics")
        artifacts_by_task.setdefault(task_id, set()).add(relative_path)

    if path.parent.name != proof_id:
        raise ProofError(f"{path}: downloaded proof directory name does not match proof_id")
    return artifacts_by_task


def _require_parseable_jsonl(path: Path) -> None:
    lines = [line for line in path.read_text(errors="replace").splitlines() if line.strip()]
    if not lines:
        raise ProofError(f"{path}: JSONL artifact must not be empty")
    for line_no, line in enumerate(lines, start=1):
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProofError(f"{path}: invalid JSONL at line {line_no}: {exc}") from exc


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
    args = parser.parse_args()

    try:
        summary = verify_private_proofs(manifest_path=args.manifest, proof_root=args.proof_root)
    except ProofError as exc:
        print(f"Private proof verification failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
