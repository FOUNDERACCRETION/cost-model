# Diagnostics moved out of the manuscript

Material that belongs to the model's provenance rather than to its results. An external reviewer
of revision 11 asked for the paper to be compressed, noting that the main results carried
"lengthy revision-history and numerical-check explanations". Those are recorded here instead of
being deleted.

**On 18 October 2026 this file said each of these regenerates from the repository. That was not
true of the file itself.** `scripts/audit_numbers.py` is pointed at the manuscript and its
appendices only, so nothing checked this document, and 27 of its roughly 45 generated figures had
gone stale --- a whole section of threshold roots computed from a synthesis bill 6.2 times too
large, two overlap tables off by up to 1.6 percentage points, and one conclusion that the stale
figures had inverted. They are corrected below, each marked. The figures here are copied from the
generated artefacts by hand and are therefore exactly as reliable as the last person to copy them;
`results/key_numbers.json` and `results/threshold_coefficients.json` are the sources, and this file
is now covered by the retired-value guard in `tests/test_structure.py` so that a figure the model
has stopped producing cannot sit here unnoticed again.

## The superseded materiality convention

Revisions up to and including 10 measured the simulated cost difference as
`|C_B/C_A − 1| > 0.10`, against the **dearer** pipeline, while the DFT threshold sweep measured
each pipeline's gap over the **cheaper** one. A exceeding B by 10% is B falling short of A by
9.09%, so the two sections' percentages were not comparable. Revision 11 unified both on
`analysis._ratio_gap` = `max/min − 1`.

Effect on the one figure that moved:

| Level, pair | Superseded (directional) | Current (symmetric) |
|:--|--:|--:|
| Level 1, B–A | 97.9% | 98.1% |
| Level 2, B–A | 8.9% | 10.0% |
| Level 3, B–A | 8.9% | 10.0% |

The two level-2 values do **not** display the same at the paper's precision --- 9% against the 10%
the paper prints --- so the published table changed as well as the number a reader reproduces.
*Corrected 2026-10-18: this table was stale by a whole run and the column was shifted, with level
1's directional value sitting in the current column; the previous text concluded from the stale
figures that "both level-2 values display as 1%, so the published table did not change", which was
the opposite of the truth.* The directional statistic is still computed and
exported as `p_material_directional` (keys `kill_l*_material_BA_directional`) so the size of the
correction stays inspectable.

Every crossing is unchanged, because B is the cheapest pipeline at every point in the swept
range. That is asserted by the generated key `sweep_b_cheapest_everywhere` rather than assumed.

## Threshold-fit numerical checks

Unrounded coefficients of `c₀ᵢ(d) = αᵢd + βᵢ`, archived in `results/threshold_coefficients.json`:

| | α (\$/core-h) | β (\$) |
|:--|--:|--:|
| A | 0.4847826087 | 0.0006416897 |
| B | 0.2934210526 | 0.0015626629 |
| C | 1.1736842105 | 0.3381360265 |

- Worst relative residual **6.3 × 10⁻¹⁶**, across six verification costs up to 2,000 core-hours —
  twice the top of the swept range, so the fit is tested outside the interval it was fitted on
  (the coefficients are recovered from two probe points, which makes agreement at those two
  points trivial).
- `α_C/α_B` = 4.000000, exactly the purity ratio of §5.3.
- At τ = 0.10 the closed form returns **31.4097** and the model's bisected root returns
  **31.4097** — relative agreement 3 × 10⁻¹⁶, i.e. the same number. Revision 10's text said the
  closed form "returns 196.6 against the 197 the model solves numerically", implying a mismatch
  that does not exist; 197 was only the rounded display, and both of those figures belong to the
  superseded synthesis bill below.
- Substituting the **printed** (rounded) coefficients gives 31.3812, a shift of 0.029 core-hours.
  This is the only source of disagreement between the paper's figures and a reader's
  recomputation from them.
- Synthesis bill at base, `b = ra` = \$270.64.

*Corrected 2026-10-18.* Every figure in this section that depends on the synthesis bill was stale
by one run. The bill was \$1,676.05 before the base case moved to the middle reading's single
recipe per target on 11 October; it is \$270.64 now, and `d* = [(1+τ)β_B − β_C + τb] /
[α_C − (1+τ)α_B]` carries that change straight into every root. Substituting the old bill
reproduces the superseded 96.4264 / 196.5733 / 407.5972 exactly, which is how the figures were
confirmed to be one propagated value rather than seven separate errors. The coefficients themselves, the
denominators and the residual check never depended on the bill, which is why they survived — and
is why the block read as though it were current.

Roots and denominators at the three reported thresholds:

