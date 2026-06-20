from __future__ import annotations

import json
import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location("verify_private_proof", ROOT / "scripts" / "verify_private_proof.py")
assert SPEC is not None and SPEC.loader is not None
verify_module = module_from_spec(SPEC)
SPEC.loader.exec_module(verify_module)


class VerifyPrivateProofTests(unittest.TestCase):
    def test_accepts_downloaded_private_proof_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root)

            summary = verify_module.verify_private_proofs(manifest_path=manifest, proof_root=root / "downloaded")

        self.assertEqual(summary["proof_count"], 1)
        self.assertEqual(summary["proofs"][0]["public_row_count"], 1)
        self.assertEqual(summary["proofs"][0]["copied_artifact_count"], 5)

    def test_accepts_required_a2a_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=self._active_a2a_trajectory())

            summary = verify_module.verify_private_proofs(
                manifest_path=manifest,
                proof_root=root / "downloaded",
                require_a2a_evidence_tasks=["citation-check"],
            )

        self.assertEqual(summary["proofs"][0]["a2a_evidence_task_count"], 1)

    def test_accepts_terminal_protocol_a2a_evidence_without_returned_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=self._terminal_protocol_a2a_trajectory())

            summary = verify_module.verify_private_proofs(
                manifest_path=manifest,
                proof_root=root / "downloaded",
                require_a2a_evidence_tasks=["citation-check"],
            )

        self.assertEqual(summary["proofs"][0]["a2a_evidence_task_count"], 1)

    def test_accepts_terminal_protocol_a2a_evidence_without_response_receipt(self) -> None:
        trajectory = [
            {key: value for key, value in event.items() if key != "agent_under_test_receipt"}
            for event in self._terminal_protocol_a2a_trajectory()
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=trajectory)

            summary = verify_module.verify_private_proofs(
                manifest_path=manifest,
                proof_root=root / "downloaded",
                require_a2a_evidence_tasks=["citation-check"],
            )

        self.assertEqual(summary["proofs"][0]["a2a_evidence_task_count"], 1)

    def test_accepts_terminal_protocol_a2a_evidence_after_initial_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=self._terminal_protocol_retry_a2a_trajectory())

            summary = verify_module.verify_private_proofs(
                manifest_path=manifest,
                proof_root=root / "downloaded",
                require_a2a_evidence_tasks=["citation-check"],
            )

        self.assertEqual(summary["proofs"][0]["a2a_evidence_task_count"], 1)

    def test_accepts_terminal_protocol_a2a_evidence_with_command_action_key(self) -> None:
        trajectory = self._terminal_protocol_a2a_trajectory()
        for event in trajectory:
            if event["type"] == "terminal_observation":
                event["action"] = {"action": "exec", "command": "cat /root/test.bib", "timeout_sec": 30}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=trajectory)

            summary = verify_module.verify_private_proofs(
                manifest_path=manifest,
                proof_root=root / "downloaded",
                require_a2a_evidence_tasks=["citation-check"],
            )

        self.assertEqual(summary["proofs"][0]["a2a_evidence_task_count"], 1)

    def test_rejects_terminal_protocol_exec_without_prior_task_request(self) -> None:
        trajectory = [
            event
            for event in self._terminal_protocol_retry_a2a_trajectory()
            if not (event.get("type") == "a2a_request" and event.get("turn") == 1)
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=trajectory)

            with self.assertRaisesRegex(verify_module.ProofError, "terminal-bench-shell-v1 exec evidence"):
                verify_module.verify_private_proofs(
                    manifest_path=manifest,
                    proof_root=root / "downloaded",
                    require_a2a_evidence_tasks=["citation-check"],
                )

    def test_rejects_terminal_protocol_a2a_evidence_without_response_event(self) -> None:
        trajectory = [
            event for event in self._terminal_protocol_a2a_trajectory() if event["type"] != "a2a_response"
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=trajectory)

            with self.assertRaisesRegex(verify_module.ProofError, "no agent-under-test A2A response receipt"):
                verify_module.verify_private_proofs(
                    manifest_path=manifest,
                    proof_root=root / "downloaded",
                    require_a2a_evidence_tasks=["citation-check"],
                )

    def test_rejects_terminal_protocol_a2a_evidence_without_exec_observation(self) -> None:
        trajectory = self._terminal_protocol_a2a_trajectory()
        for event in trajectory:
            if event["type"] == "terminal_observation":
                event["action"] = {"action": "final", "cmd": "cat /root/test.bib"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=trajectory)

            with self.assertRaisesRegex(verify_module.ProofError, "terminal-bench-shell-v1 exec evidence"):
                verify_module.verify_private_proofs(
                    manifest_path=manifest,
                    proof_root=root / "downloaded",
                    require_a2a_evidence_tasks=["citation-check"],
                )

    def test_accepts_returned_file_only_a2a_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=self._returned_file_a2a_trajectory())

            summary = verify_module.verify_private_proofs(
                manifest_path=manifest,
                proof_root=root / "downloaded",
                require_a2a_evidence_tasks=["citation-check"],
            )

        self.assertEqual(summary["proofs"][0]["a2a_evidence_task_count"], 1)

    def test_rejects_zero_event_a2a_evidence(self) -> None:
        trajectory = self._active_a2a_trajectory(event_count=0)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=trajectory)

            with self.assertRaisesRegex(verify_module.ProofError, "event_count > 0"):
                verify_module.verify_private_proofs(
                    manifest_path=manifest,
                    proof_root=root / "downloaded",
                    require_a2a_evidence_tasks=["citation-check"],
                )

    def test_rejects_missing_returned_file_a2a_evidence(self) -> None:
        trajectory = self._active_a2a_trajectory(returned_file_count=0)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=trajectory)

            with self.assertRaisesRegex(verify_module.ProofError, "returned_file_count > 0"):
                verify_module.verify_private_proofs(
                    manifest_path=manifest,
                    proof_root=root / "downloaded",
                    require_a2a_evidence_tasks=["citation-check"],
                )

    def test_rejects_missing_sandbox_context_a2a_evidence(self) -> None:
        trajectory = [
            event for event in self._active_a2a_trajectory() if event["type"] != "sandbox_context"
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=trajectory)

            with self.assertRaisesRegex(verify_module.ProofError, "returned-file evidence"):
                verify_module.verify_private_proofs(
                    manifest_path=manifest,
                    proof_root=root / "downloaded",
                    require_a2a_evidence_tasks=["citation-check"],
                )

    def test_rejects_a2a_error_evidence(self) -> None:
        trajectory = self._active_a2a_trajectory()
        trajectory.insert(2, {"type": "a2a_error", "message": "participant failed"})
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root, a2a_trajectory=trajectory)

            with self.assertRaisesRegex(verify_module.ProofError, "a2a_error"):
                verify_module.verify_private_proofs(
                    manifest_path=manifest,
                    proof_root=root / "downloaded",
                    require_a2a_evidence_tasks=["citation-check"],
                )

    def test_rejects_missing_required_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root)
            (root / "downloaded" / "proof-123" / "artifacts" / "citation-check" / "trajectory" / "acp_trajectory.jsonl").unlink()

            with self.assertRaises(verify_module.ProofError):
                verify_module.verify_private_proofs(manifest_path=manifest, proof_root=root / "downloaded")

    def test_accepts_non_scoreable_infra_failure_without_verifier_reward(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root)
            self._rewrite_as_infra_failure_without_reward(root)

            summary = verify_module.verify_private_proofs(manifest_path=manifest, proof_root=root / "downloaded")

        self.assertEqual(summary["proof_count"], 1)
        self.assertEqual(summary["proofs"][0]["copied_artifact_count"], 5)

    def test_rejects_non_scoreable_infra_failure_missing_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root)
            self._rewrite_as_infra_failure_without_reward(root, include_diagnostic=False)

            with self.assertRaisesRegex(verify_module.ProofError, "infra_failure.json"):
                verify_module.verify_private_proofs(manifest_path=manifest, proof_root=root / "downloaded")

    def test_rejects_invalid_jsonl_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._write_bundle(root)
            (root / "downloaded" / "proof-123" / "artifacts" / "citation-check" / "trajectory" / "a2a_trajectory.jsonl").write_text("not json\n")

            with self.assertRaises(verify_module.ProofError):
                verify_module.verify_private_proofs(manifest_path=manifest, proof_root=root / "downloaded")

    def _write_bundle(self, root: Path, *, a2a_trajectory: list[dict[str, object]] | None = None) -> Path:
        proof_id = "proof-123"
        storage = "s3://agentbeats-private-proof/run"
        manifest_path = root / "refs.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "private_proof_storage": storage,
                    "private_proof_retention": "90d",
                    "private_proof_manifest_refs": [f"{storage}/{proof_id}/proof.json"],
                }
            )
        )
        proof_dir = root / "downloaded" / proof_id
        task_dir = proof_dir / "artifacts" / "citation-check"
        (task_dir / "agent").mkdir(parents=True)
        (task_dir / "trajectory").mkdir()
        (task_dir / "verifier").mkdir()
        (task_dir / "agent" / "agentbeats_a2a.txt").write_text("[agentbeats-a2a] A2A prompt completed\n")
        (task_dir / "result.json").write_text('{"reward":0.0}\n')
        (task_dir / "trajectory" / "acp_trajectory.jsonl").write_text('{"type":"user_message"}\n')
        if a2a_trajectory is None:
            (task_dir / "trajectory" / "a2a_trajectory.jsonl").write_text('{"event":"done"}\n')
        else:
            (task_dir / "trajectory" / "a2a_trajectory.jsonl").write_text(
                "".join(json.dumps(event) + "\n" for event in a2a_trajectory)
            )
        (task_dir / "verifier" / "reward.txt").write_text("0.0\n")
        proof_dir.mkdir(parents=True, exist_ok=True)
        (proof_dir / "proof.json").write_text(json.dumps(self._proof(proof_id)))
        return manifest_path

    def _rewrite_as_infra_failure_without_reward(self, root: Path, *, include_diagnostic: bool = True) -> None:
        proof_dir = root / "downloaded" / "proof-123"
        task_dir = proof_dir / "artifacts" / "citation-check"
        (task_dir / "verifier" / "reward.txt").unlink()
        if include_diagnostic:
            (task_dir / "infra_failure.json").write_text(
                json.dumps(
                    {
                        "schema_version": "skillsbench.agentbeats.infra_failure.v1",
                        "task_id": "citation-check",
                        "trial_id": "citation-check__agentbeats__12345678",
                        "score_eligible": False,
                        "passed": False,
                        "reward": 0.0,
                        "infra_failure_type": "participant_timeout",
                        "error_type": "participant_timeout",
                        "source": "public_row",
                    }
                )
            )
        proof = json.loads((proof_dir / "proof.json").read_text())
        proof["public_rows"][0]["score_eligible"] = False
        proof["public_rows"][0]["infra_failure_type"] = "participant_timeout"
        proof["public_rows"][0]["error_type"] = "participant_timeout"
        proof["copied_artifacts"] = [
            artifact for artifact in proof["copied_artifacts"] if artifact["relative_path"] != "verifier/reward.txt"
        ]
        if include_diagnostic:
            proof["copied_artifacts"].append({"task_id": "citation-check", "relative_path": "infra_failure.json"})
        (proof_dir / "proof.json").write_text(json.dumps(proof))

    @staticmethod
    def _proof(proof_id: str) -> dict[str, object]:
        artifacts = [
            {"task_id": "citation-check", "relative_path": "agent/agentbeats_a2a.txt"},
            {"task_id": "citation-check", "relative_path": "result.json"},
            {"task_id": "citation-check", "relative_path": "trajectory/acp_trajectory.jsonl"},
            {"task_id": "citation-check", "relative_path": "trajectory/a2a_trajectory.jsonl"},
            {"task_id": "citation-check", "relative_path": "verifier/reward.txt"},
        ]
        return {
            "schema_version": "skillsbench.agentbeats.private_proof.v1",
            "proof_id": proof_id,
            "created_at": "2026-06-17T21:00:00Z",
            "participants": {"agent": "019e5799-ca68-7b33-b1a5-c97b92b6fda1"},
            "task_set": "smoke",
            "task_set_digest": "sha256:7118932b0d945649e7be1364754e355c533d0f0d0f6ffa56d38330bc3981a866",
            "task_set_manifest": {"task_set_digest": "sha256:7118932b0d945649e7be1364754e355c533d0f0d0f6ffa56d38330bc3981a866"},
            "public_rows": [
                {
                    "task_id": "citation-check",
                    "trial_id": "citation-check__agentbeats__12345678",
                    "score_eligible": True,
                    "passed": False,
                    "reward": 0.0,
                    "time_used": 74.049,
                    "infra_failure_type": None,
                    "error_type": None,
                }
            ],
            "worker_meta": {"worker": "skillsbench"},
            "private_proof_refs": [{"task_id": "citation-check", "rollout_dir": "/private/jobs/citation-check"}],
            "copied_artifacts": artifacts,
            "retention": "90d",
        }

    @staticmethod
    def _active_a2a_trajectory(*, event_count: int = 3, returned_file_count: int = 1) -> list[dict[str, object]]:
        return [
            {"type": "user_message", "text": "inspect /root/test.bib"},
            {
                "type": "sandbox_context",
                "agent_cwd": "/root",
                "files": [{"path": "/root/test.bib", "bytes": 34, "sha256": "abc123"}],
            },
            {
                "type": "a2a_request",
                "text": 'inspect /root/test.bib\n<sandbox_file path="/root/test.bib">...</sandbox_file>',
            },
            {
                "type": "a2a_response",
                "agent_under_test_receipt": {
                    "agent_under_test": True,
                    "participant_run_id": "purple-1",
                    "harness": "openhands",
                    "model": "deepseek/deepseek-v4-flash",
                    "provider": "deepseek",
                    "api_key_present": True,
                    "exit_code": 0,
                    "event_count": event_count,
                    "returned_file_count": returned_file_count,
                },
            },
        ]

    @staticmethod
    def _terminal_protocol_a2a_trajectory(*, event_count: int = 3) -> list[dict[str, object]]:
        return [
            {"type": "user_message", "text": "write /root/answer.json"},
            {
                "type": "a2a_request",
                "turn": 1,
                "text": json.dumps(
                    {
                        "kind": "task",
                        "protocol": "terminal-bench-shell-v1",
                        "instruction": "write /root/answer.json",
                    }
                ),
            },
            {
                "type": "a2a_response",
                "turn": 1,
                "agent_under_test_receipt": {
                    "agent_under_test": True,
                    "participant_run_id": "purple-1",
                    "harness": "openhands",
                    "model": "deepseek/deepseek-v4-flash",
                    "provider": "deepseek",
                    "api_key_present": True,
                    "exit_code": 0,
                    "event_count": event_count,
                    "returned_file_count": 0,
                },
            },
            {
                "type": "terminal_observation",
                "turn": 1,
                "action": {"action": "exec", "cmd": "cat /root/test.bib", "timeout_sec": 30},
                "observation": {"ok": True, "return_code": 0, "stdout": "@article{fake}\n", "stderr": ""},
            },
        ]

    @staticmethod
    def _terminal_protocol_retry_a2a_trajectory(*, event_count: int = 3) -> list[dict[str, object]]:
        return [
            {"type": "user_message", "text": "write /root/answer.json"},
            {
                "type": "a2a_request",
                "turn": 1,
                "text": json.dumps(
                    {
                        "kind": "task",
                        "protocol": "terminal-bench-shell-v1",
                        "instruction": "write /root/answer.json",
                    }
                ),
            },
            {
                "type": "a2a_response",
                "turn": 1,
                "agent_under_test_receipt": None,
            },
            {
                "type": "terminal_protocol_error",
                "turn": 1,
                "message": "Agent-under-test participant received the request.",
            },
            {
                "type": "a2a_request",
                "turn": 2,
                "text": json.dumps(
                    {
                        "kind": "protocol_error",
                        "protocol": "terminal-bench-shell-v1",
                        "error": "last response was not an exact JSON exec_request or final object",
                    }
                ),
            },
            {
                "type": "a2a_response",
                "turn": 2,
                "agent_under_test_receipt": {
                    "agent_under_test": True,
                    "participant_run_id": "purple-2",
                    "harness": "openhands",
                    "model": "deepseek/deepseek-v4-pro",
                    "provider": "deepseek",
                    "api_key_present": True,
                    "exit_code": 0,
                    "event_count": event_count,
                    "returned_file_count": 0,
                },
            },
            {
                "type": "terminal_observation",
                "turn": 2,
                "action": {"action": "exec", "cmd": "cat /root/test.bib", "timeout_sec": 30},
                "observation": {"ok": True, "return_code": 0, "stdout": "@article{fake}\n", "stderr": ""},
            },
        ]

    @staticmethod
    def _returned_file_a2a_trajectory(*, event_count: int = 46, returned_file_count: int = 4) -> list[dict[str, object]]:
        return [
            {"type": "user_message", "text": "solve dialogue-parser"},
            {
                "type": "a2a_request",
                "turn": 1,
                "text": json.dumps(
                    {
                        "kind": "task",
                        "protocol": "terminal-bench-shell-v1",
                        "instruction": "solve dialogue-parser",
                    }
                ),
            },
            {
                "type": "a2a_response",
                "turn": 1,
                "agent_under_test_receipt": {
                    "agent_under_test": True,
                    "participant_run_id": "purple-1",
                    "harness": "openhands",
                    "model": "deepseek/deepseek-v4-flash",
                    "provider": "deepseek",
                    "api_key_present": True,
                    "exit_code": 0,
                    "event_count": event_count,
                    "returned_file_count": returned_file_count,
                },
            },
            {
                "type": "returned_files",
                "uploaded": [
                    {
                        "path": "/app/solution.py",
                        "target_path": "/app/solution.py",
                        "bytes": 123,
                        "sha256": "a" * 64,
                        "media_type": "text/x-python",
                    }
                ],
                "skipped": [],
            },
        ]


if __name__ == "__main__":
    unittest.main()
