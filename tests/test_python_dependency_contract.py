from __future__ import annotations

import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PythonDependencyContractTests(unittest.TestCase):
    def test_pyproject_is_pep621_project_and_matches_runtime_requirements(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        project = pyproject["project"]

        self.assertEqual(project["name"], "baseball-player-sim")
        self.assertEqual(project["version"], "0.1.0")
        self.assertEqual(project["requires-python"], ">=3.12")

        requirements = [
            line.strip()
            for line in (ROOT / "requirements-api.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(project["dependencies"], requirements)

    def test_vercel_entrypoint_contract_is_preserved(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(pyproject["tool"]["vercel"]["entrypoint"], "src.api.app:app")


if __name__ == "__main__":
    unittest.main()
