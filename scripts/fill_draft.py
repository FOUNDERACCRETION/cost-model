"""Rewrite every tagged model number in the paper draft from results/key_numbers.json.

A tagged number is VALUE immediately followed by an HTML comment `k:KEY`, e.g. `$3,625` then the tag for
`l2_B`. Run scripts/stage2.py first, then: uv run python scripts/fill_draft.py [--check]
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFT = ROOT / "paper" / "p1-full-draft.md"
KEYS = ROOT / "results" / "key_numbers.json"

NUMBER = r"\$?[\d,]*\.?\d+%?(?:–\$?[\d,]*\.?\d+%?)?(?:,000)?"
TAG = re.compile(rf"(?P<val>{NUMBER})<!--k:(?P<key>\w+)-->")


def tags(text: str) -> list[tuple[str, str]]:
    return [(m.group("val"), m.group("key")) for m in TAG.finditer(text)]


def fill(text: str, keys: dict) -> str:
    def sub(m):
        if m.group("key") not in keys:
            raise KeyError(f"draft tag {m.group('key')} is not in {KEYS.name}")
        return keys[m.group("key")] + f"<!--k:{m.group('key')}-->"
    return TAG.sub(sub, text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report drift without writing")
    args = ap.parse_args()
    keys = json.loads(KEYS.read_text())
    text = DRAFT.read_text()
    drift = [(v, k, keys.get(k)) for v, k in tags(text) if keys.get(k) != v]
    for v, k, new in drift:
        print(f"{k}: draft {v} -> model {new}")
    if not args.check and drift:
        DRAFT.write_text(fill(text, keys))
    print(f"{len(tags(text))} tagged numbers, {len(drift)} {'drifted' if args.check else 'updated'}")
    sys.exit(1 if args.check and drift else 0)


if __name__ == "__main__":
    main()
