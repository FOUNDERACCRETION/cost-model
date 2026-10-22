"""Build the single upload PDF: main paper and appendices in one pandoc run.

Building the two Markdown files separately and concatenating the PDFs gave a document whose
page numbers restarted at 1 after page 33 and whose bibliography appeared twice, with the
same work cited as "Riebesell et al. 2025" in the main paper and "2025a" in the appendix,
because each run disambiguated its own reference list. One run fixes both: the appendix
body is appended under the main paper's front matter, with a page break and an unnumbered
heading, and citeproc builds one list at the end.

Usage:  python scripts/build_pdf.py [--out build/Aduru-2026-cost-to-validate-a-material.pdf]

Needs pandoc with citeproc and XeTeX. If the TeX tree lacks lmodern.sty (pandoc's default
template loads it), the script builds with a copy of the template that does not.
"""
from __future__ import annotations
import sys as _sys
if hasattr(_sys.stdout, "reconfigure"):
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "paper" / "p1-final.md"
APPX = ROOT / "paper" / "p1-appendices.md"
BIB = ROOT / "paper" / "references.bib"


def split_front_matter(text: str) -> tuple[str, str]:
    m = re.match(r"---\n.*?\n---\n", text, re.S)
    if not m:
        raise SystemExit("no YAML front matter found")
    return m.group(0), text[m.end():]


def template(build: Path) -> Path | None:
    """pandoc's default LaTeX template, minus \\usepackage{lmodern} if that package is missing."""
    if shutil.which("kpsewhich") and subprocess.run(["kpsewhich", "lmodern.sty"], capture_output=True).returncode == 0:
        return None
    tpl = subprocess.run(["pandoc", "-D", "latex"], capture_output=True, text=True, check=True).stdout
    tpl = tpl.replace("\\usepackage{lmodern}", "%\\usepackage{lmodern}")
    out = build / "template-no-lmodern.latex"
    out.write_text(tpl, encoding="utf-8")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "build" / "Aduru-2026-cost-to-validate-a-material.pdf"))
    args = ap.parse_args()
    out = Path(args.out).resolve()
    build = out.parent
    build.mkdir(parents=True, exist_ok=True)

    front, main_body = split_front_matter(MAIN.read_text(encoding="utf-8"))
    _, appx_body = split_front_matter(APPX.read_text(encoding="utf-8"))
    combined = (front + main_body.rstrip() + "\n\n\\newpage\n\n# Appendices and Supplements {.unnumbered}\n\n"
                + appx_body.lstrip())
    src = build / "combined.md"
    src.write_text(combined, encoding="utf-8")

    cmd = ["pandoc", str(src), "-o", str(out), "--pdf-engine=xelatex", "--citeproc",
           f"--bibliography={BIB}", f"--resource-path={ROOT / 'paper'}"]
    tpl = template(build)
    if tpl:
        cmd.append(f"--template={tpl}")
    print(" ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    for line in (r.stderr or "").splitlines():
        if "Citeproc" not in line:  # the three unresolvable-URL warnings are known and harmless
            print(line, file=sys.stderr)
    if r.returncode:
        raise SystemExit(r.returncode)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
