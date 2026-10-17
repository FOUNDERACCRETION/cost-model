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

---

## Part 3 — second pass, 18 October 2026 (pre-upload)

### Closed first-hand this pass

**`nih2026stipends` — verified at the notice itself.** NOT-OD-26-044, "Ruth L. Kirschstein National
Research Service Award (NRSA) Stipends, Tuition/Fees and Other Budgetary Levels Effective for Fiscal
Year 2026". Two parameter values depend on it and both check out: the FY2026 predoctoral stipend is
**\$29,364 per year**, which is `synth.labour_annual_salary`; and tuition support is "equal to 60% of
the actual tuition level at the applicant institution, up to \$16,000 per year", which is the base of
`synth.labour_tuition_remission`. The notice also prints a \$21,000 cap for formally combined
dual-degree programmes, which we do not use and which a reader should not confuse with the \$16,000.
This entry was previously listed as unverified and as the sole source for the labour term; it is now
read at source.

**The DFT protocol is now in the paper.** Section 4.2 previously reported hardware and rank counts but
no cutoffs, k-mesh, smearing, spin treatment or convergence thresholds, so the 2.98 core-hour anchor
could not be assessed. The protocol was recorded in the benchmark package throughout and is now stated
in the manuscript, including the forced substitution of GBRV for the planned SSSP library after the
Materials Cloud file server returned HTTP 503.

### Four flagged citations, read at source this pass

| Entry | Verdict | Evidence |
|:--|:--|:-----------|
| `agrawal2026aiinscience` | verified | NBER WP 34953, **equation (9)**: productivity is $\alpha\beta\gamma\delta$ over question generation, idea generation, design generation and testing. The attribution holds in full, including testing as a stage, so contribution 3 rests on a first-hand read. Section 2.2 now cites the equation number. |
| `riebesell2025` | verified | "could **consequently** be interpreted as overestimating the performance" appears verbatim, and the stated reason for declining a combined hull is path-dependence. Read in arXiv v3 §2.1.3 and in a lab-hosted copy of the published *Nature Machine Intelligence* version; **not** checked against nature.com, which blocks the fetch. |
| `walker2026carbon` | verified | Eight configurations from fully ML to fully DFT, emissions per strategy, and the authors' own accuracy--emissions front. The source calls the learned scissor correction a "viable" intermediate method; an earlier draft called it "strong", which overstated it, and the compression of Section 2.1 removed that sentence before this pass. Still an Advance Article, so the absent pagination is correct. |
| `renault2026comment` | verified, and the citation reframed | The Comment argues that dating adoption by the first LLM-flagged abstract is mechanically related to output and that placebo flags reproduce the reported dynamics. Citing it in a bare semicolon list beside `kusumegi2025` implied two concordant sources; Section 2.2 now states that it contests the identification. The paper uses none of Kusumegi's effect sizes. |

### First-hand benchmark claims, re-derived from the raw timing data

Every claim the paper makes about its own measurements was recomputed from `data/dft_benchmark/timings.csv`
and `data/mlip_benchmark/timings.csv`. All eight hold exactly.

| Claim | Checked against the data |
|:--|:-----------|
| Seven structures, 10 to 56 atoms | 7 distinct sizes: 10, 14, 16, 20, 28, 32, 56 |
| Twelve ranks cost 2.6 to 7.3 times four | Per-size medians of the **SCF** runs give 2.63 to 7.30 (2.6272 to 7.3032). Basis matters and is easy to get wrong: including the four `vc-relax` rows gives 2.82 to 27.69, and the same-session interleaved pairs give 7.32 and 3.86, which is the pair `data/dft_benchmark/PROTOCOL.md` quotes -- as the MEDIAN OF THE MATCHED PAIR RATIOS (10 atoms: 7.6479, 7.3205, 7.1890, median 7.32; 20 atoms: 3.8445, 3.8678, median 3.86), which is the right statistic for an interleaved design and is not the same as the ratio of the medians, 7.3163 and 3.8487. Three bases, three answers, all correct for what they measure. A review pass on 2026-10-18 flagged 7.30 as a typo for the protocol's 7.32; it is not. The two are different statistics over the same data and both are correct. |
| 0.480 against 3.842 core-hours, factor 8.0, exponent 3.0 | Medians are 0.480 and 3.842; factor 8.00; log2 = 3.00 |
| Step count 18 to 81 | 68 converged CHGNet and MACE relaxations span exactly 18 to 81. M3GNet is correctly excluded: all its converged runs report 191 steps, set by the cap rather than by convergence |
| One of three potentials failed on six of seven structures | M3GNet converged on 1 of 7 in `primary_1thread`. The MLIP protocol's "5 of 6" excludes the non-native supercell; both figures are right for their populations |
| Twelve threads cost 32 to 90 times one | The sweep's billed-cost multiplier runs 32.27 to 89.98. Note for anyone re-checking: `core_seconds_per_ionic_step` gives a different and much smaller range, because it normalises away the step count; the billed-cost column is the right basis for a core-hour claim |
| ecutwfc 40 Ry, ecutrho 200 Ry for every run | Both constant across all 45 DFT rows |
| Spin-polarised for the manganese structures only | Holds for all rows; the three Mn formulas are the three spin-polarised ones |

