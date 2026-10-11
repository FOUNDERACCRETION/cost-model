"""Read paper/references.bib, the single source of bibliographic truth for parameters and the draft."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "paper" / "references.bib"

ENTRY = re.compile(r"^@(\w+)\s*\{\s*([^,\s]+)\s*,", re.M)


def keys(path: Path = BIB) -> list[str]:
    """Citation keys of every entry, in file order."""
    return [m.group(2) for m in ENTRY.finditer(Path(path).read_text())]


def entries(path: Path = BIB) -> dict[str, dict]:
    """{key: {"type": ..., field: value}} with brace-balanced field values (enough for checks, not a full parser)."""
    text = Path(path).read_text()
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


def draft_citations(text: str) -> list[str]:
    """Keys cited in pandoc form, [@key] or [@key1; @key2], in a Markdown draft."""
    found = []
    for group in DRAFT_CITE.findall(text):
        found += [k.strip().lstrip("@").split(",")[0].strip() for k in group.split(";")]
    return found
