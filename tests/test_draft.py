"""Every tagged model number in the paper draft matches results/key_numbers.json."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from fill_draft import DRAFT, KEYS, fill, tags  # noqa: E402


def test_tagged_numbers_match_model():
    keys = json.loads(KEYS.read_text())
    found = tags(DRAFT.read_text())
    assert len(found) > 100, "draft has lost its number tags"
    unknown = sorted({k for _, k in found if k not in keys})
    assert not unknown, f"draft tags not in {KEYS.name}: {unknown}"
    drift = [(k, v, keys[k]) for v, k in found if keys[k] != v]
    assert not drift, f"draft numbers drifted from the model (run scripts/fill_draft.py): {drift}"


def test_every_tag_is_parsed():
    """A tag whose preceding value the parser cannot read would silently escape the check."""
    text = DRAFT.read_text()
    assert len(re.findall(r"<!--k:\w+-->", text)) == len(tags(text))


def test_fill_is_idempotent():
    keys = json.loads(KEYS.read_text())
    text = DRAFT.read_text()
    assert fill(text, keys) == text


CURRENT = DRAFT.parent / "p1-revision7.md"


def test_current_manuscript_exists():
    assert CURRENT.exists(), "paper/p1-revision7.md is the current manuscript"


def test_no_stale_overhead_figures():
    """Values from before the effective-rate fix (negotiated 58% as base) must not survive untagged."""
    text = CURRENT.read_text()
    # Figures superseded by the 2026-10-11 repairs (unconditional success; matched indirect base).
    # "within 3%" is deliberately NOT listed: the repaired model gives a 3% spread again.
    for stale in ("$3,794", "$3,765 / $3,897", "$3,722", "$2,751", "$65,403", "$5,186", "21 to 119",
                  "$3,653", "$3,625", "$3,756", "$3,581", "$213 per attempt", "20 to 114", "20 to 83",
                  "38/54", "38 of 54", "given the DFT verdict is right",
                  # withdrawn in revision 7: w cancels out of level 2
                  "Verification accuracy is the computational lever",
                  "26 to 136 times weaker", "each target is charged six attempts",
                  "controlled on the model dimension"):
        assert stale not in text, stale