| τ | closed form | numerical root | denominator | usable |
|--:|--:|--:|--:|:--|
| 0.05 | 15.2442 | 15.2442 | 0.865592 | yes |
| 0.10 | 31.4097 | 31.4097 | 0.850921 | yes |
| 0.20 | 65.4726 | 65.4726 | 0.821579 | yes |

A positive denominator is necessary but not sufficient: the root must also be nonnegative to lie
in the domain `d ≥ 0`. The boundary is at `b = (β_C − (1+τ)β_B)/τ`; below it the formula returns a
negative `d*` with a positive denominator, meaning the gap already exceeds τ at zero verification
cost and there is no crossing to quote. Pinned by
`test_positive_denominator_is_not_sufficient_for_a_usable_crossing`.

## Overlap-coefficient bin sensitivity

Full sweep in `results/overlap_bin_sensitivity.csv`. A–B overlap:

| bins | 20 | 40 | 60 | 120 | 240 |
|:--|--:|--:|--:|--:|--:|
| Level 1 | 90.8% | 90.4% | 89.6% | 88.9% | 87.7% |
| Level 2 | 97.4% | 97.3% | 97.1% | 96.6% | 95.5% |

Beyond the reported range, level-1 A–B overlap falls to 79.2% at 2,000 bins and 52.6% at 20,000
bins against 20,000 draws.

**Two generalisations revision 11 asserted and revision 12 does not**, both corrected by the
reviewer:

1. *Weakly decreasing in bin count.* True only for **nested** refinements, where each coarse bin
   divides exactly into fine ones. 20 → 60 → 240 is nested (×3 then ×4); 40 → 60 is not (×1.5),
   and its direction is not guaranteed. On these draws it happens to decrease (90.36% → 89.61%),
   so the monotonicity across the sweep is an observation, not a theorem.
2. *Falls towards zero as bins approach the sample size.* Not a property of the statistic. Two
   samples with identical values have identical histograms at any bin count and retain overlap
   exactly 1 — verified at 20, 240, 2,000 and 20,000 bins in
   `test_overlap_does_not_approach_zero_for_identical_samples`. The decline observed here holds
   because A and B differ in nearly every draw, which is a fact about these pipelines.

## Invariances that must not be re-asserted away

Two parameters cancel from the paired pipeline comparison. Both have been claimed as levers in
earlier drafts and both claims were withdrawn; each now has a test, because a cancelled parameter
is easy to reintroduce in prose.

