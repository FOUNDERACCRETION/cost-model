---
title: "Appendices and Supplements"
subtitle: "Companion to \"What Does It Cost to Validate a Predicted Inorganic Material?\""
author: "Karthikeya"
date: "Working paper --- 11 October 2026"
documentclass: article
classoption:
  - 11pt
geometry:
  - a4paper
  - margin=2.6cm
mainfont: "FreeSerif"
sansfont: "FreeSans"
monofont: "DejaVu Sans Mono"
monofontoptions: "Scale=0.85"
linestretch: 1.1
colorlinks: true
linkcolor: black
urlcolor: RoyalBlue
citecolor: RoyalBlue
link-citations: true
reference-section-title: "References"
header-includes:
  - \usepackage{booktabs}
  - \usepackage{microtype}
  - \renewcommand{\arraystretch}{1.15}
---

This companion carries the derivations, parameter provenance and diagnostics that the main paper
cites but does not reproduce. Section numbers refer to the main paper. Nothing here is a separate
finding.

# Appendix A. Derivations and robustness detail

Material a reader checking the arithmetic needs, moved out of Section 5 so the results read as
results. Nothing here is a separate finding.

## A.1 The verification-cost crossing in closed form

**Where the crossing comes from.** Upstream compute expenditure per candidate reaching synthesis is affine in DFT cost $d$ (in core-hours per candidate):

$$c_{0i}(d) \;=\; \alpha_i\,d + \beta_i$$

where $\alpha_i$ (dollars per core-hour) carries the compute price and the number of candidates verified per candidate reaching synthesis, and $\beta_i$ (dollars) collects generation, filtering and any cost independent of $d$. Fitting against the model gives $\alpha = 0.485$, $0.293$ and $1.174$ \$/core-h and $\beta = 0.0006$, $0.0016$ and $0.338$ \$ for A, B and C. The relation is affine, and the coefficients printed here are rounded; the unrounded values, the residuals and the range over which affinity was checked are in the replication package. The ratio $\alpha_C/\alpha_B$ is exactly 4.0, the purity ratio of Section 5.3, which is an identity rather than an artefact of rounding.

Writing $b = ra$ for the shared synthesis expenditure per target, \$271 at base, $(C_C - C_B)/C_B = \tau$ gives

$$d^{*} \;=\; \frac{\tau b + (1+\tau)\beta_B - \beta_C}{\alpha_C - (1+\tau)\,\alpha_B}$$

A positive denominator is necessary but not sufficient for a usable crossing: the solution must also be nonnegative, since $d$ is a verification cost and negative values are outside the domain. A negative $d^{*}$ with a positive denominator means the gap already exceeds $\tau$ at zero verification cost, so there is no crossing to report and the formula returns a number to discard. At our parameters both conditions hold: the denominator is 0.851 and $d^{*}$ is positive at every threshold we report.

At $\tau = 0.10$ this returns the 31.4 core-hours quoted above. Reproducing it from the rounded coefficients shifts the answer by 0.03 core-hours, so the replication package carries the unrounded values.

The threshold is therefore **affine in the synthesis bill, not proportional to it**. The intercept terms contribute 1.3% of the numerator of $d^{*}$ at our parameter values, because generation and filtering cost cents against a synthesis bill of hundreds of dollars, so the crossings move nearly in proportion to attempt cost across the accounting variants below. That near-proportionality is a property of these parameters, not an identity, and it is weaker here than under a larger synthesis bill: the intercept share scales inversely with $b$, so a campaign reporting several recipes per target would push it back towards zero, and a pipeline with a large $d$-independent cost would break it in the other direction.

| Accounting basis | \$ per attempt | Generative, 10% | Filter, 10% |
|:--|--:|--:|--:|
| Direct costs only | 191 | 22 | 118 |
| Effective 42% on an MTDC-like base | 213 | 25 | 131 |
| Effective 42% on total direct costs (default) | 271 | 31 | 167 |
| Negotiated 58% on total direct costs | 301 | 35 | 186 |

Both crossings stay inside the tested range under every accounting treatment we carry, so neither decision can be called immaterial as a general property of the model: the generative crossing moves only between 22 and 35 core-hours and the filter crossing between 118 and 186. What the accounting choice changes is the size of the crossing, not whether there is one. Across the four treatments the attempt cost rises by 58% and both crossings rise by 58 to 59%, which is the near-proportionality the closed form above explains.

This is why we report thresholds rather than a single immateriality claim. The quantity that decides them is the one Section 4.3 says we cannot pin down, and the second quantity that decides them is an accounting choice.

