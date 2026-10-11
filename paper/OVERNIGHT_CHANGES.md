# Overnight changes, 2026-10-10

## Summary

**Headline before and after the indirect-cost fix.** The overhead rate (`synth.indirect_rate`) went from 0.58 to 0.42.
0.58 is the average *negotiated* indirect cost recovery rate; 0.42 is the *effective* rate NIH actually pays
(Azoulay, Gross & Sampat 2025, NBER WP 33627). The range is now 0.25 / 0.42 / 0.58. It was 0.42 / 0.58 / 0.70 (Caltech).
All figures are for pipeline B unless marked.

| Quantity | Before (58%) | After (42%) |
|---|---|---|
| Cost per synthesis attempt | $221 (indirect cost $30) | $213 (indirect cost $22) |
| Level 2, base case, A / B / C | $3,794 / $3,765 / $3,897 | $3,653 / $3,625 / $3,756 |
| Synthesis term per validated material | $3,722 | $3,581 |
| Level-2 spread: base DFT / top of span | 1.03× / 1.53× | 1.04× / 1.55× |
| "Pipelines land within X%" | 3% | **4%** (3.6%) |
| Headline, A-Lab reading (MC median, 90% interval) | $2,751 ($1,956–$3,847) | $2,653 ($1,872–$3,725) |
| Headline, Prein reading | $5,186 ($2,968–$10,277) | $5,004 ($2,859–$9,923) |
| Headline, Leeman reading | $65,403 ($28,025–$191,211) | $63,072 ($27,021–$184,697) |
| Factor between extreme readings | 24× | 24× (unchanged) |
| Synthesis vs best compute lever, per point | 21–119× | **20–114×** |
| Spot-price lever | 0.7%–2.8% | 0.7%–2.9% |
| Level-2 95th percentile (equal weights) / with Leeman at weight 0 | $122,696 / $8,716 | $118,428 / $8,430 |
| Cost bases: direct only / funder / fees inside base (A) | $3,284 / $3,794 / $4,946 | $3,284 / $3,653 / $4,487 |
| Spread between the extreme cost bases | 51% | 37% |
| Synthesis share of level 2 at base DFT cost | 96–99% | 95–99% |
| Level-3 lower bounds A / B / C | ≥ $45,369 / $45,030 / $44,602 | ≥ $43,687 / $43,347 / $42,992 |
| Attempt cost below which compute is 10% of level 2 | $23–$94 | $23.26–$93.52 (unchanged: compute-side quantity) |

Level-1 costs, the DAF figures, P(B < A) = 99.5%, the 2× multiplier (44% → 87%) and the tornado shares do not change.
As a check, the model at a 58% rate reproduces the old $221 attempt and $3,765 level 2 exactly (keys
`attempt_at_negotiated`, `l2_B_at_negotiated`), so the rate is the only thing that moved.

**Wording the fix changed.** "Within 3%" is now "within 4%" in the abstract, contributions and conclusion. "21 to
119 times" is now "20 to 114". The abstract's "the only lever available at zero cost moves the result by under 3%"
still holds, but only just: 2.9% for C.

**Bibliographic fields resolved** (checked against Crossref, the publisher-deposited record, unless noted):

- Walker & Butler: they were missing from the bib altogether. Added `walker2026carbon`: Materials Horizons 13(4),
  1993–2004 (2026). The first author is **Matthew** Walker. Issue number: 4.
- ASE: the title uses an em dash (U+2014), with no spaces around it. Seen on the IOP page and in Crossref.
- GBRV and pymatgen: neither Crossref record has an issue number. The ScienceDirect pages were not fetched, so "no
  issues" is confirmed only to the level of the Crossref record.
- Chen et al., JACS: the title says **"Machine Learning"**. The pages are 20009–20018. This comes from the
  ACS-deposited Crossref record; pubs.acs.org itself was not fetched.
- OMat24: a peer-reviewed version **does** exist: Nature Computational Science 6(6), 642–652 (2026),
  doi:10.1038/s43588-026-00996-w. Added as `barrosoluque2026omat24`. The publisher spells the first author
  "Barros-Luque" (probably a typo), and its author list adds M. Uyttendaele. Decide which spelling to print.
- Jansen (2002): Angew. Chem. Int. Ed. 41(20), 3746–3766. The DOI is added.
- Kononova et al. (2019): Scientific Data 6, article 203, doi:10.1038/s41597-019-0224-1, with the full author list.
  The Author Correction is Scientific Data 6, article 273, doi:10.1038/s41597-019-0297-x (`kononova2019correction`).
- Kusumegi et al.: "Scientific production in the era of large language models", Science 390(6779), 1240–1243.
  **The year is 2025** (18 December 2025), not 2026, so the key is renamed `kusumegi2025`.
- Pilon et al.: "A flexible and affordable self-driving laboratory for automated reaction optimization", Nature
  Synthesis 5(10), 1552–1564 (2026).
  - **Both platform cost figures are in the paper itself**, in the introduction, not only in press coverage. I
    checked the open-access text on nature.com myself.
  - The US$50,000 is the group's *earlier* RoboChem platform, "for essential components alone", excluding the NMR.
  - The US$5,000 is RoboChem-Flex in its human-in-the-loop configuration.
  - It is a flow-chemistry platform, not a solid-state one.
- Exact titles, all from Crossref:
  - Montoya: "How the AI-assisted discovery and synthesis of a ternary oxide highlights capability gaps in materials
    science".
  - Aziz & Carrasco: "Towards Predictive Synthesis of Inorganic Materials Using Network Science".
  - Chung, Walsh & Payne: "Solid-state synthesizability predictions using positive-unlabeled learning from
    human-curated literature data". Digital Discovery 4(9), 2439–2453.
  - Strom et al.: "Shared instrumentation facilities: Benefiting researchers and universities, and sustaining
    research excellence". Issue 5.
  - Sorzano & Carazo: "Rational acquisition of laboratory equipment: an accurate mathematical model to estimate the
    trade-offs in shared and nonshared equipment".
  - Tobias & Wahab: "Autonomous 'self-driving' laboratories: a review of technology and policy implications".