| Parameter | Why it cancels | Withdrawn in | Test |
|:--|:--|:--|:--|
| `w`, cross-functional stable-to-unstable transition rate | level-1 cost `c` is per robust prediction, so `c₀ = (1−w)c` and the factors cancel in `C = (c₀ + ra)/S` | revision 7 (the verification-accuracy result) | `test_level2_is_independent_of_w` |
| `S`, unconditional synthesis success | shared across pipelines, so it cancels from `(c₀C + ra)/(c₀B + ra)` and appears nowhere in `d*` | revision 12 (a prose claim in revision 11's §5.6) | `test_the_crossing_does_not_depend_on_synthesis_success` |

The second is the more instructive failure: revision 11 reintroduced an `S`-dependence claim in
the prose of the very section that proves `S` cancels, within one revision of having withdrawn
the structurally identical `w` claim. Sweeping `S` over 0.052–0.632 moves neither crossing in the
twelfth significant figure.

## Transcription errors found by machine, not by reading

Revision 11 added an audit that extracts every numeric string in the manuscript and checks it
against `results/key_numbers.json`. On its first run against revision 10 it found three errors
that had survived every prose review:

| Claim | Printed | Generated | Places |
|:--|--:|--:|--:|
| P(B < A), all three levels | 99.5% | 99.4% | 5 |
| Level-2 B–A overlap | 98% | 99% | 1 |
| Level-2 tornado share | 98.8% | 98.6% | 1 |

Revision 12 added a fourth of the same kind: the title page of revision 11 still read "revision
10". None changes a conclusion; all are numbers retyped from an earlier run rather than
regenerated. **This check belongs in the build.**

Related: `pct()` was rounding a probability of 0.995 up to "100%", asserting a certainty the
simulation never found. It now gains decimal places instead of printing 100% for anything short
of certainty, or 0% for anything above zero.

---

# Software validation moved out of the manuscript

The manuscript states results. The checks that establish the implementation computes those results
correctly live here, because they are properties of the software rather than findings about
materials discovery. Each regenerates from the repository.

## Threshold fit

- Worst relative residual of `c0i(d) = αi·d + βi` against the model: **6.3 × 10⁻¹⁶**, evaluated at
  six verification costs up to 2,000 core-hours — twice the top of the swept range, so affinity is
  checked outside the interval the two-point recovery was fitted on.
- Unrounded coefficients, residual table and root comparison: `results/threshold_coefficients.json`.
- Closed form against the model's bisected root at τ = 0.10: **31.4097 vs 31.4097**, relative
  agreement 2 × 10⁻¹⁵. They are the same number, as they must be if the relation is affine.
- Substituting the *rounded* printed coefficients instead gives **31.3812** — a shift of 0.029
  core-hours. This is the only source of disagreement between the paper's printed figures and a
  reader's recomputation from them.
- `α_C/α_B = 4.000000`, exactly the purity ratio of §5.3, asserted to 1e-9 by
  `test_threshold_coefficient_archive`.
- Usable-crossing condition: a positive denominator is necessary but not sufficient; the root must
  also be nonnegative. Boundary at `b = (β_C − (1+τ)β_B)/τ`, pinned by
  `test_positive_denominator_is_not_sufficient_for_a_usable_crossing`.

## Overlap reference

`analysis.overlap_reference` draws two independent bootstrap samples, with replacement and of the
original size, from one pipeline's own draws, so true overlap is 1 by construction. **60
replicates** on the same equal-width log₁₀ grid `kill_condition` uses, spanning the pooled finite
positive range of all three pipelines at that level.

| | Measured | Reference range | Position |
|:--|--:|:--|:--|
| Level 1 | 90% | 96.1%–97.9% | below |
| Level 2 | 97% | 97.0%–98.3% | inside |

*Corrected 2026-10-18.* Both rows were stale and the level-2 row was wrong in kind, not only in
value: its measured 99% is level 3's figure, and the "above" verdict was false. Level 2's measured
overlap of 97.05% sits **inside** the reference band, 0.06 percentage points above its floor of
96.99%. The file asserted that the level-2 marginals are more alike than independent resampling
would make them; they are statistically indistinguishable from it. That is a weaker claim than the
one the file made, and the right one.

The replicates are independent pairs; the measured A and B samples are dependent, sharing parameter
draws. That dependence is not reproduced, is not modelled, and its direction is not asserted. The
reference is a yardstick for finite-sample histogram variability, not a null distribution, and no
p-value is computed anywhere in the module.

Bin-count sweep, A–B overlap:

| bins | 20 | 40 | 60 | 120 | 240 |
|:--|--:|--:|--:|--:|--:|
| Level 1 | 90.8% | 90.4% | 89.6% | 88.9% | 87.7% |
| Level 2 | 97.4% | 97.3% | 97.1% | 96.6% | 95.5% |

Beyond the reported range the level-1 figure falls to 80.2% at 2,000 bins and 53.4% at 20,000 bins
against 20,000 draws. Those values are reported here and not in the paper, because at that
resolution the coefficient is dominated by sample sparsity: two independent samples from an
identical distribution score 0.60 at 20,000 bins.

## Test suite

756 tests. The ones that guard against specific past failures:

| Test | Guards |
|:--|:--|
| `test_level2_is_independent_of_w` | `w` cancels from level 2, at interior values, and is still live at level 1 |
| `test_the_crossing_does_not_depend_on_synthesis_success` | `S` cancels from `d*`, swept over the full range of the three readings |
| `test_materiality_is_symmetric_and_matches_the_sweep_convention` | one denominator convention across sweep and simulation |
| `test_parity_and_materiality_boundaries_are_distinct_and_both_correct` | each boundary delivers the gap it claims; materiality is >3× parity at base |
| `test_success_ratio_boundaries_are_checked_against_the_probability_ceiling` | a ratio is attainable only while the implied rate stays ≤ 1 |
| `test_feasibility_ceiling_moves_with_the_reading` | the ceiling is 1/S_base and depends on which reading sets it |
| `test_matching_purity_does_not_quite_equalise_the_pipelines` | residual equals the β gap over Q_B, not over the bill |
| `test_overlap_decreases_under_nested_refinement_only` | monotonicity holds for nested refinements only |
| `test_overlap_does_not_approach_zero_for_identical_samples` | identical samples retain overlap 1 at any bin count |
| `test_overlap_null_floor_calibrates_the_coefficient` | marginal overlap is invariant to pairing; the paired statistic is not |
| `test_the_current_manuscript_passes_the_numeric_audit` | every printed figure matches the model or is waived with a reason |
| `test_the_manuscript_revision_label_matches_its_filename` | title-page label matches the file |
| `test_reconstruction_worksheet_reproduces_the_attempt_cost` | the worksheet's printed components sum to its printed subtotal |

Both cancellation tests also assert the parameter remains live where it should act, so neither can
pass by the quantity having been dropped from the model.
