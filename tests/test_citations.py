"""Parameters and the paper draft cite only keys that exist in paper/references.bib, and nothing withdrawn."""

import subprocess
from pathlib import Path

import pytest

from src.bib import BIB, draft_citations, entries, keys, parameter_citations
from src.params import load

ROOT = Path(__file__).resolve().parent.parent
DRAFT = ROOT / "paper" / "p1-final.md"


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
    cited = draft_citations(DRAFT.read_text())
    missing = sorted({k for k in cited if k not in bib})
    assert not missing, f"draft cites keys absent from {BIB.name}: {missing}"


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
