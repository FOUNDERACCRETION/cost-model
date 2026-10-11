#!/usr/bin/env python3
"""Check every number printed in a manuscript against the model's generated figures.

Four transcription errors reached revision 12 of the paper and none was caught by rereading:
P(B < A) printed as 99.5% in five places against the generator's 99.4%, a level-2 overlap of 98%
against 99%, a tornado share of 98.8% against 98.6%, and a title page still reading "revision 10"
in revision 11. Each was a number read off an earlier run and retyped. Prose review does not find
these, so this check exists and belongs in the build rather than in someone's scratch directory.

What it does, in two directions:

  DRIFT     every value in results/key_numbers.json that the manuscript ought to contain but does
            not appear verbatim. A hit is not automatically an error -- a key the paper
            deliberately does not quote shows up here too -- so keys may be waived by listing
            them in paper/audit-waivers.txt with a reason.

  ORPHANS   percentages and dollar amounts in the manuscript that match no generated key. These
            are hand-written figures. They may be perfectly correct (arithmetic in prose, a figure
            from a cited source) but each one is a number no test guards, so the count is reported
            and can be held to a ceiling.

Exit status is nonzero when an unwaived key is missing, so CI fails on drift.

Run: python scripts/audit_numbers.py paper/p1-revision13.md
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WAIVERS = ROOT / "paper" / "audit-waivers.txt"


def normalise(s: str) -> str:
    """Strip the formatting that differs between the generator and the manuscript.

    The manuscript is pandoc markdown, so dollar signs are backslash-escaped and en dashes are
    written as `--`; the generator emits plain text with real dashes. Comparing without
    normalising produces false hits on nearly every currency figure.
    """
    return (s.replace("\\", "").replace("$", "").replace(",", "")
             .replace("\u2013", "-").replace("\u2014", "-").replace("--", "-")
             .replace("\u00d7", "x").strip())


def load_waivers() -> dict:
    out = {}
    if WAIVERS.exists():
        for line in WAIVERS.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, _, reason = line.partition(":")
            out[name.strip()] = reason.strip() or "no reason given"
    return out


_WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
             "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
             "fourteen": 14, "fifteen": 15, "sixteen": 16}


def _census_states(body: str, keys: dict) -> bool:
    """True when the manuscript's evidence-grade sentence agrees with the generated census.

    The sentence writes some counts as numerals and some as words ("eight `proxy`, five
    `assumption`"), so both spellings are accepted. Every grade with a nonzero count must appear
    beside its own grade name, and the total beside the word "parameters".
    """
    ok = True
    for name, value in keys.items():
        if not name.startswith("grade_"):
            continue
        grade = name[len("grade_"):]
        n = int(str(value).replace(",", ""))
        word = next((w for w, v in _WORD_NUM.items() if v == n), None)
        forms = [str(n)] + ([word] if word else [])
        if grade == "total":
            hit = any(re.search(rf"\b{f}\s+parameters\b", body) for f in forms)
        else:
            # The sentence reads "46 are `published`, 15 `first_hand`, ...", so a connector verb
            # may sit between the count and the grade name on the first item only.
            hit = any(re.search(rf"\b{f}\s+(?:are\s+|is\s+)?`?{grade}`?", body) for f in forms)
        ok = ok and hit
    return ok


def audit(papers: list[Path], keys_path: Path) -> int:
    # Several files, because the manuscript is split into a main document and a companion holding
    # the appendices and supplements. A figure counts as present if it appears in ANY of them: the
    # check is that no generated figure is stranded, not that it sits in a particular file.
    if isinstance(papers, Path):
        papers = [papers]
    text = "\n".join(p.read_text() for p in papers)
    paper = papers[0]
    keys = json.loads(keys_path.read_text())
    waived = load_waivers()
    body = normalise(text)

    missing, waived_hits = [], []
    for name in sorted(keys):
        value = normalise(str(keys[name]))
        # Skip values too short or too generic to match meaningfully: a bare "0" or a yes/no flag
        # would match somewhere in any document and tell us nothing.
        #
        # The grade census is the exception. Its values are one- and two-digit counts, so the
        # length rule skipped them -- which is how the manuscript came to claim 88 parameters and
        # 14 first-hand ones after the count had moved to 89 and 15. Those are checked against the
        # sentence that states them rather than against the whole document, since a bare "46"
        # matches almost anything.
        if name.startswith("grade_"):
            if not _census_states(body, keys):
                missing.append((name, keys[name]))
            continue
        if len(value) < 3 or value in ("yes", "no"):
            continue
        if value in body:
            continue
        (waived_hits if name in waived else missing).append((name, keys[name]))

    print(f"{', '.join(p.name for p in papers)}: {len(keys)} generated keys")
    print(f"  {len(missing)} MISSING (in the model, not in the paper, not waived)")
    for name, value in missing:
        print(f"     {name} = {value}")
    print(f"  {len(waived_hits)} waived")

    # Orphans: figures in the manuscript that no key accounts for. LaTeX math is stripped first:
    # an inline $...$ span makes the dollar-amount pattern match fragments of equations, which
    # inflates the count with things that are not figures at all.
    quoted = {normalise(str(v)) for v in keys.values()}
    prose = re.sub(r"\$\$.*?\$\$", " ", text, flags=re.S)
    prose = re.sub(r"(?<!\\)\$(?!\s)[^$\n]{1,200}?(?<!\\)\$", " ", prose)
    found = re.findall(r"\\\$[\d,]+(?:\.\d+)?|\d+(?:\.\d+)?%", prose)
    orphans = sorted({f for f in found if normalise(f) not in quoted})
    print(f"  {len(orphans)} hand-written figures matching no key")
    if orphans:
        print("     " + ", ".join(orphans[:40]) + (" ..." if len(orphans) > 40 else ""))

    if missing:
        print("\nFAIL: a generated figure is absent from the manuscript. Either the manuscript is")
        print("stale, or the key is one the paper does not quote -- in which case add it to")
        print("paper/audit-waivers.txt with a reason.")
        return 1
    print("\nOK: every unwaived generated figure appears in the manuscript.")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    papers = []
    for arg in sys.argv[1:]:
        q = Path(arg)
        papers.append(q if q.is_absolute() else ROOT / q)
    return audit(papers, ROOT / "results" / "key_numbers.json")


if __name__ == "__main__":
    raise SystemExit(main())
