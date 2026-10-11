# Diagnostics moved out of the manuscript

Material that belongs to the model's provenance rather than to its results. An external reviewer
of revision 11 asked for the paper to be compressed, noting that the main results carried
"lengthy revision-history and numerical-check explanations". Those are recorded here instead of
being deleted, and each regenerates from the repository.

## The superseded materiality convention

Revisions up to and including 10 measured the simulated cost difference as
`|C_B/C_A − 1| > 0.10`, against the **dearer** pipeline, while the DFT threshold sweep measured
each pipeline's gap over the **cheaper** one. A exceeding B by 10% is B falling short of A by
9.09%, so the two sections' percentages were not comparable. Revision 11 unified both on
`analysis._ratio_gap` = `max/min − 1`.

Effect on the one figure that moved:

| Level, pair | Superseded (directional) | Current (symmetric) |
|:--|--:|--:|
| Level 1, B–A | 97.7% | 97.9% |
| Level 2, B–A | 0.5% | 0.9% |
| Level 3, B–A | 0.5% | 0.9% |

Both level-2 values display as 1% at the paper's precision, so the published table did not
change, but the number a reader reproduces did. The directional statistic is still computed and
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

- Worst relative residual **7.6 × 10⁻¹⁶**, across six verification costs up to 2,000 core-hours —
  twice the top of the swept range, so the fit is tested outside the interval it was fitted on
  (the coefficients are recovered from two probe points, which makes agreement at those two
  points trivial).
- `α_C/α_B` = 4.000000, exactly the purity ratio of §5.3.
- At τ = 0.10 the closed form returns **196.5733** and the model's bisected root returns
  **196.5733** — relative agreement 2 × 10⁻¹⁵, i.e. the same number. Revision 10's text said the
  closed form "returns 196.6 against the 197 the model solves numerically", implying a mismatch
  that does not exist; 197 was only the rounded display.
- Substituting the **printed** (rounded) coefficients gives 196.39, a shift of 0.18 core-hours.
  This is the only source of disagreement between the paper's figures and a reader's
  recomputation from them.
- Synthesis bill at base, `b = ra` = \$1,676.05.

Roots and denominators at the three reported thresholds:

| τ | closed form | numerical root | denominator | usable |
|--:|--:|--:|--:|:--|
| 0.05 | 96.4264 | 96.4264 | 0.865592 | yes |
| 0.10 | 196.5733 | 196.5733 | 0.850921 | yes |
| 0.20 | 407.5972 | 407.5972 | 0.821579 | yes |

A positive denominator is necessary but not sufficient: the root must also be nonnegative to lie
in the domain `d ≥ 0`. The boundary is at `b = (β_C − (1+τ)β_B)/τ`; below it the formula returns a
negative `d*` with a positive denominator, meaning the gap already exceeds τ at zero verification
cost and there is no crossing to quote. Pinned by
`test_positive_denominator_is_not_sufficient_for_a_usable_crossing`.

## Overlap-coefficient bin sensitivity

Full sweep in `results/overlap_bin_sensitivity.csv`. A–B overlap:

| bins | 20 | 40 | 60 | 120 | 240 |
|:--|--:|--:|--:|--:|--:|
| Level 1 | 90.6% | 89.9% | 89.4% | 88.8% | 87.8% |
| Level 2 | 98.5% | 98.5% | 98.6% | 97.7% | 97.1% |

Beyond the reported range, level-1 A–B overlap falls to 80.2% at 2,000 bins and 53.4% at 20,000
bins against 20,000 draws.

**Two generalisations revision 11 asserted and revision 12 does not**, both corrected by the
reviewer:

1. *Weakly decreasing in bin count.* True only for **nested** refinements, where each coarse bin
   divides exactly into fine ones. 20 → 60 → 240 is nested (×3 then ×4); 40 → 60 is not (×1.5),
   and its direction is not guaranteed. On these draws it happens to decrease (89.93% → 89.43%),
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
