"""Network-free safety tests for the weekly publishing gate."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from publish_weekly import publish
from weekly_contract import validate_edition

ROOT = Path(__file__).resolve().parents[1]


class WeeklyPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.valid = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))

    def test_current_edition_satisfies_contract(self) -> None:
        validate_edition(self.valid)

    def test_invalid_edition_never_replaces_live_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "papers.json"
            source = root / "invalid.json"
            history = root / "history"
            target.write_text('{"sentinel": true}', encoding="utf-8")
            invalid = copy.deepcopy(self.valid)
            for item in invalid["items"]:
                item["featured"] = False
            source.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError):
                publish(source, target, history, online=False)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"sentinel": True})

    def test_valid_publish_is_atomic_and_keeps_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "papers.json"
            source = root / "curated.json"
            history = root / "history"
            target.write_text(json.dumps(self.valid, ensure_ascii=False), encoding="utf-8")
            source.write_text(json.dumps(self.valid, ensure_ascii=False), encoding="utf-8")
            publish(source, target, history, online=False)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["updatedAt"], self.valid["updatedAt"])
            self.assertTrue((history / f"papers-{self.valid['updatedAt']}.json").exists())
            self.assertFalse(target.with_suffix(".json.tmp").exists())

    def test_doi_network_failure_never_replaces_live_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "papers.json"
            source = root / "curated.json"
            history = root / "history"
            target.write_text('{"sentinel": "last-live-edition"}', encoding="utf-8")
            source.write_text(json.dumps(self.valid, ensure_ascii=False), encoding="utf-8")
            with patch("publish_weekly.verify_doi", side_effect=ValueError("simulated Crossref outage")):
                with self.assertRaises(ValueError):
                    publish(source, target, history, online=True)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"sentinel": "last-live-edition"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
