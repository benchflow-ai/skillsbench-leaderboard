from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RunScenarioWorkflowTests(unittest.TestCase):
    def test_task_set_override_updates_submission_metadata(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "run-scenario.yml").read_text()

        config_updates = workflow.count(".components.gateway.config.assessment_config.task_set = $task_set_manifest.task_set")
        metadata_updates = workflow.count(".metadata.task_set = $task_set_manifest.task_set")

        self.assertGreater(config_updates, 0)
        self.assertEqual(metadata_updates, config_updates)

    def test_shard_override_updates_submission_metadata(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "run-scenario.yml").read_text()

        config_updates = workflow.count(".components.gateway.config.assessment_config.num_shards = $num_shards")
        metadata_updates = workflow.count(".metadata.num_shards = $num_shards")

        self.assertGreater(config_updates, 0)
        self.assertEqual(metadata_updates, config_updates)

    def test_durable_private_proof_is_verified_after_publish(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "run-scenario.yml").read_text()

        publish_index = workflow.index("- name: Publish private proof")
        verify_index = workflow.index("- name: Verify published private proof")
        upload_index = workflow.index("- name: Upload shard results")

        self.assertLess(publish_index, verify_index)
        self.assertLess(verify_index, upload_index)
        self.assertIn('verify_args=(--manifest "${refs_file}" --proof-root "${download_root}")', workflow)
        self.assertIn('python scripts/verify_private_proof.py "${verify_args[@]}"', workflow)

    def test_smoke_private_proof_requires_real_a2a_evidence(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "run-scenario.yml").read_text()

        self.assertIn('if [[ "${TASK_SET_INPUT}" == "smoke" ]]', workflow)
        self.assertIn("--require-a2a-evidence-task citation-check", workflow)

    def test_shard_private_proof_manifest_includes_storage_metadata(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "run-scenario.yml").read_text()

        self.assertIn('"private_proof_storage": prefix', workflow)
        self.assertIn('"private_proof_retention": os.environ["PRIVATE_PROOF_RETENTION"]', workflow)


if __name__ == "__main__":
    unittest.main()
