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


def next_curated() -> dict:
    """A curated file that continues the current published edition."""
    data = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))
    data["edition"] = data["edition"] + 1
    return data


class WeeklyPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.valid = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.target = root / "papers.json"
        self.source = root / "curated.json"
        self.history = root / "history"
        self.manifest = root / "editions.json"

    def tearDown(self) -> None:
        self.directory.cleanup()

    def write(self, path: Path, data: dict) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_current_edition_satisfies_contract(self) -> None:
        validate_edition(self.valid)
        self.assertTrue(all(item.get("en") for item in self.valid["items"]), "every paper needs English copy")

    def test_invalid_edition_never_replaces_live_data(self) -> None:
        self.write(self.target, {"edition": 1, "sentinel": True})
        invalid = next_curated()
        for item in invalid["items"]:
            item["featured"] = False
        self.write(self.source, invalid)
        with self.assertRaises(ValueError):
            publish(self.source, self.target, self.history, online=False, manifest_path=self.manifest)
        self.assertEqual(json.loads(self.target.read_text(encoding="utf-8")), {"edition": 1, "sentinel": True})

    def test_missing_english_copy_blocks_publication(self) -> None:
        self.write(self.target, self.valid)
        invalid = next_curated()
        del invalid["items"][0]["en"]
        self.write(self.source, invalid)
        with self.assertRaises(ValueError):
            publish(self.source, self.target, self.history, online=False, manifest_path=self.manifest)
        self.assertEqual(json.loads(self.target.read_text(encoding="utf-8"))["edition"], self.valid["edition"])

    def test_valid_publish_is_atomic_and_keeps_backup(self) -> None:
        self.write(self.target, self.valid)
        self.write(self.source, next_curated())
        manifest = publish(self.source, self.target, self.history, online=False, manifest_path=self.manifest)
        published = json.loads(self.target.read_text(encoding="utf-8"))
        self.assertEqual(published["edition"], self.valid["edition"] + 1)
        self.assertEqual(published["updatedAt"], self.valid["updatedAt"])
        self.assertTrue((self.history / f"papers-{self.valid['updatedAt']}.json").exists())
        self.assertFalse(self.target.with_suffix(".json.tmp").exists())
        self.assertEqual(manifest["current"], self.valid["edition"] + 1)
        self.assertEqual([entry["edition"] for entry in manifest["editions"]], [self.valid["edition"] + 1, self.valid["edition"]])

    def test_edition_number_is_auto_assigned(self) -> None:
        self.write(self.target, self.valid)
        curated = next_curated()
        del curated["edition"]
        self.write(self.source, curated)
        manifest = publish(self.source, self.target, self.history, online=False, manifest_path=self.manifest)
        self.assertEqual(manifest["current"], self.valid["edition"] + 1)
        self.assertEqual(json.loads(self.target.read_text(encoding="utf-8"))["edition"], self.valid["edition"] + 1)

    def test_out_of_order_edition_is_rejected(self) -> None:
        self.write(self.target, self.valid)
        curated = next_curated()
        curated["edition"] = curated["edition"] + 3
        self.write(self.source, curated)
        with self.assertRaises(ValueError):
            publish(self.source, self.target, self.history, online=False, manifest_path=self.manifest)
        self.assertEqual(json.loads(self.target.read_text(encoding="utf-8"))["edition"], self.valid["edition"])

    def test_doi_network_failure_never_replaces_live_data(self) -> None:
        self.write(self.target, {"edition": 1, "sentinel": "last-live-edition"})
        self.write(self.source, next_curated())
        with patch("publish_weekly.verify_doi", side_effect=ValueError("simulated Crossref outage")):
            with self.assertRaises(ValueError):
                publish(self.source, self.target, self.history, online=True, manifest_path=self.manifest)
        self.assertEqual(json.loads(self.target.read_text(encoding="utf-8"))["sentinel"], "last-live-edition")
        self.assertFalse(self.manifest.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
