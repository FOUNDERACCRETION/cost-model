# What I did not fix, and why — 11 October 2026

Items from the fix list and the review rounds that were **not** applied as written. Each says what
was asked, what I found, and what I did instead. Nothing here was skipped for convenience; three of
them are cases where the request itself rests on a mistake, and I would rather you know that before
a referee finds it.

---

## 1. P0-1: "Leeman 3 of 43" — not applied, the denominator is theirs

**Asked:** change the Leeman success count from 3 of 58 to 3 of 43, and delete the clause naming
CaFe₂(PO₄)₂O as the only convincingly demonstrated success.

**Found:** both halves are wrong, verified against the PRX Energy text on 11 October 2026.

- Leeman et al. publish the denominator themselves: *"In this case, the success rate would be
  3/58, or 5%."* The 43 is the size of the set they inspected in detail — the 36 classed as
  successes plus seven partial successes — and they report significant issues with 42 of those 43.
  The two numbers do different work and are not alternatives.
- The CaFe₂(PO₄)₂O clause is supported verbatim: *"we have found significant issues with 42 of them
  (the exception being CaFe₂(PO₄)₂O)"* and *"Of those CaFe₂(PO₄)₂O seems to have been convincingly
  synthesized based on the provided PXRD data"*, with the other two described as too poorly fitted
  to judge.

**Did instead:** §2.3 now states both denominators and says what each one counts, so a reader cannot
confuse them. Using 3/43 would have raised the pessimistic success rate from 5.2% to 7.0% and cited
a figure the source does not publish.

---

## 2. P1-1: the chemistry sweep — I was wrong, now applied

**Asked:** state $w$ with the 4.0–30.7% chemistry sweep.

**What I said first, and why it was wrong.** I searched An et al. and Merchant et al., found no
such range, and wrote that no source reports the flip rate by chemistry. The source is your own
P2 audit, and I did not think to look there. The claim I put in the paper — "no source reports
the transition rate by chemistry" — was false, and it was false in a way that would have read as
carelessness to anyone who knew both papers were yours.

**Now applied.** §3.4 states $w = 16$% at base with 13.2% and 34.3% as the endpoints (it never
printed the base value before, which you also caught), and adds the chemistry range: a global
13.04% against the MP hull, with disjoint cells at fixed element count running 4.0% for
intermetallics with neither a lanthanide nor a 3d element to 30.7% for oxides with a 3d element
and no lanthanide, a 26.7 pp spread. The sweep is run through the model, not asserted: level-1
cost for pipeline B moves \$16.67 to \$23.09, a 39% spread, and level 2 does not move at all.

**That second column is worth more than the first.** A parameter that moves level-1 cost by 39%
and level-2 cost by nothing is the cleanest demonstration in the paper that $w$ cancels from cost
per validated material. The sweep now carries that argument, and a test pins it on the real
parameter file at the real cell endpoints.

**Attribution.** Reported as a companion analysis in preparation, not cited, since the repository
is private and nothing is posted. I also recorded three cautions in the text: it is an unrefereed
result of your own, though it widens the paper's uncertainty rather than narrowing it, which is
the conservative direction; the cells are disjoint classes at fixed element count, so the
endpoints are extremes of 23 cells rather than bounds on a material; and the companion's own
attribution of the gradient to Hubbard-$U$ list membership is contested within its analysis, so
nothing in P1 depends on the mechanism, only on the spread. Swap "in preparation" for a citation
once P2 posts, and re-check the direction if its numbers move in review.

---

## 3. P0-5: regrading the tuition term `published` — the premise was stale

**Asked:** the NRSA tuition value is the \$16,000 cap, so regrade it `published`, reducing the
`missing` parameters from three to two.

**Found:** the parameter file already had one `missing` parameter, not three — the manuscript's
claim of three was simply out of date. And by the paper's own taxonomy the tuition base should stay
`proxy`: `published` means "stated in the cited source", `proxy` means "a published number for a
related but not identical quantity", and the NRSA cap is a training-grant allowance standing in for
a charge on a research project. The number is published; the *use* is a proxy.

**Did instead:** §4.1 and Limitation 9 now give the real census (46 published, 14 first-hand, 13
derived, 8 proxy, 5 assumption, 1 figure-read, 1 missing), and the census is generated so the next
drift fails the build rather than sitting unnoticed.

---

## 4. Length — settled at working-paper length, and two free cuts taken

**Asked:** cut from 35 to 16 pages. **Settled:** you confirmed 16 was a journal target and that a
30-page working paper plus companion is fine, and that none of the four sections I named should go.

**You were right that my "floor" was overstated.** I said nearly every sentence carries a figure, a
citation or a caveat. Two classes of text carried none, and both are now cut:

- **Repeats.** The ordering finding (most successes ≠ cheapest) ran in the abstract, the
  contributions, §5.7 twice, §6.2 and the conclusion. The abstract, contributions and conclusion
  are the places that are *supposed* to repeat a headline; the two in-body restatements were not,
  and are gone. §6.2 also stated it twice inside one sentence, once by cross-reference and once in
  full.
- **Revision history.** "No longer", "the previous calibration", "has changed sign relative to", and
  "though no longer three" are all gone. They encode a diff against a draft no reader has seen, and
  your earlier instruction was to state warnings prospectively.

I also disambiguated three unrelated quantities the paper was calling "four": the filter benefit
under imported benchmark rates (4.0), the level-1 ratio between the generative and filtered
pipelines (4.02), and the recipe-mismatch factor (now written as 3.8, which is what it is). And the
identification-tier figures (33 → 71 or 15) are now labelled as computed on the deterministic
scenarios, where the uniform-tier spread is 33, against the Monte Carlo median factor of 30 quoted
elsewhere — two estimands the paper was calling "the factor" without distinction.

These do not get to 16 pages and were never going to. They remove about a page of text that was
doing no work.

---

## 5. Things the model still cannot do

**Not on this list: publishing the repository.** I had it here, and you are right that it does not
belong — it needs no data and no equipment, only a decision. §8 states that the repository is not
public and no DOI is minted, and that stays accurate only until you act on it. The same is true of
the P2 repository, which has to be public before that paper's printed URL resolves.

Unchanged from earlier rounds, restated so the list is in one place. None is a refusal; each needs
data or equipment this project does not have.

- **Lab cost validation.** No attempt cost has been checked against a laboratory's actual books.
- **Capital and utilisation.** No capital figure exists for an autonomous bulk solid-state platform,
  so the synthesis term cannot be decomposed into labour, consumables and amortised equipment. This
  is the largest unmodelled structure in the paper and Limitation 15 says so.
- **An MP-compatible DFT benchmark.** Our timings use Quantum ESPRESSO with ultrasoft
  pseudopotentials and cannot be placed on the Materials Project hull. This is the most consequential
  unresolved issue in the paper (Limitation 8) and it is why §5.4 reports crossings instead of a base
  case.
- **x86 and GPU benchmarks.** All first-hand timings are from one virtualised ARM64 laptop.
- **Target-level data.** The crosswalk that would confirm the four inconclusive A-Lab targets are not
  subtracted twice needs the annotated supplement.
- **Expert elicitation** on the readings' relative credibility, which is why they carry equal weight.

---

## 6. One caution carried forward from the verification pass

The Kusumegi figures in §2.2 (23.7% and 89.3%) were read from a third-party-hosted PDF because
science.org was unreachable, and that source contains an internal inconsistency — a supplementary
caption giving 37.7% where the main text gives 43.0% for one subgroup. **Re-check both figures
against the publisher version before submission.** `paper/VERIFICATION.md` records this and the
other claims that could not be closed.