### Still open at upload

- **The Kusumegi figures (23.7%, 89.3%).** Read from a third-party-hosted PDF because science.org was
  unreachable, and that text contains an internal inconsistency: a supplementary caption gives 37.7%
  where the main text gives 43.0% for one subgroup. Re-check against the publisher version.
- **The target-level crosswalk** for A-Lab's 36 of 57, which would confirm the four inconclusive
  targets are not subtracted twice. Needs the annotated supplement.
- **Independent reproduction.** Has not happened. The repository is not public and no DOI is minted.

## Part 6: the model code, reviewed as code — 18 October 2026

Everything above checks figures *against* the model. This part checks the model. Each algebraic
identity below was re-derived independently and compared with the implementation, not run through
the same code path and compared with itself.

**One defect found and fixed.** `analysis.percentile` returned `nan` where the answer is `inf`:
when both bracketing order statistics are infinite the interpolation computes `inf - inf`, which is
`nan`, and `nan` survives the multiply. Every reported median and 5th-to-95th interval flows through
this function. `nan` is worse than wrong here, because it compares false against every threshold, so
a materiality or ordering test downstream counts the draw as immaterial rather than skipping it — a
silent bias toward "no difference" in exactly the comparisons §5.6 reports. Reachable: level 3 is
unbounded wherever the novelty share is zero, which is what the pessimistic reading asserts. Not
live at the current parameters (the Jeffreys posterior never draws exactly zero), so the fix moved
no figure; confirmed by regenerating and comparing checksums.

**Verified correct, with the derivation:**

| What | Check |
|:--|:-----------|
| `mlip_filter`, measured basis | `flagged = prevalence x recall / purity` is the right bookkeeping: of the pool, `prevalence x recall` are true positives that pass, and if purity is the true-positive share of passers then passers = true_pos/purity |
| `mlip_filter`, `recall_if_matbench_fpr` | From `P = pi.r / (pi.r + (1-pi).f)`, solving for `r` gives `P(1-pi)f / (pi(1-P))`, which is what the code computes |
| `mlip_filter`, `implied_fpr` | From `flagged = pi.r + (1-pi).f`, `f = (flagged - pi.r)/(1-pi)` |
| Stage cost allocation | `_stage` charges cost on candidates ENTERING a stage, not survivors, so failed DFT runs and failed synthesis attempts are paid for |
| `novel_beyond_mp` | Conditions correctly as `frac_novel_all_db / frac_novel_mp`, both shares being of all generated |
| Success bound | `success x filtered multiplier` is guarded and raises above 1. Expected this to be a hole, since the multiplier is only checked for non-negativity. It is not |
| `attempt_cost_thresholds`, compute share | From `c/(c + k.a) = s`, `a = c(1-s)/(s.k)` |
| `attempt_cost_thresholds`, spread | From `(max(c) + k.a)/(min(c) + k.a) = S`, `a = (max(c) - S.min(c))/(k(S-1))` |
| `purity_for_parity` | Bisection bracket is correct — the gap decreases in purity — and the floor is `prevalence x recall`, below which the pass fraction would exceed 1 (0.030 x 0.7585 = 2.28%) |
| `multiplier_for_level2_spread` | Hits its targets to six decimal places (1.4473 and 1.9297 give spreads of exactly 1.500000 and 2.000000, implying 42% and 56% success), and its `m_max = 1/S` is 3.4286, the same feasibility ceiling Appendix A.3 reports as 3.429 |
| `kill_condition` | Implementation matches its docstring: histograms hold normalised probabilities rather than densities and are not divided by bin width, the bin index is clamped so the maximum lands in the last bin, the reported materiality statistic is the symmetric `max/min - 1`, and the directional form is computed only so the difference is inspectable |
| The two percentile conventions | Limitation 10 compares an interpolated percentile with a nearest-rank weighted one. They differ by 0.009% on that figure and agree to the cent at equal weights — four orders of magnitude inside the ±3.8% Monte Carlo error on a 95th percentile |
| Generator reproducibility | `results/` regenerates byte-identically; no unseeded RNG anywhere in the generating code, now pinned by a test |

**Two latent edge cases, inert at these parameters,** both reachable only through infinite costs and
both in superseded or diagnostic quantities rather than reported ones: `a/b` with `b` infinite scores
as material in `p_material_directional`, and `inf < inf` is False in `p_lt`.
