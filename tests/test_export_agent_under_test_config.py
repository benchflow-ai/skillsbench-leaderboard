from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "export-agent-under-test-config.sh"


class ExportAgentUnderTestConfigTests(unittest.TestCase):
    def test_provider_key_takes_precedence_over_generic_key(self) -> None:
        result, github_env = self._run_export(
            {
                "AGENT_MODEL": "deepseek/deepseek-v4-flash",
                "AGENT_UNDER_TEST_API_KEY": "generic-key",
                "DEEPSEEK_API_KEY": "deepseek-key",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("deepseek-key", github_env)
        self.assertNotIn("generic-key", github_env)

    def test_generic_key_is_fallback_for_non_strict_provider_when_provider_key_missing(self) -> None:
        result, github_env = self._run_export(
            {
                "AGENT_MODEL": "gemini/gemini-3.5-flash",
                "AGENT_UNDER_TEST_API_KEY": "generic-key",
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("generic-key", github_env)

    def test_deepseek_requires_provider_specific_key(self) -> None:
        result, github_env = self._run_export(
            {
                "AGENT_MODEL": "deepseek/deepseek-v4-flash",
                "AGENT_UNDER_TEST_API_KEY": "generic-key",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(github_env, "")
        self.assertIn("AGENT_UNDER_TEST__DEEPSEEK_API_KEY", result.stderr)

    def test_missing_key_fails_with_model_name(self) -> None:
        result, _github_env = self._run_export({"AGENT_MODEL": "deepseek/deepseek-v4-flash"})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("deepseek/deepseek-v4-flash", result.stderr)

    def _run_export(self, extra_env: dict[str, str]) -> tuple[subprocess.CompletedProcess[str], str]:
        with tempfile.TemporaryDirectory() as tmp:
            github_env_path = Path(tmp) / "github-env"
            env = {
                "GITHUB_ENV": str(github_env_path),
                "PATH": os.environ.get("PATH", ""),
            }
            env.update(extra_env)
            result = subprocess.run(
                ["bash", str(SCRIPT)],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            github_env = github_env_path.read_text() if github_env_path.exists() else ""
            return result, github_env


if __name__ == "__main__":
    unittest.main()