- NBER WP 34953 "AI in Science" (Agrawal, McHale & Oettl, March 2026): title, authors and abstract confirmed on
  nber.org. The abstract says returns differ across domains and workflow stages.
- **Errors found in entries the bib marked as verified.** I ran a Crossref audit of every DOI in the bib, and it
  turned these up:
  - Wrong author given names:
    - Leeman et al.: Josh Leeman, Joseph Stiles, Scott B. Lee and Prajna Bhatt, not Joshua, Jackson, Seung Beom and
      Palak.
    - AlabOS: Olympia Dartsi, not Oleg.
    - Adesiji: Jiashuo Wang and Cheng-Shu Kuo.
    - Buchner: Arian E. Hohgräve, not Arne.
    - Strom: T. Amanda Strom and Jonathan Shu.
    - Hautier: Chris Fischer.
  - Quotation marks inside two titles: Jones (2009), "Death of the Renaissance Man"; Lo et al., "frugal twin".
  - All other differences the audit reported are typographic (LaTeX against MathML or HTML) or conventional. The
    conventional ones:
    - Crossref gives issue "1" for continuous-publication journals.
    - Crossref's "issued" date for Hautier is its 2010 online-first date. The print issue is vol. 50, no. 2 (2011),
      as the bib has it.

**Still unverified:**

- **Strom et al. (2020): the claim we cite it for.** The claim is that user-fee income alone does not fully support
  most shared facilities. Springer blocked every fetch, so I never saw the sentence.
  - It is used in limitation 12 of the draft, limitation 11 of the README, and the XRD and furnace `source_note`s.
  - All of those flag it as unchecked. Read the article before submission.
- **ScienceDirect pages for GBRV and pymatgen**, and the **pubs.acs.org page for Chen et al.** These were checked via
  Crossref only.
- **The content behind every citation inserted into the draft.** Bibliographic fields are verified; that each source
  says what the sentence uses it for is not. The list is at the end of the draft, under "Citations inserted overnight
  that are not fully verified".
- The preprint titles stated in your brief (the A-Lab's "novel materials" and Leeman's singular "Material") were not
  re-checked. Only the current published titles were.

**What I could not do, or did differently from the brief:**

1. **Low end of the rate.** The paper gives no explicit low value. I used 25%, from "effective rates in practice are
   generally between 25% and 45%" (section 3.3, p. 17). The paper's Table 1 also gives a minimum of 14% and a s.d. of
   10%.
2. **Vocabulary.** The paper's title and abstract say "indirect cost recovery (ICR)". However, the body *does* use
   "F&A rate", for negotiated agreements; it is not true that the paper avoids the term. The source note leads with
   ICR and records this. In the README and code I kept "F&A" where it names the accounting base, and the rate itself
   is now described as the effective indirect cost recovery rate.
3. **A caveat the brief did not mention.** The effective rate is measured against total direct costs, a wider base
   than the MTDC-like base we charge it on, so 42% leans low. This is recorded in the source note, the README and §4.5.
4. **Bib location.** The bib is now `paper/references.bib`. `paper/p1-citation-memo.md` was not in the repo, so for
   Part 5 I used the list in your brief, and placed citations where your brief said.
5. **DO NOT CITE.** The bib's original DO NOT CITE comment contained the withdrawn paper's arXiv ID and author name,
   so the new guard test would have failed on it.
   - I rewrote that comment without the identifiers.
   - The test assembles the forbidden strings from parts, so the test file does not trip itself.
   - It scans every tracked and untracked, non-ignored file.
6. **Facts about the draft that I changed.** The draft claimed that "the test suite fails if a figure in the text
   drifts". That was not true before tonight; it is now.
   - Every model number in the draft (158 of them) carries an HTML-comment tag linking it to
     `results/key_numbers.json`.
   - `tests/test_draft.py` checks every tag against that file.
   - `scripts/fill_draft.py` rewrites the numbers after a rerun.
   - The tags are invisible in pandoc output, but they do clutter the Markdown. If you dislike them, say so and I will
     move the mapping to a sidecar file.
7. **README numbers that were hand-typed** are now generated blocks: base case, cost bases, DFT span, attempt
   breakdown, level 3, and the multiplier.
8. **A small bug fixed along the way.** The README's top-80% tornado table was printed twice. The cause was
   `md_table(...) + md_table(...)` in `scripts/stage2.py`.
9. **Not done:** no DFT or `pw.x` runs, as instructed. No source was read in full. §2.1 and §2.2 of the draft still
   rest on abstracts.
10. **CITATION NEEDED, in four places.** Each has a source URL but no bib entry:
    - the Liverpool throughput figure
    - the MP 2012 CPU-hours (NERSC slides)
    - two press figures in §6.3
    - "thousands of candidates an hour" in §1, which may simply be wrong: 9.22 A100-s per structure is about 390 an
      hour per GPU.

## Commits (all pushed to origin/main, private repo)

1. `84d0f2e` Indirect cost: effective 42% rate, stage-1 README blocks generated, key_numbers.json
2. `9c85de5` Bibliography moved to paper/references.bib, parameter citation keys, citation and DO NOT CITE tests, Crossref fixes
3. `126b8cf` Published-version map in sources/, Hautier for ion exchange, Strom caveat
4. `1f18ff8` Draft updated to the corrected model, tagged numbers, citations
5. This file

Tests: 732 passed (`uv run pytest`), up from 716.
