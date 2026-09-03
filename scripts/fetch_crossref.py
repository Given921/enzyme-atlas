"""Collect weekly Crossref candidates without touching the published edition.

The collector is deliberately separated from publishing. It writes only to
``data/staging`` (or an explicit ``--output`` path); ``data/papers.json`` is
updated exclusively by ``publish_weekly.py`` after editorial and validation.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
KEYWORDS = (
    "enzyme", "enzymatic", "biocatal", "protein engineering",
    "directed evolution", "enzyme cascade", "protein design",
    "protein language model",
)
QUERIES = (
    "enzyme engineering",
    "biocatalysis",
    "directed evolution enzyme",
    "multi-enzyme cascade",
    "enzyme cascade assembly",
    "enzyme immobilization",
    "fusion enzyme",
    "computational enzyme design",
    "protein language model enzyme",
)


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(value or ""))).strip()


def edition_monday(value: dt.date) -> dt.date:
    """Return the Monday edition date on or before *value*."""
    return value - dt.timedelta(days=value.weekday())


def topic_for(text: str) -> str:
    text = text.lower()
    rules = [
        ("immobil", "酶固定化与酶—材料体系"),
        ("scaffold|assembly|spatial", "酶的级联组装"),
        ("fusion", "融合酶与多功能酶"),
        ("cascade|cofactor", "多酶级联反应"),
        ("machine learning|artificial intelligence|deep learning|language model", "AI 与机器学习辅助酶研究"),
        ("structure|cryo|molecular dynamics", "酶的结构与催化机制"),
        ("specificity|selectivity|promiscu", "酶动力学、选择性与底物特异性"),
        ("stability|thermo", "酶的稳定性工程"),
    ]
    for pattern, topic in rules:
        if re.search(pattern, text):
            return topic
    return "定向进化与理性设计"


def fetch_query(search_term: str, start: dt.date, end: dt.date) -> list[dict]:
    query = urlencode({
        "query.bibliographic": search_term,
        "filter": f"from-pub-date:{start},until-pub-date:{end},type:journal-article",
        "sort": "published",
        "order": "desc",
        "rows": 50,
    })
    request = Request(
        f"https://api.crossref.org/works?{query}",
        headers={"User-Agent": "EnzymeAtlas/1.0"},
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)["message"]["items"]
        except (HTTPError, URLError, TimeoutError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Crossref query failed after 3 attempts: {search_term}: {last_error}")


def normalize(item: dict, fallback_date: dt.date) -> dict | None:
    title = clean((item.get("title") or [""])[0])
    abstract = clean(item.get("abstract", ""))
    searchable = f"{title} {abstract}".lower()
    if not title or not any(key in searchable for key in KEYWORDS):
        return None
    authors = item.get("author", [])
    author_text = (
        authors[0].get("family", "Unknown") + (" et al." if len(authors) > 1 else "")
        if authors else "Unknown"
    )
    date_parts = item.get("published", {}).get(
        "date-parts", [[fallback_date.year, fallback_date.month, fallback_date.day]]
    )[0]
    date = "-".join(str(v).zfill(2) for v in (date_parts + [1, 1])[:3])
    doi = item.get("DOI", "").strip()
    if not doi:
        return None
    return {
        "id": doi.lower().replace("/", "-"),
        "title": title,
        "authors": author_text,
        "journal": clean((item.get("container-title") or ["Unknown journal"])[0]),
        "date": date,
        "topicSuggestion": topic_for(searchable),
        "typeSuggestion": "review" if item.get("subtype") == "review" else "original",
        "doi": doi,
        "url": f"https://doi.org/{doi}",
        "abstract": abstract,
        "crossrefRelation": item.get("relation") or {},
        "publisher": clean(item.get("publisher", "")),
    }


def atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Fetch and print a summary; write no files.")
    parser.add_argument("--as-of", type=dt.date.fromisoformat, help="Cutoff date; normalized to its Monday edition.")
    parser.add_argument("--output", type=Path, help="Candidate JSON path; defaults under data/staging.")
    parser.add_argument("--show-candidates", action="store_true", help="Print normalized candidates as JSON.")
    parser.add_argument("--compact", action="store_true", help="Print one line per candidate.")
    parser.add_argument("--doi", action="append", help="Limit review output to one or more DOI values.")
    args = parser.parse_args()

    edition = edition_monday(args.as_of or dt.date.today())
    period_start = edition - dt.timedelta(days=7)
    items_by_doi: dict[str, dict] = {}
    for search_term in QUERIES:
        for item in fetch_query(search_term, period_start, edition):
            doi = item.get("DOI", "").lower()
            if doi:
                items_by_doi[doi] = item

    records = [record for item in items_by_doi.values() if (record := normalize(item, edition))]
    records = [record for record in records if period_start <= dt.date.fromisoformat(record["date"]) <= edition]
    records.sort(key=lambda record: (record["date"], record["doi"]), reverse=True)
    if args.doi:
        requested_dois = {doi.lower() for doi in args.doi}
        records = [record for record in records if record["doi"].lower() in requested_dois]
    if not records:
        raise RuntimeError("No enzyme-focused candidates found; published data was left unchanged.")

    payload = {
        "editionDate": str(edition),
        "periodStart": str(period_start),
        "periodEnd": str(edition),
        "source": "crossref_candidates",
        "queries": list(QUERIES),
        "candidateCount": len(records),
        "items": records,
    }
    print(f"Collected {len(records)} candidates for {period_start} through {edition}.")
    if args.compact:
        for record in records:
            print(f'{record["date"]}\t{record["doi"]}\t{record["journal"]}\t{record["title"]}')
    elif args.show_candidates:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    if args.dry_run:
        print("Dry run: no files were written and data/papers.json was not touched.")
        return
    output = args.output or ROOT / "data" / "staging" / f"candidates-{edition}.json"
    if not output.is_absolute():
        output = ROOT / output
    staging_root = (ROOT / "data" / "staging").resolve()
    published = (ROOT / "data" / "papers.json").resolve()
    if output.resolve() == published:
        raise ValueError("Candidate output may not be data/papers.json; use publish_weekly.py after editorial review.")
    if not output.resolve().is_relative_to(staging_root):
        raise ValueError("Candidate output must stay under data/staging.")
    atomic_write(output, payload)
    print(f"Wrote editorial candidates to {output}")


if __name__ == "__main__":
    main()
