# Reference and claim verification — 11 October 2026

Every bibliography entry and every substantive claim attached to one was checked against a fetched
authoritative record on this date. Nothing below rests on recollection: where a source could not
be reached, that is recorded as unreached rather than resolved.

Policy, carried from an earlier failure in this project where author given names were expanded
from memory and four were wrong: **print what the source prints.** Where a publisher prints
initials, the entry prints initials.

---

## Part 1 — bibliography: 63 of 63 entries checked

Each entry was resolved to its DOI (or arXiv identifier, or official page for government and
report items) and compared field by field: author list and order, title, venue, year. None was
unreachable.

### Corrections made

| Entry | Was | Source prints | Where verified |
|:--|:--|:--|:--|
| `buchner2018tea` | Hohgräve, **Arne** E. | Hohgräve, **Arian** E. | 10.1021/acs.iecr.8b01248 |
| `kusumegi2025` | Yang, **Y.** | Yang, **X.** (Xinyu Yang) | 10.1126/science.adw3000 |
| `hautier2011substitution` | Fischer, **Christopher** | Fischer, **Chris** | 10.1021/ic102031h |
| `sorzano2026` | Sorzano, **Carlos Oscar S.**; Carazo, **José María** | **C. O. S.** Sorzano; **J. M.** Carazo | 10.1107/S2059798326003608 |
| `giannozzi2017qe` | Giannozzi, **Paolo** | **P** Giannozzi | 10.1088/1361-648X/aa8f79 |
| `kobos2020tea` | Outkin, **Alexander** | Outkin, **Alexander V.** | Sandia pubs record, SAND2020-13473 |

Two of these — `kusumegi2025` and `hautier2011substitution` — were wrong in substance: an initial
that duplicated a different author's, and a given name expanded to the wrong full form. Two more —
`sorzano2026` and `giannozzi2017qe` — were expansions of printed initials, the specific error this
project's policy exists to prevent.

### Noted, not changed

- `kobos2020tea`: the Sandia publications record prints "Peter Kobos" where the entry has "Peter
  H. Kobos". The report's own cover page could not be reached, so the middle initial is
  **unresolved** and left as it stands.
- `barrosoluque2024omat24`: the cited preprint (arXiv:2410.12771) has since been published in
  *Nature Computational Science* (2026), which adds an author and spells the first author's
  surname **Barros-Luque** where arXiv prints **Barroso-Luque**. The two records disagree. The
  entry continues to cite the preprint, which is the version read, rather than silently adopting
  one spelling.
- `kononova2019` has an uncited Author Correction. The entry is not cited in the manuscript, so no
  action was taken.
- `jain2012nersc`: the citation key says 2012; the slide deck and the `year` field both say 2013.
  Cosmetic key mismatch only.
- Three entries are in the bibliography but not cited in the final manuscript:
  `barrosoluque2024omat24`, `chen2024jacs`, `kononova2019`. Pandoc renders only cited entries, so
  they do not appear in the reference list.

**A caution about the method.** The first pass extracted bibliography fields with a script whose
regex silently dropped `eprint`, `archivePrefix`, multi-line titles and some final fields. That
produced several false findings — four entries reported as having an empty `year` and three as
having no venue, all of which were in fact complete. Every reported discrepancy was re-checked
against the file itself before any edit, and only the six above survived. A verification pass needs
its own verification.

---

## Part 2 — substantive claims: 11 checked against the source text

### Findings that changed the paper

**1. The A-Lab correction publishes no revised success count and no denominator.**

Verified at 10.1038/s41586-025-09992-y, cross-checked on PMC12872444. The notice states that the
platform "came to the correct conclusion in 36 of its 40 reported successes, with 4 compounds being
inconclusive", that the total "has now been updated to exclude four target materials whose presence
is inconclusive from XRD alone", and that Zn₂Cr₃FeO₈ was "mistakenly included in the training data".

**The numerals 38, 54 and 57 do not appear in the notice.** No revised total is published.

So 36/57 cannot be cited to the correction as a count. The 36 follows from the notice's own
arithmetic; the 57 is the 2023 article's target count. §3.5 now presents the ratio as a composite
of two documents and says the correction publishes no revised total, and the readings table
attributes it accordingly. This matters because 36/57 is the paper's central optimistic
calibration.

