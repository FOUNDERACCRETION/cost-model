"""Read paper/references.bib, the single source of bibliographic truth for parameters and the draft."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "paper" / "references.bib"

ENTRY = re.compile(r"^@(\w+)\s*\{\s*([^,\s]+)\s*,", re.M)


def keys(path: Path = BIB) -> list[str]:
    """Citation keys of every entry, in file order."""
    return [m.group(2) for m in ENTRY.finditer(Path(path).read_text(encoding="utf-8"))]


def entries(path: Path = BIB) -> dict[str, dict]:
    """{key: {"type": ..., field: value}} with brace-balanced field values (enough for checks, not a full parser)."""
    text = Path(path).read_text(encoding="utf-8")
    out = {}
    starts = list(ENTRY.finditer(text))
    for i, m in enumerate(starts):
        body = text[m.end(): starts[i + 1].start() if i + 1 < len(starts) else len(text)]
        fields = {"type": m.group(1).lower()}
        for f in re.finditer(r"(\w+)\s*=\s*\{", body):
            depth, j = 1, f.end()
            while j < len(body) and depth:
                depth += {"{": 1, "}": -1}.get(body[j], 0)
                j += 1
            fields[f.group(1).lower()] = body[f.end(): j - 1]
        out[m.group(2)] = fields
    return out


def parameter_citations(doc: dict) -> dict[str, list[str]]:
    """{parameter name: [bib keys]} for every record with a `citations` field."""
    return {r["name"]: list(r["citations"]) for r in doc["parameters"] if "citations" in r}


DRAFT_CITE = re.compile(r"\[@([^\]]+)\]")
# Author-in-text citations, "@leeman2024 re-analyse the campaign", which pandoc resolves exactly as
# it resolves the bracketed form. Until 2026-10-18 only the bracketed form was extracted, so
# draft_citations saw 37 of the 43 keys the manuscript cites and test_draft_citations_resolve was
# validating a minority of its own target. A broken key of this form renders as a bare marker in
# the PDF rather than failing anything. The negative lookbehind keeps bracketed keys from matching
# twice; the trailing strip drops sentence punctuation, which is not part of a key.
INTEXT_CITE = re.compile(r"(?<![\[\w@])@([A-Za-z][A-Za-z0-9_:.#$%&+?<>~/-]*)")


def draft_citations(text: str) -> list[str]:
    """Keys cited in a Markdown draft, in either pandoc form.

    Bracketed: [@key] or [@key1; @key2]. Author-in-text: @key.
    """
    found = []
    for group in DRAFT_CITE.findall(text):
        found += [k.strip().lstrip("@").split(",")[0].strip() for k in group.split(";")]
    found += [k.rstrip(".,;:!?)") for k in INTEXT_CITE.findall(text)]
    return found
