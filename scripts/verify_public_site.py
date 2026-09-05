"""Verify the GitHub Pages edition after deployment."""
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
    papers = json.loads(fetch(base + "data/papers.json"))
    classics = json.loads(fetch(base + "data/classics.json"))
    if "Enzyme Atlas" not in homepage or "本周精选" not in homepage:
        raise RuntimeError("public homepage content is incomplete")
    public_classics = len(classics.get("items", []))
    if "经典" not in classics_page or public_classics != expected_classics:
        raise RuntimeError(f"public classics library has {public_classics} records, expected {expected_classics}")
    if edition and papers.get("updatedAt") != edition:
        raise RuntimeError(f"public edition is {papers.get('updatedAt')}, expected {edition}")
    print(
        f"PASS: public homepage, classics and data are live at {base}; "
        f"edition={papers.get('updatedAt')}; classics={public_classics}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
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
    last_error: Exception | None = None
    for attempt in range(args.attempts):
        try:
            verify(args.base_url, args.edition, args.classic_count)
            return
        except (RuntimeError, HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            if attempt + 1 < args.attempts:
                time.sleep(args.delay)
    raise RuntimeError(f"public site verification failed after {args.attempts} attempts: {last_error}")


if __name__ == "__main__":
    main()