## A.2 The joint boundary region

**Each boundary varies one synthesis quantity while holding the others fixed**, so these are not joint robustness bounds. The general ratio carries the joint condition: the gap between C and B exceeds $\tau$ whenever

$$\frac{Q_C}{Q_B}\cdot\frac{S_B}{S_C} \;>\; 1 + \tau \qquad\text{or}\qquad \frac{Q_C}{Q_B}\cdot\frac{S_B}{S_C} \;<\; \frac{1}{1 + \tau}$$

with $Q_i = c_{0i} + r_i a_i$. Evaluated over a grid of the two ratios at base, the region where the 10% gap is exceeded is not the union of the one-at-a-time boundaries:

| $S_C/S_B$ \\ $r_C/r_B$ | 0.90 | 0.95 | 1.00 | 1.05 | 1.10 | 1.20 |
|:--|:--:|:--:|:--:|:--:|:--:|:--:|
| 0.90 | **19%** | **25%** | **30%** | **35%** | **40%** | **51%** |
| 0.95 | **13%** | **18%** | **23%** | **28%** | **33%** | **43%** |
| 1.00 | 7.4% | **12%** | **17%** | **22%** | **26%** | **36%** |
| 1.05 | 2.3% | 6.8% | **11%** | **16%** | **20%** | **29%** |
| 1.10 | 2.4% | 2.0% | 6.2% | **11%** | **15%** | **23%** |
| 1.20 | **12%** | 7.0% | 2.7% | 1.3% | 5.3% | **13%** |

Each cell is the gap $\max/\min - 1$ between C and B, bold where it exceeds 10%; because the convention is symmetric, a large gap in the bottom-left corner means C has become materially *cheaper*, not dearer. The immaterial region is a narrow diagonal band, and it does not contain the origin of the grid: at equal synthesis behaviour C is 17% dearer, so staying inside 10% requires generative candidates to succeed more often *and* need no more recipes. The band's width is what the one-at-a-time columns cannot show. A pipeline whose candidates succeed 10% more often sits at a 6.2% gap with equal recipes, but at an 11% gap if it also needs 5% more recipes --- differences in the same direction compound, and in opposite directions they cancel. A reader with a view about both quantities should evaluate the condition rather than read either boundary alone.

## A.3 The parity boundary under parameter variants

| Variant | $S_C/S_B$ for parity | implied $S_C$ | Extra recipes for parity, share of baseline |
|:--|--:|--:|--:|
| Base | 1.169x | 34.1% | 3.85% |
| Generative purity at pool purity, 15.2% | 1.001x | 29.2% | 3.85% |
| Generative purity at 2.4%, near the feasibility floor | 1.299x | 37.9% | 3.85% |
| Compute price 10x | 2.115x | 61.7% | 38.53% |
| Compute price 100x | 3.566x | **104.0%: parity infeasible** | 385.33% |
| DFT cost at the span top, 1,000 core-h | 2.561x | 74.7% | 70.71% |

**An algebraic boundary is not automatically a feasible probability.** A success *ratio* is attainable only while the success *rate* it implies stays within $[0, 1]$, so every interval above must be intersected with that range. At the base reading's $S_B$ of 29.17% the admissible ceiling on the ratio is $1/S_B = 3.429$, and one variant breaches it: at a hundredfold compute price, parity would need $S_C = 104.0\%$, which no campaign can reach. That row states a cost relationship with no attainable synthesis counterpart, and we label it rather than let the number stand. Every row of the main table is feasible at this baseline, the largest implied rate being 74.7%. Feasibility is reading-dependent, because the ceiling moves with $S_B$: under the optimistic reading's 63.2% the ceiling falls to 1.583, so the upper materiality bound of 2.817 at the top of the DFT span would be infeasible there, implying 177.9%; under the pessimistic reading's 5.2% the ceiling rises to 19.3 and nothing in either table is constrained. The lower ceiling at a higher success rate is not a paradox: a pipeline already succeeding two times in three has less room to improve, so the same cost gap demands a success advantage it cannot deliver.

