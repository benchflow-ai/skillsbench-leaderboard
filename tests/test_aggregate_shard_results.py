from __future__ import annotations

import json
import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location("aggregate_shard_results", ROOT / "scripts" / "aggregate_shard_results.py")
assert SPEC is not None and SPEC.loader is not None
aggregate_module = module_from_spec(SPEC)
SPEC.loader.exec_module(aggregate_module)


class AggregateShardResultsTests(unittest.TestCase):
    def test_preserves_nested_shard_envelopes_and_uses_registered_participant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_json(root / "scenario.json", {"metadata": {"agentbeats_ids": {"baseline_agent": "019e4ed1-d333-7133-807f-5f22c04d5eef"}}})
            self._write_json(
                root / "shards" / "shard-0" / "results.json",
                {
                    "status": "completed",
                    "results": [
                        {
                            "status": "completed",
                            "participants": {"agent": "http://127.0.0.1:8080/agent"},
                            "results": [self._row()],
                        }
                    ],
                },
            )

            payload = aggregate_module.aggregate_shard_results(
                shard_artifacts=root / "shards",
                num_shards=1,
                scenario=root / "scenario.json",
            )

        self.assertEqual(payload["participants"], {"agent": "019e4ed1-d333-7133-807f-5f22c04d5eef"})
        self.assertEqual(payload["results"][0]["participants"], {"agent": "http://127.0.0.1:8080/agent"})
        self.assertEqual(payload["results"][0]["results"][0]["task_id"], "citation-check")

    def test_wraps_legacy_direct_rows_and_falls_back_to_shard_participant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_json(root / "scenario.json", {"metadata": {"agentbeats_ids": {"agent": ""}}})
            self._write_json(
                root / "shards" / "shard-0" / "results.json",
                {
                    "status": "completed",
                    "participants": {"agent": "http://127.0.0.1:8080/agent"},
                    "results": [self._row()],
                },
            )

            payload = aggregate_module.aggregate_shard_results(
                shard_artifacts=root / "shards",
                num_shards=1,
                scenario=root / "scenario.json",
            )

        self.assertEqual(payload["participants"], {"agent": "http://127.0.0.1:8080/agent"})
        self.assertEqual(payload["results"][0]["participants"], {"agent": "http://127.0.0.1:8080/agent"})
        self.assertEqual(payload["results"][0]["results"][0]["reward"], 0.0)

    def test_rejects_missing_participant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_json(root / "scenario.json", {"metadata": {"agentbeats_ids": {}}})
            self._write_json(
                root / "shards" / "shard-0" / "results.json",
                {
                    "status": "completed",
                    "results": [{"status": "completed", "participants": {}, "results": [self._row()]}],
                },
            )

            with self.assertRaises(aggregate_module.AggregateError):
                aggregate_module.aggregate_shard_results(
                    shard_artifacts=root / "shards",
                    num_shards=1,
                    scenario=root / "scenario.json",
                )

    @staticmethod
    def _write_json(path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload))

    @staticmethod
    def _row() -> dict[str, object]:
        return {
            "task_id": "citation-check",
            "score_eligible": True,
            "passed": False,
            "reward": 0.0,
        }


if __name__ == "__main__":
    unittest.main()
