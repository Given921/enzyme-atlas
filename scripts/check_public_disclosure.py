"""Fail the build if a published file leaks a private-name or host-brand token.

The site must never display a personal account name or a hosting brand marker in
its output. This guard walks every tracked file and looks for tokens that should
not be there.

Tokens come from three places, in order of precedence:

  1. ``site.config.json`` -> ``disclosure.denyTokens`` (explicit, committed list)
  2. the local, git-ignored policy file (``disclosure.localPolicy``) so a token
     can be enforced without ever being written into the repository
  3. the repository owner parsed from ``git remote get-url origin`` - this makes
     the personal-name rule work everywhere, including a fresh CI checkout

Run it directly::

    python scripts/check_public_disclosure.py
    python scripts/check_public_disclosure.py --root . --verbose
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "site.config.json"

BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz",
    ".woff", ".woff2", ".ttf", ".otf", ".mp4", ".mov", ".xlsx", ".docx", ".pptx",
}
# files whose whole purpose is to name the tokens, so they are never scanned
SELF_REFERENTIAL = {
    "scripts/check_public_disclosure.py",
    "scripts/disclosure.policy.example.json",
}


def mask_token(token: str) -> str:
    """Render a token so it is recognisable in logs without being restated."""
    if len(token) <= 2:
        return token[0] + "*"
    return token[0] + "*" * (len(token) - 2) + token[-1]


def _git(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=20
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_remote_owner() -> str | None:
    url = _git("remote", "get-url", "origin")
    if not url:
        return None
    match = re.search(r"(?:github\.com[:/])([^/]+)/", url)
    return match.group(1) if match else None


def load_local_policy(config: dict) -> list[str]:
    rel = (config.get("disclosure") or {}).get("localPolicy") or "scripts/disclosure.local.json"
    path = ROOT / rel
    if not path.exists():
        return []
    try:
        return list(json.loads(path.read_text(encoding="utf-8")).get("denyTokens") or [])
    except (json.JSONDecodeError, OSError):
        return []


def active_deny_tokens(config: dict | None = None) -> list[str]:
    """Every token that must not appear in a published file."""
    if config is None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.exists() else {}
    disclosure = config.get("disclosure") or {}
    raw: list[str] = []
    raw += list(disclosure.get("denyTokens") or [])
    raw += load_local_policy(config)
    if disclosure.get("deriveOwnerFromGitRemote", True):
        owner = git_remote_owner()
        if owner:
            raw.append(owner)
    # publisher / contactEmail are intentionally public, so they are never denied
    seen: list[str] = []
    for token in raw:
        token = (token or "").strip()
        if not token:
            continue
        minimum = 2 if not token.isascii() else 4
        if len(token) < minimum:
            continue
        if token.lower() not in {existing.lower() for existing in seen}:
            seen.append(token)
    return seen


def tracked_files(root: Path) -> list[Path]:
    # cached = tracked, others+exclude-standard = new files that would be committed
    listed = _git("ls-files", "--cached", "--others", "--exclude-standard")
    if listed:
        return [root / name for name in listed.splitlines() if (root / name).is_file()]
    return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]


def is_scannable(path: Path, root: Path) -> bool:
    if path.suffix.lower() in BINARY_SUFFIXES:
        return False
    if path.relative_to(root).as_posix() in SELF_REFERENTIAL:
        return False
    try:
        head = path.read_bytes()[:4096]
    except OSError:
        return False
    return b"\x00" not in head


def scan(root: Path, tokens: list[str]) -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    lowered = [(t, t.lower()) for t in tokens]
    for path in tracked_files(root):
        if not is_scannable(path, root):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for number, line in enumerate(lines, start=1):
            low = line.lower()
            for original, needle in lowered:
                if needle in low:
                    findings.append((rel, number, mask_token(original)))
    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--verbose", action="store_true", help="List the masked tokens under enforcement")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    tokens = active_deny_tokens()
    if args.verbose:
        print("active disclosure tokens: " + (", ".join(mask_token(t) for t in tokens) or "none"))
    if not tokens:
        print("PASS: no disclosure tokens configured; nothing to enforce")
        return

    findings = scan(root, tokens)
    if findings:
        print(f"FAIL: {len(findings)} disclosure leak(s) found:")
        for rel, number, masked in findings:
            print(f"  {rel}:{number}  contains {masked}")
        sys.exit(1)
    print(f"PASS: {len(tokens)} disclosure token(s) absent from every tracked file")


if __name__ == "__main__":
    main()
