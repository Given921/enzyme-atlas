"""Shared schema and safety checks for a publishable Enzyme Atlas edition."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

REQUIRED_ITEM_FIELDS = (
    "id", "title", "cn", "authors", "journal", "date", "topic", "type",
    "doi", "url", "summary", "why", "evidence", "audience", "minutes",
    "labels", "verification",
)
# Bilingual editions: every paper carries an inline `en` object with the same
# editorial prose, so the English site never falls back to Chinese copy.
REQUIRED_EN_ITEM_FIELDS = ("summary", "why", "evidence", "audience", "verification")
PLACEHOLDERS = ("等待编辑", "自动收录", "待审核", "TODO", "TBD")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_edition(data: dict) -> None:
    for key in ("updatedAt", "periodStart", "periodEnd", "source", "observations", "items"):
        if not data.get(key):
            raise ValueError(f"edition missing {key}")
    edition_number = data.get("edition")
    if not isinstance(edition_number, int) or edition_number < 1:
        raise ValueError(f"edition must be a positive integer, got {edition_number!r}")
    items = data["items"]
    if not isinstance(items, list) or not items:
        raise ValueError("edition must contain at least one paper")
    featured_count = sum(bool(item.get("featured")) for item in items)
    if not 3 <= featured_count <= 5:
        raise ValueError(f"featured count must be 3–5, got {featured_count}")
    if len(data["observations"]) != 3 or not all(str(value).strip() for value in data["observations"]):
        raise ValueError("edition must contain exactly three non-empty editorial observations")
    observations_en = data.get("observationsEn")
    if not isinstance(observations_en, list) or len(observations_en) != 3:
        raise ValueError("edition must contain exactly three English editorial observations (observationsEn)")
    if any(not isinstance(entry, list) or len(entry) != 2 or not all(str(part).strip() for part in entry) for entry in observations_en):
        raise ValueError("every observationsEn entry must be a non-empty [title, body] pair")
    edition_date = dt.date.fromisoformat(data["updatedAt"])
    period_start = dt.date.fromisoformat(data["periodStart"])
    period_end = dt.date.fromisoformat(data["periodEnd"])
    if edition_date.weekday() != 0:
        raise ValueError("weekly edition date must be Monday")
    if edition_date != period_end or period_start > period_end:
        raise ValueError("invalid edition period")
    if data["source"] in {"curated_seed", "crossref_candidates"}:
        raise ValueError("candidate or seed data cannot be published")

    dois: set[str] = set()
    for item in items:
        missing = [key for key in REQUIRED_ITEM_FIELDS if not item.get(key)]
        if missing:
            raise ValueError(f"{item.get('id', '<unknown>')} missing {', '.join(missing)}")
        doi = item["doi"].lower()
        if doi in dois:
            raise ValueError(f"duplicate DOI: {item['doi']}")
        dois.add(doi)
        if item["url"] != f"https://doi.org/{item['doi']}":
            raise ValueError(f"{item['id']} has a non-canonical DOI URL")
        item_date = dt.date.fromisoformat(item["date"])
        if not period_start <= item_date <= period_end:
            raise ValueError(f"{item['id']} is outside the weekly period")
        serialized = json.dumps(item, ensure_ascii=False)
        if any(marker.lower() in serialized.lower() for marker in PLACEHOLDERS):
            raise ValueError(f"{item['id']} contains an editorial placeholder")
        if not isinstance(item["labels"], list) or not item["labels"]:
            raise ValueError(f"{item['id']} labels must be a non-empty list")
        if not isinstance(item["minutes"], int) or item["minutes"] <= 0:
            raise ValueError(f"{item['id']} minutes must be a positive integer")
        english = item.get("en")
        if not isinstance(english, dict):
            raise ValueError(f"{item['id']} is missing its inline English copy (en)")
        missing_en = [key for key in REQUIRED_EN_ITEM_FIELDS if not str(english.get(key, "")).strip()]
        if missing_en:
            raise ValueError(f"{item['id']} missing English {', '.join(missing_en)}")


def build_editions_manifest(current: dict, history_dir: Path) -> dict:
    """Builds data/editions.json from the published edition plus archived history files."""
    entries: list[dict] = []

    def describe(data: dict, path: str) -> dict:
        featured = [item for item in data["items"] if item.get("featured")]
        lead = featured[0] if featured else data["items"][0]
        return {
            "edition": data["edition"],
            "updatedAt": data["updatedAt"],
            "periodStart": data["periodStart"],
            "periodEnd": data["periodEnd"],
            "itemCount": len(data["items"]),
            "featuredCount": len(featured),
            "headline": lead["cn"],
            "en": {"headline": lead["title"]},
            "path": path,
        }

    entries.append(describe(current, "data/papers.json"))
    for archive in sorted(history_dir.glob("papers-*.json")):
        data = load_json(archive)
        if data.get("edition") == current["edition"]:
            # Same edition as the live file (e.g. a re-publish); never list it twice.
            continue
        if not isinstance(data.get("edition"), int):
            raise ValueError(f"{archive.name} has no edition number; cannot archive it")
        entries.append(describe(data, f"data/history/{archive.name}"))
    entries.sort(key=lambda entry: entry["edition"], reverse=True)
    known = [entry["edition"] for entry in entries]
    if len(set(known)) != len(known):
        raise ValueError(f"duplicate edition numbers in archive: {known}")
    return {"updatedAt": current["updatedAt"], "current": current["edition"], "editions": entries}