**What the parity tolerances are measuring.** They express the compute-cost difference between two pipelines relative to the shared synthesis expenditure $ra$. They shrink as computation gets cheaper, holding synthesis inputs fixed, and widen with compute price and verification cost; they also depend on the synthesis baseline, since $ra$ is the denominator and the relative recipe tolerance is divided by $r$. Setting generative purity to the pool's takes the required success advantage to 1.001174 rather than to one exactly: matching purity equalises the slope $\alpha$ but not the intercept $\beta$, and C still pays \$0.34 per target of generation cost that B does not --- 0.1174% of the ratio, which rounds to 1.001 but is not zero. That residual is six times larger than under a multi-recipe synthesis baseline, for the same reason the intercept share of the crossing is: the \$0.34 is measured against a smaller synthesis bill. The filter boundary does not move with generative purity at all, as it should not, since neither A nor B draws from that pool. A purity below about 2.3% is not admissible: at the generative pool's 3.0% prevalence and the filter's recall it would imply a pass fraction above one, and the model rejects it, so the downward variant is the largest the model admits rather than an arbitrary choice.

## A.4 Parameter provenance: the optimistic count, the disagreement rate, and identification cost

**Which optimistic value, and why 36 of 57.** The A-Lab campaign supports several success counts. Because the model takes unconditional rates, the choice is narrower than it would otherwise be, but it still moves the optimistic branch.

| Count | Value | What it includes |
|:--|:--|:---------------|
| 36 / 57 | 63.2% | The corrected figure, unconditional. **Used.** Includes the three targets that failed for computational reasons, as an unconditional rate should. |
| 36 / 54 | 66.7% | Excludes the three computational failures, so it is a conditional rate and overstates unconditional success unless a separate failure multiplier is applied. |

Three things about that ratio are worth stating, because the published record is in two versions. The 2023 article reports 41 realised of 58 targets. The corrected article reports 36 of 57, and those are the numbers we use. The correction *notice* publishes neither total: it states that the platform reached the correct conclusion in 36 of its 40 reported successes, that four compounds are inconclusive from diffraction alone, and that one further compound was removed as training data, from which 41 − 1 − 4 = 36 and 58 − 1 = 57 both follow. So 57 is the original target count less the removed compound, not a number the 2023 article prints. The 36/54 rate excludes computationally attributed failures and therefore does not estimate unconditional campaign success; it would be the right quantity only alongside a separate computational-failure multiplier, which the model does not apply.

We considered and discarded counts that add the two targets realised only after an operator reground and reheated the products. No published document states such a total, so any version of it is our own composite; the intervention is outside the autonomous protocol being costed, and the model charges none of the extra labour it took.

Two cautions follow. The ratio should be cited to the corrected article rather than to the correction notice, which publishes no total. And the target-level crosswalk that would confirm the four inconclusive targets are not subtracted twice is still outstanding. We therefore treat 36/57 as a proposed baseline rather than a settled count, and a reader who reconstructs it differently from the same two documents is not contradicting a published figure.

**Where the three values of $w$ come from, since this parameter is easy to assert and hard to source.** The base and low values are published: @merchant2023gnome report that 84% of discovered binaries and ternaries present negative phase-separation energies and that 86.8% of tested quaternaries remain stable on the r2SCAN hull, giving 16% and 13.2%. Those are two different tests rather than one metric split by composition arity, and we use the pair as a range rather than averaging them. The high value, 34.3%, is weaker and we grade it accordingly: @an2026 report that of 166 *dynamically stable* candidates, 109 sit below 1 meV/atom on the SCAN hull, and the complement is our own subtraction, which that paper does not present as a flip rate. It is also not a flip rate over all PBE-stable candidates, because the higher functional was not run on those eliminated earlier, and its population is pre-screened on dynamical stability while the other two endpoints are not. We found no source reporting the transition rate by chemistry, only by number of elements, so the model does not vary $w$ by chemical system and Section 5.10 does not claim to have tested that dependence. Because $w$ enters only level 1 and cancels from level 2, the weakness of its upper endpoint does not propagate to the paper's headline figures. The underlying error scale is well documented: GGA formation-energy errors against experiment are of order 0.1 eV/atom [@kirklin2015oqmd]; surrogate models inherit and compound them [@bartel2020]; corrections reduce but do not eliminate them [@wang2021corrections]; and about half of ICSD-reported compounds sit above the computed hull at all [@sun2016metastability].

**Identification cost: bounding the tier.** The tier the model charges uniformly is the internal service rate of \$80.00 per sample. We found no published fee for a refinement-grade determination, so rather than invent one we bound the effect with the three tiers the fee schedules do supply --- \$5.00 self-use, \$80.00 internal service, \$150 external service. Changing the tier for all three readings together moves the level by $-37$% to $+35$% and leaves the spread between readings untouched, because the charge is shared. Tying each reading to its own tier is what moves the spread: the factor between the dearest and cheapest readings is 33 at a uniform tier, 71 if the strictest reading pays the dearest tier and the most lenient the cheapest, and 15 under the reverse assignment. Which assignment is right is an assumption; that the uniform tier understates the spread under the plausible one is not.

