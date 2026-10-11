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


def test_no_stale_overhead_figures():
    """Values from before the effective-rate fix (negotiated 58% as base) must not survive untagged."""
    text = DRAFT.read_text()
    for stale in ("$3,794", "$3,765 / $3,897", "$3,722", "$2,751", "$65,403", "$5,186", "within 3%", "21 to 119"):
        assert stale not in text, stale
