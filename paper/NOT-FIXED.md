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

## 2. P1-1: the "4.0–30.7% chemistry sweep" — the range is in neither source

**Asked:** state $w$ with the 4.0–30.7% chemistry sweep.

**Found:** that range appears in neither cited source. An et al. (arXiv:2607.01713) give only two
single-compound examples (NiCl₃, BaI₂ polymorphs) and no class-level rates; Merchant et al. break
down by *number of elements*, not chemistry. I could not find a published transition rate by
chemical system anywhere.

**Did instead:** §3.4 and Appendix A.4 now state the provenance of all three values of $w$ and say
explicitly that no source reports the rate by chemistry, so the model does not vary $w$ by chemical
system and §5.10 claims no such test. The underlying review point — that $w$ was never sourced — is
addressed. Checking it also turned up a real defect: the high value of 34.3% is **our** subtraction
from a figure An et al. never present as a flip rate, computed over a population pre-screened on
dynamical stability, with the higher functional never run on the candidates eliminated earlier. That
is now stated in both the paper and the parameter file.

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

## 4. The 16-page target — not reached, and I think it conflicts with your other instructions

**Asked:** cut from 35 to 16 pages.

**Where it stands:** 30 pages for the main paper plus a 9-page companion holding the appendices and
supplements, against 40 before this round. Every table, equation, quotation and citation survived,
and the numeric audit spans both files.

**Why not 16.** Moving material to a companion redistributes pages, it does not remove them. The
remaining body is about 14,000 words in which nearly every sentence carries a figure, a citation or
a caveat, and your standing instruction is that substantive methodological warnings survive
compression. Three independent compression passes each hit the same floor and each reported it.
Reaching 16 pages means **deleting** roughly half the body, not tightening it. If that is what you
want, the honest candidates, in the order I would cut them:

1. **§5.5's tolerance apparatus** (~1,100 words) reduced to two sentences giving the 16.9% and 3.85%
   boundaries. Cost: the paper loses its answer to "how far does the shared-synthesis assumption
   have to fail", which is currently its best response to Limitation 1.
2. **Supplements S1 and S2** (~1,000 words) dropped to the repository. Cost: S1 is a genuinely novel
   observation and the only part of the paper addressed to the benchmark literature.
3. **§5.6's Monte Carlo** (~660 words) reduced to its table and two sentences. Cost: the
   crossing-versus-prior-mass distinction goes, and that is a real methodological contribution.
4. **§4.2's benchmark detail** and **§6.3's platform-cost discussion** (~700 words combined).

My recommendation is not to. A 30-page working paper is unremarkable on SSRN, and the apparatus is
what makes the central claim — that the evidence cannot support a general cost figure — defensible
rather than assertive. But it is your paper and the call is yours; say which of the four and I will
cut them.

---

## 5. Things the model still cannot do

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
- **Publishing the repository.** §8 states plainly that it is not public, no DOI is minted, and
  nothing has been independently reproduced.

---

## 6. One caution carried forward from the verification pass

The Kusumegi figures in §2.2 (23.7% and 89.3%) were read from a third-party-hosted PDF because
science.org was unreachable, and that source contains an internal inconsistency — a supplementary
caption giving 37.7% where the main text gives 43.0% for one subgroup. **Re-check both figures
against the publisher version before submission.** `paper/VERIFICATION.md` records this and the
other claims that could not be closed.