## A.5 Rounding policy and accounting detail

**Rounding and precision.** Because several figures in Section 5 are solved rather than measured, they can be printed to more digits than they deserve, and the paper would mislead if it printed them without saying which digits are meaningful. The policy, applied throughout:

- **Dollar figures per output are rounded to two significant figures** (\$1,000, not \$1,019). None of the inputs supports more: the attempt cost rests on an assumed throughput, and the verification cost spans two and a half orders of magnitude. Unrounded values are in the replication package.
- **Shares of cost and relative gaps are printed to one decimal place** (16.9%, 3.6%). The decimal distinguishes quantities compared against a 10% convention, and nothing turns on it: 16.9% and 17% carry the same conclusion.
- **Break-even boundaries are printed to the precision needed to reproduce the solve** (1.169, 3.85%), because a reader checking the arithmetic against the equation needs the digits the equation consumed. They are not claims about the world to that precision; each inherits the full uncertainty of the synthesis bill it is measured against.
- **Crossings in core-hours are rounded to two significant figures** (31, 170, 410), and the distribution around each is reported alongside, since the point estimate is the least informative thing about it.
- **Threshold coefficients are printed rounded and reproduced unrounded** in the package, because recomputing the crossing from the rounded coefficients shifts it, and Section 5.4 quantifies that shift rather than hiding it.

No figure in this paper is quoted to more digits than the generator produces, and the build fails if a printed figure drifts from the model, so the precision shown is the precision computed --- which is not the same as the precision warranted, and this policy is the distinction.

**The MTDC base.** We call the narrowed variant *MTDC-like* rather than MTDC, and the distinction is worth stating because the regulation is explicit. Modified total direct cost is defined as "all direct salaries and wages, applicable fringe benefits, materials and supplies, **services**, travel, and up to the first \$25,000 of each subaward", excluding equipment, capital expenditures, patient care, rental costs, tuition remission, scholarships and fellowships, participant support, and subaward amounts above \$25,000 [@cfr2001]. So excluding tuition is MTDC; excluding service-centre fees is not, because the definition names services as part of the base. The same section adds that other items "may only be excluded when necessary to avoid a serious inequity in the distribution of indirect costs, and with the approval of the cognizant agency for indirect costs" --- which is to say the regulation anticipates an exclusion of this kind and makes it a case to be approved, not a definition to be applied.

Our reasoning for testing it is that federal rules direct recharge rates to be composed of direct costs and an allocable share of indirect costs [@cfr200468], so applying institution-wide overhead on top risks counting some of it twice. We treat that as a hypothesis rather than a demonstrated fact: the rule does not establish that any particular facility's fee schedule absorbs the same cost pools an institution-wide rate covers, and we have not inspected those pools. It is a scenario in the table of Section 4.5 rather than the default, for two reasons --- pairing an effective rate with a narrowed base is a rate/base mismatch whatever the merits of the exclusion, and the exclusion is not one the definition grants.

**A social-cost perspective.** A social-cost perspective would differ again, in both directions: it would strip out transfers that are not resource use, tuition remission being partly one, and add consumption of resources nobody is billed for. We do not attempt it, and we flag that the first of those adjustments would *lower* the figure, so a reader should not assume every unmodelled term points upward.

# Supplement

Material that the main argument does not rest on. S1 is an uncontrolled comparison retained because the discrepancy is worth recording; S2 is a diagnostic whose decision value is lower than the paired statistics it accompanies.

## S1. An illustrative cross-setting discrepancy in filter enrichment

The discovery acceleration factor (DAF) is the ratio of a filter's precision to its pool's prevalence --- how many times more often a filter-passed candidate is stable than a random one. @riebesell2025 define it this way, so the comparison requires no assumption about which classifier rate transfers. The filter is CHGNet in both settings: @szymanski2025baselines state that they "used CHGNet to compute the internal (0 K) energies of all candidate materials", and 3.36 is CHGNet's reported value on the benchmark test set. The comparison is therefore matched on model family. Neither source names a version or checkpoint, so we do not claim identical fitted models.

| Pool | Stable fraction | Purity after filter | DAF |
|:-----|:-----|:--|--:|
| Benchmark test set (unique prototypes), CHGNet [@riebesell2025; @riebesell2025correction] | 15.3% (32,942 of 215,488) | --- | 3.36 |
| Ion-exchange pool, CHGNet [@szymanski2025baselines] | 9.2% | 15.2% | **1.65** |
| Generative pool, CHGNet [@szymanski2025baselines] | 3.0% | 3.8% | **1.27** |

