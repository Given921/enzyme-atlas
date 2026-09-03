"""Validate and atomically publish one editorially curated weekly edition."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from weekly_contract import load_json, validate_edition

ROOT = Path(__file__).resolve().parents[1]


def verify_doi(item: dict) -> str:
    request = Request(
        f"https://api.crossref.org/works/{quote(item['doi'], safe='')}",
        headers={"User-Agent": "EnzymeAtlas/1.0"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            message = json.load(response)["message"]
    except (HTTPError, URLError, TimeoutError) as error:
        raise ValueError(f"DOI verification failed for {item['doi']}: {error}") from error
    if message.get("DOI", "").lower() != item["doi"].lower():
        raise ValueError(f"Crossref DOI mismatch for {item['doi']}")
    relation = message.get("relation") or {}
    relation_text = json.dumps(relation, ensure_ascii=False).lower()
    if "retract" in relation_text:
        raise ValueError(f"retraction relation detected for {item['doi']}; publication stopped")
    if "correct" in relation_text and "更正" not in str(item.get("verification", "")):
        raise ValueError(f"correction relation for {item['doi']} is not disclosed in verification")
    return item["doi"]


def publish(source: Path, target: Path, history_dir: Path, online: bool) -> None:
    data = load_json(source)
    validate_edition(data)
    if online:
        for item in data["items"]:
            verify_doi(item)

    target.parent.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        previous = load_json(target)
        previous_date = previous.get("updatedAt", "unknown")
        backup = history_dir / f"papers-{previous_date}.json"
        if not backup.exists():
            shutil.copy2(target, backup)

    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path, help="Editorially curated edition JSON.")
    parser.add_argument("--online", action="store_true", help="Resolve DOI and inspect correction/retraction relations.")
    parser.add_argument("--target", type=Path, default=ROOT / "data" / "papers.json")
    parser.add_argument("--history-dir", type=Path, default=ROOT / "data" / "history")
    args = parser.parse_args()
    source = args.input if args.input.is_absolute() else ROOT / args.input
    target = args.target if args.target.is_absolute() else ROOT / args.target
    history_dir = args.history_dir if args.history_dir.is_absolute() else ROOT / args.history_dir
    if source.resolve() == target.resolve():
        raise ValueError("input must be a staging file, not the published data file")
    publish(source, target, history_dir, args.online)
    data = load_json(target)
    print(f"Published {len(data['items'])} papers ({sum(bool(p['featured']) for p in data['items'])} featured) for {data['updatedAt']}")


if __name__ == "__main__":
    main()
