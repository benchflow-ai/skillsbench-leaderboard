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


if __name__ == "__main__":
    unittest.main()
