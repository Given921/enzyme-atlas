"""Verify the deployed site at the configured public address."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "EnzymeAtlasDeployCheck/1.0"})
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        return response.read()


ROOT = Path(__file__).resolve().parents[1]


def verify(base_url: str, edition: str | None, expected_classics: int) -> None:
    base = base_url.rstrip("/") + "/"
    homepage = fetch(base).decode("utf-8")
    classics_page = fetch(base + "classics.html").decode("utf-8")
    archive_page = fetch(base + "archive.html").decode("utf-8")
    runtime = fetch(base + "i18n.js").decode("utf-8")
    papers = json.loads(fetch(base + "data/papers.json"))
    classics = json.loads(fetch(base + "data/classics.json"))
    manifest = json.loads(fetch(base + "data/editions.json"))
    if "Enzyme Atlas" not in homepage or "本周精选" not in homepage:
        raise RuntimeError("public homepage content is incomplete")
    if "data-lang-slot" not in homepage or "data-lang-slot" not in classics_page:
        raise RuntimeError("public pages are missing the bilingual language switch")
    if "data-lang-option" not in runtime or "classicTopics" not in runtime:
        raise RuntimeError("public i18n runtime is incomplete")
    if "editionSwitcher" not in archive_page or "archiveDetail" not in archive_page:
        raise RuntimeError("public archive page is incomplete")
    public_classics = len(classics.get("items", []))
    if "经典" not in classics_page or public_classics != expected_classics:
        raise RuntimeError(f"public classics library has {public_classics} records, expected {expected_classics}")
    if edition and papers.get("updatedAt") != edition:
        raise RuntimeError(f"public edition is {papers.get('updatedAt')}, expected {edition}")
    if manifest.get("current") != papers.get("edition"):
        raise RuntimeError(f"public manifest edition {manifest.get('current')} does not match papers.json edition {papers.get('edition')}")
    editions = manifest.get("editions", [])
    if len(editions) < 2:
        raise RuntimeError(f"public archive lists only {len(editions)} edition(s)")
    for entry in editions:
        if not entry.get("path"):
            raise RuntimeError(f"archive entry {entry.get('edition')} has no data path")
        if entry["path"] != "data/papers.json":
            fetch(base + entry["path"])
    if not all(item.get("en") for item in papers.get("items", [])):
        raise RuntimeError("public weekly edition is missing English copy")
    if not all(item.get("en") for item in classics.get("items", [])):
        raise RuntimeError("public classics are missing English copy")
    print(
        f"PASS: public homepage, classics, archive and data are live at {base}; "
        f"edition={papers.get('updatedAt')} (#{papers.get('edition')}); classics={public_classics}; editions={len(editions)}"
    )


def resolve_base_url(explicit: str | None) -> str:
    """Use --base-url when given, otherwise read the address from site.config.json."""
    if explicit:
        return explicit
    config_path = ROOT / "site.config.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    url = (config.get("siteUrl") or "").strip()
    if not url:
        raise SystemExit(
            "no --base-url given and site.config.json has no siteUrl; "
            "run `python scripts/set_site_address.py --url https://<address>/` first"
        )
    return url


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", help="Public base address; defaults to site.config.json")
    parser.add_argument("--from-config", action="store_true", help="Read the address from site.config.json (default when --base-url is omitted)")
    parser.add_argument("--edition")
    parser.add_argument(
        "--classic-count",
        type=int,
        default=len(json.loads((ROOT / "data" / "classics.json").read_text(encoding="utf-8"))["items"]),
        help="Expected number of published classic records (defaults to the checked-out data file).",
    )
    parser.add_argument("--attempts", type=int, default=12)
    parser.add_argument("--delay", type=int, default=10)
    args = parser.parse_args()
    base_url = resolve_base_url(args.base_url)
    last_error: Exception | None = None
    for attempt in range(args.attempts):
        try:
            verify(base_url, args.edition, args.classic_count)
            return
        except (RuntimeError, HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            if attempt + 1 < args.attempts:
                time.sleep(args.delay)
    raise RuntimeError(f"public site verification failed after {args.attempts} attempts: {last_error}")


if __name__ == "__main__":
    main()

