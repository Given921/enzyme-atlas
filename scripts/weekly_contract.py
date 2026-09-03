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
PLACEHOLDERS = ("等待编辑", "自动收录", "待审核", "TODO", "TBD")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_edition(data: dict) -> None:
    for key in ("updatedAt", "periodStart", "periodEnd", "source", "observations", "items"):
        if not data.get(key):
            raise ValueError(f"edition missing {key}")
    items = data["items"]
    if not isinstance(items, list) or not items:
        raise ValueError("edition must contain at least one paper")
    featured_count = sum(bool(item.get("featured")) for item in items)
    if not 3 <= featured_count <= 5:
        raise ValueError(f"featured count must be 3–5, got {featured_count}")
    if len(data["observations"]) != 3 or not all(str(value).strip() for value in data["observations"]):
        raise ValueError("edition must contain exactly three non-empty editorial observations")
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