**2. The 3.8% generative-pool purity is not assigned to any model by its source.**

Verified at arXiv:2501.02144v2, which matches the published *Materials Horizons* version. The
3.8–8.8% range spans two generative models; the source never says which endpoint belongs to which,
and it tabulates no filtered rates per method at all. The 3.0% unfiltered figure is one model's own
rate, not a pooled one. §5.3 previously said assigning 3.8% was "our reading rather than the
source's assignment"; it now says the source leaves the question open and that the 3.0% is
likewise one model's rate.

Also recorded: **v1 and v2 of that preprint differ materially on these figures.** v2 is the
citable version.

**3. Kusumegi's 23.7% and 89.3% are subgroup-by-platform figures, not a range across fields.**

Verified in the article text. 23.7% is the arXiv low end for authors with Caucasian names at
institutions in English-speaking countries; 89.3% is the bioRxiv figure for Asian-named scholars at
Asian institutions. §2.2 described them as varying "across fields", which was wrong, and now names
the groups and the servers.

Two cautions on this one. science.org was not reachable, so the text read was a third-party-hosted
PDF self-identifying as *Science* 390:1240. And the source contains an internal inconsistency: a
supplementary figure caption gives 37.7% where the main text gives 43.0% for one subgroup. **This
claim should be re-checked against the publisher version before submission.**

**4. Cheetham and Seshadri report counts, not shares, and do not describe the ten sampled entries
as "known structure types".**

Verified at PMC11044265. The source identifies the structure of every one of ten randomly sampled
entries in the ICSD, "usually with a space group of higher symmetry"; "known structure types" is
the abstract's general phrasing, not its description of the ten. For radioactivity it gives counts
— 18,138 compounds of Pm, Ac or Pa and 23,529 containing Tc, Np or Pu, in a set of 384,870 — and
asserts no percentage. §2.2 and Limitation 16 now give the counts and say the implied fraction is
ours.

**5. Riebesell's 15.3% is the unique-prototype test set, not the full WBM test set.**

Verified: 32,942 of 215,488 for unique prototypes, against 16.7% (42,825 of 256,963) for the full
dataset. CHGNet's DAF is 3.361. The Author Correction removes model rows that were never discussed
in the text and changes neither figure. The §5.4 table row now carries the qualifier.

### Confirmed as stated

| Claim | Verdict | Source |
|:--|:--|:--|
| ~200 CPU-h per calculation; 1–5 calculations per material | supported, slide 4 (unnumbered) | NERSC User Day deck |
| 10–20% of jobs fail and are rerun | supported, slide 25 (unnumbered) | same deck |
| Chung et al. on experimental validation limiting discovery | supported — it is the abstract's opening sentence | 10.1039/D5DD00065C |
| Agrawal et al. ω = αβγδ | supported, Eq. (9) | NBER WP 34953 |
| Lo et al. tabulate costs for 25 platforms | supported, Table 1, 25 rows | 10.1039/D3DD00223C |
| Strom et al.: user fees do not fully support most facilities | supported, verbatim | 10.1557/mrs.2020.130 |
| Ion-exchange pool: 15.2% filtered purity of 300 novel structures, 9.2% unfiltered | supported | arXiv:2501.02144v2 |

### Still unverified, and why

| Claim | Status |
|:--|:--|
| Target-level crosswalk reconciling 36/57, 36/54, 38/57, 38/54 | **Cannot be closed from the correction**, which publishes no revised total. Needs the annotated supplement. |
| Low DFT anchor of 2.98 core-hours | First-hand measurement; the author's own data, not externally verifiable. |
| Kusumegi 23.7% / 89.3% | Read from a third-party PDF; publisher version unreachable. Re-check before submission. |
| Post-correction Table 1 of Riebesell et al. | nature.com table pages are robots-disallowed; verified from arXiv v3 and an eScholarship copy predating the correction. |
| NRSA stipend, tuition high value, spot discount | Parameter values traceable to the manifest; not re-fetched in this pass. |

---

## What this pass does not establish

It checks that each source says what the paper says it says. It does not check that the model's
arithmetic is right (the test suite does that), that the parameter values are the right ones to
use, or that the conclusions follow. And it is a check by the same parties who wrote the paper.
Independent reproduction remains outstanding.
