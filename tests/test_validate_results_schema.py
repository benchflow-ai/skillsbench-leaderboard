from __future__ import annotations

import json
import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location("validate_results_schema", ROOT / "scripts" / "validate_results_schema.py")
assert SPEC is not None and SPEC.loader is not None
validate_module = module_from_spec(SPEC)
SPEC.loader.exec_module(validate_module)


class ValidateResultsSchemaTests(unittest.TestCase):
    def test_accepts_query_compatible_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.json"
            self._write(path, self._result(self._row()))

            self.assertEqual(validate_module.validate_result_file(path), [])

    def test_rejects_non_uuid_participant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.json"
            payload = self._result(self._row())
            payload["participants"]["agent"] = "http://127.0.0.1:8080/agent"
            self._write(path, payload)

            errors = validate_module.validate_result_file(path)

        self.assertTrue(any("registered AgentBeats UUID" in error for error in errors))

    def test_rejects_rows_missing_query_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.json"
            row = self._row()
            row.pop("time_used")
            row.pop("infra_failure_type")
            row.pop("category")
            row.pop("difficulty")
            self._write(path, self._result(row))

            errors = validate_module.validate_result_file(path)

        self.assertTrue(any("time_used is required" in error for error in errors))
        self.assertTrue(any("infra_failure_type is required" in error for error in errors))
        self.assertTrue(any("category is required" in error for error in errors))
        self.assertTrue(any("difficulty is required" in error for error in errors))

    def test_rejects_empty_nested_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.json"
            payload = self._result(self._row())
            payload["results"][0]["results"] = []
            self._write(path, payload)

            errors = validate_module.validate_result_file(path)

        self.assertTrue(any("must contain at least one task row" in error for error in errors))

    @staticmethod
    def _write(path: Path, payload: object) -> None:
        path.write_text(json.dumps(payload))

    @staticmethod
    def _result(row: dict[str, object]) -> dict[str, object]:
        return {
            "status": "completed",
            "participants": {"agent": "019e4ed1-d333-7133-807f-5f22c04d5eef"},
            "results": [
                {
                    "status": "completed",
                    "participants": {"agent": "http://127.0.0.1:8080/agent"},
                    "results": [row],
                }
            ],
        }

    @staticmethod
    def _row() -> dict[str, object]:
        return {
            "task_id": "citation-check",
            "score_eligible": True,
            "passed": False,
            "reward": 0.0,
            "time_used": 75.477,
            "infra_failure_type": None,
            "category": "office-white-collar",
            "difficulty": "medium",
        }


if __name__ == "__main__":
    unittest.main()