On a realistically constructed ion-exchange pool, enrichment is 1.65 against the 3.36 reported. On the generative pool it is 1.27: the filter barely enriches at all. Because the acceleration factor depends on prevalence, applying the benchmark's own rates at each pool's prevalence gives a prevalence-adjusted comparison, 1.65 against 4.05 --- a larger gap still. This adjustment assumes the benchmark's classifier rates transfer to our pools, which is the assumption the rest of this section questions, so we report it as a calculation under that assumption rather than as a like-for-like measurement.

The mechanism, which rests on an assumption, is that if the benchmark's recall transfers, measured purity implies a false-positive rate of 0.43 on the ion-exchange pool against 0.13 on the benchmark. The alternative attribution requires recall of 0.23 on our pool. We cannot rank these two against each other: recall is a population-specific quantity and both values can be correct for their own populations. We report both conditional calculations and resolve neither; the acceleration-factor comparison does not depend on the choice.

**Two explanations, one unresolved.** Distribution shift is a live candidate explanation, and the source itself raises it. It is not the whole story on its face: the benchmark's test set was itself built by elemental substitution from the same database. The construction is not identical, however. The benchmark's set was built over several generations, each substituting into the relaxed outputs of the last, whereas our ion-exchange pool is single-generation. The benchmark's *evaluation* inputs are unrelaxed, as ours are, so the two do not differ in that respect; they may still differ in composition diversity and in the geometry distribution inherited from multi-generation construction. We have not measured either, so we cannot rule distribution shift in or out. The competing explanation is definitional. The two studies judge stability against different reference sets. @riebesell2025 judge against the Materials Project hull; @szymanski2025baselines judge against phase diagrams that "included all entries from MP (as of June 2025) as well as the entries generated from each AI model or baseline approach", which is a stricter test on two counts: the self-inclusion of the candidate pool, and the growth of the reference database between the two studies. A stricter reference lowers both prevalence and the passed-candidate stable share, so part of the gap may be definitional rather than a weakness of the models.

We note that @riebesell2025 do not rule out the stricter construction. They decline a combined reference set, concede that their choice "could consequently be interpreted as overestimating the performance" of the models while noting that the overestimate shrinks as the hull becomes better sampled, and leave the combined set to future work. Their stated reason for declining it is that it would make evaluation path-dependent, not that it is wrong. Public data can resolve this by recomputing the benchmark's acceleration factor against the joint reference set. Until then the gap is a measured fact with an open cause and a specified experiment to close it.


## S2. Overlap of the marginal cost distributions

The marginal distributions overlap heavily at every level, including level 1. Absolute cost is dominated by uncertainty all pipelines share. Only the paired comparison separates them, and only at level 1.

The overlap coefficient depends on the bin count, so we report the dependence rather than one figure. Over 20 to 240 bins the A--B overlap moves from 90% to 87% at level 1 and from 97% to 96% at level 2, spans of 3.4 and 1.3 percentage points, so the qualitative statement --- near-complete overlap at level 2, substantial overlap even at level 1 --- is not a binning artefact over this range, though the second decimal of any single figure is. At much finer resolution the empirical coefficient is dominated by sample sparsity rather than by any difference between the distributions, so we rest the comparison on the moderate-resolution range above and report the fine-bin behaviour only in the replication package.

A coefficient of 97% invites the question: high compared with what? The coefficient has a defined 0--1 scale, but two samples from one distribution do not score 1 on a finite histogram, so we report a reference for that finite-sample variability. Resampling a single pipeline's own draws against itself, where the true overlap is one by construction, gives a reference range for that variability: 96.1% to 97.6% at level 1 and 97.0% to 98.1% at level 2. The measured level-1 coefficient of 90% falls below its reference range; the measured level-2 coefficient of 97% falls inside its own. The construction and the replicate counts are documented with the code.

**We treat this as descriptive and go no further.** The reference is built from independent resamples, whereas the measured samples come from the same parameter draws; we neither model that dependence nor assert which way it pushes the coefficient. Nor is the reference a calibrated null, and no p-value is computed. So the claim is the observation only: the level-1 coefficient falls below its same-pipeline reference range, and the level-2 coefficient sits inside its own across the bin resolutions tested. These are descriptive diagnostics, not statements about distributional equality or separation. The section's conclusion rests on the paired comparison, which does not depend on any of this.

