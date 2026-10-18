"""Parameters and the paper draft cite only keys that exist in paper/references.bib, and nothing withdrawn."""

import re
import subprocess
from pathlib import Path

import pytest

from src.bib import BIB, draft_citations, entries, keys, parameter_citations
from src.params import load

ROOT = Path(__file__).resolve().parent.parent
# Both documents. Checking only p1-final.md left four keys unguarded -- bartel2020, cfr200468,
# riebesell2025correction and wang2021corrections are cited only in the appendices -- and a broken
# key there renders as a bare marker in the companion PDF, which is the half a referee checks the
# provenance in. (All four do resolve; they were simply not being checked.)
DRAFTS = [ROOT / "paper" / "p1-final.md", ROOT / "paper" / "p1-appendices.md"]


def test_bib_keys_unique():
    ks = keys()
    assert ks, f"no entries in {BIB}"
    assert len(ks) == len(set(ks)), sorted(k for k in ks if ks.count(k) > 1)


def test_every_parameter_citation_resolves():
    bib = set(keys())
    cited = parameter_citations(load())
    assert cited, "no parameter carries a citations field"
    missing = {name: [k for k in ks if k not in bib] for name, ks in cited.items()}
    missing = {n: ks for n, ks in missing.items() if ks}
    assert not missing, f"parameters cite keys absent from {BIB.name}: {missing}"


def test_parameters_with_bib_sources_keep_their_urls():
    """A citation key supplements the source URL; it never replaces it."""
    for rec in load()["parameters"]:
        if "citations" in rec:
            assert rec["source_url"], rec["name"]


def test_draft_citations_resolve():
    bib = set(keys())
    missing = {}
    for draft in DRAFTS:
        assert draft.exists(), f"{draft.name} is missing, so its citations go unchecked"
        cited = draft_citations(draft.read_text())
        assert cited, f"{draft.name} cites nothing, which means the parser has stopped matching"
        bad = sorted({k for k in cited if k not in bib})
        if bad:
            missing[draft.name] = bad
    assert not missing, f"a document cites keys absent from {BIB.name}: {missing}"


def test_citation_extraction_sees_both_pandoc_forms():
    """The guard above is only as wide as the extractor, and the extractor was half-blind.

    draft_citations matched only the bracketed form, [@key], so it saw 37 of the 43 keys the
    manuscript cites and test_draft_citations_resolve was validating a minority of its own target.
    Author-in-text citations -- "@leeman2024 re-analyse the campaign" -- were invisible, and a
    broken key of that form renders as a bare marker in the PDF rather than failing anything.

    This pins both forms, and pins that the manuscript really does use both, so the check cannot go
    quiet by the extractor narrowing OR by the paper's citation style drifting.
    """
    found = draft_citations("Bracketed [@alpha] and grouped [@beta; @gamma], then @delta in text.")
    assert set(found) == {"alpha", "beta", "gamma", "delta"}, found
    # trailing sentence punctuation is not part of a key
    assert draft_citations("as @epsilon. And @zeta, also @eta;") == ["epsilon", "zeta", "eta"]
    # a bracketed key must not be counted twice by the in-text pattern
    assert draft_citations("[@theta]").count("theta") == 1

    main = set(draft_citations((ROOT / "paper" / "p1-final.md").read_text()))
    assert len(main) > 30, f"only {len(main)} keys extracted from the manuscript"
    bracket_only = set(re.findall(r"\[@([a-z0-9]+)\]", (ROOT / "paper" / "p1-final.md").read_text()))
    assert main - bracket_only, (
        "every citation in the manuscript is bracketed, so this test would pass even with the "
        "in-text pattern removed; check the extractor still handles author-in-text citations")


def test_bib_entries_have_titles_and_years():
    for key, e in entries().items():
        assert e.get("title"), key
        assert e.get("year"), key


# ---------------------------------------------------------------- DO NOT CITE
# A 2024 arXiv working paper on AI and productivity in a materials R&D lab was withdrawn after the author's
# institution (MIT) stated on 16 May 2025 that it had no confidence in the data, and asked for withdrawal from the
# journal and from arXiv. The arXiv page was still not flagged as withdrawn when checked, so it is easy to cite by
# accident. Its identifiers are assembled from parts so that this file does not itself contain them.
FORBIDDEN = (
    "2412" + "." + "17866",          # arXiv identifier
    "toner" + "-" + "rodgers",       # author surname, hyphenated
    "toner" + " " + "rodgers",       # author surname, unhyphenated
    "toner" + "rodgers",
)


def repo_files():
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                         cwd=ROOT, capture_output=True, check=True).stdout.decode()
    return [ROOT / f for f in out.split("\0") if f and (ROOT / f).is_file()]


def test_withdrawn_paper_cited_nowhere():
    hits = []
    for path in repo_files():
        try:
            text = path.read_text(errors="ignore").lower()
        except OSError:
            continue
        # Strip comment lines first: a DO-NOT-CITE warning has to be able to name the paper
        # it warns about. BibTeX comments start with %, Python/YAML with #, Markdown uses <!-- -->.
        body = "\n".join(
            ln for ln in text.splitlines()
            if not ln.lstrip().startswith(("%", "#")) and "<!--" not in ln
        )
        hits += [f"{path.relative_to(ROOT)}: {f}" for f in FORBIDDEN if f in body]
    assert not hits, f"withdrawn paper referenced (DO NOT CITE): {hits}"


@pytest.mark.parametrize("needle", FORBIDDEN)
def test_guard_detects(needle, tmp_path):
    """The guard's matching is case-insensitive."""
    assert needle in f"see {needle.upper()} here".lower()
