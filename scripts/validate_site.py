"""Static acceptance checks for the Enzyme Atlas prototype."""
from __future__ import annotations
import argparse
import datetime as dt
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from weekly_contract import validate_edition

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--online", action="store_true", help="Verify every DOI against the Crossref API.")
args = parser.parse_args()
data = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))
items = data["items"]
validate_edition(data)
classics_data = json.loads((ROOT / "data" / "classics.json").read_text(encoding="utf-8"))
classics = classics_data["items"]
assert items, "no papers"
assert 3 <= sum(bool(p["featured"]) for p in items) <= 5, "featured count must be 3–5"
edition_date = dt.date.fromisoformat(data["updatedAt"])
period_start = dt.date.fromisoformat(data["periodStart"])
period_end = dt.date.fromisoformat(data["periodEnd"])
assert edition_date.weekday() == 0, "weekly edition must be dated Monday"
assert edition_date == period_end and period_start <= period_end, "invalid edition period"
assert data["source"] != "curated_seed", "weekly edition still uses seed data"
assert len(data.get("observations", [])) == 3, "weekly observations are missing"
for p in items:
    for key in ("title", "cn", "doi", "url", "why", "evidence", "audience", "minutes", "labels", "verification"):
        assert p.get(key), f"{p.get('id')} missing {key}"
    assert p["url"] == f"https://doi.org/{p['doi']}", f"{p['id']} has non-DOI URL"
    assert period_start <= dt.date.fromisoformat(p["date"]) <= period_end, f"{p['id']} is outside the weekly window"
    assert "等待编辑" not in json.dumps(p, ensure_ascii=False), f"{p['id']} still contains automatic placeholder copy"
source_minimums = {
    "Nature 正刊": 7,
    "Science 正刊": 5,
    "Cell 正刊": 5,
    "Nature 子刊": 12,
    "其他精选": 8,
}
assert len(classics) >= 50, "classic library must contain at least 50 records"
assert len({c["doi"].lower() for c in classics}) == len(classics), "duplicate DOI in classic library"
for source_group, minimum in source_minimums.items():
    count = sum(c["sourceGroup"] == source_group for c in classics)
    assert count >= minimum, f"{source_group} has only {count} records"
assert sum(c["sourceGroup"] == "其他精选" for c in classics) / len(classics) <= 0.35, "other journals are no longer a minority"
for c in classics:
    for key in ("topic", "year", "title", "authors", "journal", "sourceGroup", "kind", "note", "doi"):
        assert c.get(key), f"classic record missing {key}: {c.get('title')}"
    if c["sourceGroup"] == "Nature 正刊":
        assert c["journal"] == "Nature", f"Nature main-journal mismatch: {c['title']}"
    if c["sourceGroup"] == "Science 正刊":
        assert c["journal"] == "Science", f"Science main-journal mismatch: {c['title']}"
    if c["sourceGroup"] == "Cell 正刊":
        assert c["journal"] == "Cell", f"Cell main-journal mismatch: {c['title']}"
if args.online:
    def verify_crossref(record):
        request = Request(f"https://api.crossref.org/works/{quote(record['doi'], safe='')}", headers={"User-Agent": "EnzymeAtlas/0.3 (mailto:maintainer@example.org)"})
        try:
            with urlopen(request, timeout=30) as response:
                message = json.load(response)["message"]
        except (HTTPError, URLError) as error:
            raise AssertionError(f"Crossref lookup failed for {record['doi']} ({record['title']}): {error}") from error
        assert message["DOI"].lower() == record["doi"].lower(), f"Crossref DOI mismatch: {record['doi']}"
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(verify_crossref, [*items, *classics]))
index = (ROOT / "index.html").read_text(encoding="utf-8")
app = (ROOT / "app.js").read_text(encoding="utf-8")
search = (ROOT / "search.js").read_text(encoding="utf-8")
classics_js = (ROOT / "classics.js").read_text(encoding="utf-8")
for required in ("observationGrid", "subscriptionTopics", "每周一更新", "editionSummary", "intent-strip", "本期全部收录"):
    assert required in index, f"missing {required}"
for prohibited in ("每日更新", "每日推送", "每周文献雷达", "编辑筛选后发布", "了解筛选方法", "48篇"):
    assert prohibited not in index, f"homepage contains prohibited copy: {prohibited}"
for prohibited in ("setFilter(", "classicBtn", "weeklyCount"):
    assert prohibited not in app, f"stale runtime reference: {prohibited}"
for required in ("exportSaved", "quick-grid", "fetch('data/papers.json')", "function move(id, kind)", "subscriptionTopics", "renderEdition", "item.summary", "隐藏"):
    assert required in app, f"missing interaction: {required}"
assert "fetch('data/papers.json')" in search and "p.url" in search, "search is not using the shared real-DOI data"
for required in ("fetch('data/classics.json')", "sourceOrder", "doiUrl", "打开 DOI / 出版社页面"):
    assert required in classics_js, f"classic library missing {required}"
styles = (ROOT / "styles.css").read_text(encoding="utf-8")
for required in ("--ink: #0d0d0d", "--paper: #f7f7f5", ".intent-strip", ".site-footer", "height: 153px"):
    assert required in styles, f"missing design contract: {required}"
for page in ("search.html", "classics.html", "topics.html"):
    html = (ROOT / page).read_text(encoding="utf-8")
    assert "subpage-hero" in html and "site-footer" in html, f"{page} is not using the shared design system"
fetcher = (ROOT / "scripts" / "fetch_crossref.py").read_text(encoding="utf-8")
assert "OUT =" not in fetcher and "OUT.write_text" not in fetcher, "candidate collector still writes directly to the published data file"
assert "data/staging" in (ROOT / ".gitignore").read_text(encoding="utf-8"), "staging data is not excluded from release commits"
assert (ROOT / ".github" / "workflows" / "pages.yml").exists(), "GitHub Pages workflow is missing"
online_note = "; Crossref DOI verification passed" if args.online else ""
print(f"PASS: {len(items)} weekly real-DOI records; {sum(bool(p['featured']) for p in items)} featured; {len(classics)} DOI-linked classics; UI contracts valid{online_note}")
