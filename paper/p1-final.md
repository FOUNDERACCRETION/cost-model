---
title: "What Does It Cost to Validate a Predicted Inorganic Material?"
subtitle: "A transparent end-to-end pipeline model, and what its inputs cannot yet support"
author: "Karthikeya"
date: "Working paper --- 18 October 2026"
abstract: |
  Machine learning has sharply reduced the cost of parts of the computational materials pipeline, and the field widely asserts that synthesis is now the bottleneck. We did not find that claim priced in dollars. We build a transparent end-to-end model from candidate generation through machine-learned screening and density functional theory verification to laboratory synthesis, reporting cost per robust stable prediction and per experimentally validated target. A third level, per material new to science, we define but cannot price: the only novelty count we found for our reference campaign is zero. The attempt cost, \$190 to \$300 depending on the overhead convention, is assembled from three US university recharge schedules, federal and institutional rate notices and vendor list prices, with assumed throughput and allocation rules --- a construction, not a cost observed in any laboratory.

  Holding synthesis behaviour shared across pipelines, a machine-learned prefilter cuts modelled cost per robust prediction by 39%. Once the shared synthesis stage is included, the two decisions inside "pipeline choice" separate: the prefilter moves cost per validated material by 3.6% and sourcing candidates generatively by 16.9%, and both cross a 10% gap inside the verification-cost range we test. No source we found measures pipeline-specific synthesis behaviour, so these are tolerances, not findings.

  Three readings of essentially two campaigns give scenario medians from roughly \$1,100 to \$34,000, a factor of 30. The reading counting the most successes is not the cheapest: it reached a success rate 2.2 times higher using 6.2 recipes per target against another campaign's one, so recipe multiplicity moves cost more than the success rate does; a success rate without an experiment count cannot be costed at all. Published evidence cannot identify a general cost per validated inorganic material; the framework supplies which measurements would change the answer.

keywords: "materials discovery, machine-learned interatomic potentials, cost model, autonomous laboratories, research productivity"
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

Accretion Labs, Hyderabad, India. Contact: founder@accretionlabs.net. The author is an independent researcher and the founder of Accretion Labs; he holds no university appointment. This is a working paper and has not been peer reviewed.

**Keywords:** materials discovery, machine-learned interatomic potentials, cost model, autonomous laboratories, research productivity. **JEL:** O31, O32.

# 1. Introduction

The computational half of inorganic materials discovery has become very cheap very quickly. Graph neural network potentials relax a crystal structure in seconds on a laptop --- for two of the three potentials we benchmarked (Section 4.2); the third failed to converge on six of seven structures under our cold-start protocol [@deng2023chgnet; @chen2022m3gnet; @batatia2025macemp]. Generative models propose candidates at a few hundred structures per GPU-hour --- at the generation times reported by @szymanski2025baselines, roughly 390 per GPU-hour for one diffusion model on an A100. One recent project reported 2.2 million predicted structures, of which roughly 381,000 were placed on or below the convex hull [@merchant2023gnome]. Against that volume, the experimental half has barely moved: a laboratory still makes one material at a time, and the most prominent autonomous synthesis platform realised 36 of 57 target compounds over 17 days of continuous operation, across 353 synthesis experiments [@szymanski2023alab; @szymanski2026correction].

The field's standard account of this asymmetry is that synthesis has become the bottleneck. @montoya2024 state that synthesis "almost always represents the rate-limiting step in getting real-world feedback into AI and DFT-driven discovery processes"; @chung2025synthesizability that "the rate of materials discovery is limited by the experimental validation of promising candidate materials"; see also @aziz2021 and @tom2024chemrev. What we could not find anywhere is a price for it.

This matters for three reasons. A research group choosing between computational pipelines is implicitly making a budget decision without knowing the budget. A funder deciding between a larger compute allocation and a synthesis robot is comparing two numbers, one of which does not exist. And an investor reading that an AI system finds materials ten or a hundred times faster has no way to know what share of the cost that speed-up addresses.

The question sits inside a larger one. Research productivity has been falling across sectors: ideas per research dollar decline steadily in @bloom2020ideas, and in pharmaceuticals the decline persisted across six decades of dramatic improvement in the underlying tools --- Eroom's Law [@scannell2012eroom]. @jones2009burden attributes part of the pattern to the rising human-capital cost of reaching the research frontier, and AI is widely proposed as the reversal, an "invention in the method of invention" in the phrase @cockburn2018 take up from Griliches. Those are time series of output per unit of input estimated over decades; ours is a single cross-sectional level, and we do not claim it is a point in either series. What it offers is a decomposition: which stage a tool would have to improve for such a series to bend, which is the question those literatures leave open for any particular field.

This paper builds the missing number. We model discovery as a funnel from candidate generation through machine-learned screening and density functional theory verification to laboratory synthesis, with a cost and a pass rate at every stage, and price the whole of it in dollars. We compare three pipelines --- DFT applied to every candidate; a machine-learned interatomic potential (MLIP) used as a pre-filter before DFT; and a generative model supplying the candidate pool --- and report three outputs rather than one, because a cost per "discovered material" that does not say whether the material was ever made, or whether it was new, conceals the question being asked.

Our contributions are:

**Principal contributions.**

1. **A transparent end-to-end funnel accounting framework** from candidate generation to experimentally validated target, with every parameter documented, graded for evidence quality, and released with the code. The framework is the contribution; the numbers it currently produces are conditional on inputs we grade openly, five of which are modelling conventions with no source and one of which has no source at all.

2. **An illustrative synthesis-attempt cost build-up and scenario analysis.** We price an attempt at \$190 to \$300 depending on the overhead convention, from three US university recharge schedules, federal and institutional rate notices and vendor list prices, combined with assumed throughput, a compensation proxy and allocation rules, each graded and individually sourced. The published rates are measured inputs; the total is a construction on top of them. It determines the synthesis component of every downstream figure, and it is the one output a reader can lift and reuse independently of any disagreement about readings, pipelines or benchmarks.

3. **Evidence that disagreement about experimental validation dominates current cost estimates.** Cost per validated material spans roughly \$1,100 to \$34,000 across three published readings of essentially two campaigns. The readings differ in phase-identification standard, denominator and recipe multiplicity, so this compares non-equivalent scenarios rather than bounding one quantity — which is itself the finding, because it means no amount of computational improvement resolves it. The reading that counts the most successes is not the cheapest, because it attempted each target six times rather than once.

**Supplementary contributions.** A first-hand MLIP and plane-wave DFT timing benchmark, run because single-threaded core-seconds per ionic step per atom and the cold-start convergence rate do not appear to be published per model, and reported as a protocol demonstration on seven structures rather than a representative study. A verification-cost threshold analysis, which replaces reliance on any single assumed DFT cost by reporting where conclusions change. A break-even analysis for pipeline-specific synthesis behaviour, which converts the model's central untested assumption into stated tolerances. And an uncontrolled cross-setting observation about filter enrichment, reported in the supplement because its confounds are not separable.

# 2. Related work

Three literatures bear on this question; none answers it.

## 2.1 Resource accounting of computational discovery

@walker2026carbon is closest in structure: a DFT workflow for photovoltaic maximum efficiency, machine-learned surrogates progressively substituted, each configuration's CO$_2$ emissions estimated. The architecture is ours --- a staged pipeline with a substitutable component, costed end to end --- but the unit is carbon, not money, and the scope is compute: nothing is synthesised, and synthesis never enters the accounting. We agree that resource cost belongs beside accuracy; we differ on which resource binds, because ours includes the laboratory.

Matbench Discovery frames MLIPs explicitly as triage tools for allocating a DFT budget and reports a discovery acceleration factor per model [@riebesell2025] --- cost-adjacent framing without a cost, counting calculations saved rather than money and stopping at the DFT gate. Supplement S1 records a cross-setting discrepancy in its metrics. @miller2024flowmm reports cost per stable material in integration steps: per-method computational cost, not pipeline cost.

@szymanski2025baselines compare generative and substitution-based candidate generation on stability, novelty and generation time, establishing that a simple ion-exchange baseline outperforms several generative models. Their comparison runs over 500 *novel* materials per method --- "For each of these six approaches, 500 materials were considered", each run until 500 novel materials were obtained --- selection on novelty, not a fixed generation budget; Section 3.3 draws the implication for our chaining step. Their measurements are among our most important inputs, and Section 5.3 restates part of their conclusion in dollars --- a restatement, not an independent reproduction.

**Gap:** none prices the full funnel; none includes synthesis.

## 2.2 The economics of AI-aided discovery

@agrawal2024 model innovation as sequential search over a combinatorial design space in which a predictive model prioritises costly tests: better fidelity raises the probability of successful innovation and shortens search, but --- centrally for us --- those gains may go unrealised without matching investment in testing capacity.

@agrawal2026aiinscience decompose this by stage: in their equation (9), scientific productivity is a product of stage-specific terms, $\omega = \alpha\cdot\beta\cdot\gamma\cdot\delta$ --- question generation, idea generation, design generation and testing --- with returns to AI differing by stage. The decomposition is of productivity, not of pass probabilities --- an analogue of our result, not a statement of it --- and the model is analytical and uncalibrated: it says when prediction and testing are complements, not how far apart the two stages actually are in any real discovery problem. We supply that calibration for inorganic materials. Its limit is that the theory concerns prediction *fidelity* while our model varies compute *price*: better verification might raise experimental success, or lower it by rejecting makeable candidates, and would certainly cost more compute; we do not estimate that joint relationship.

Evidence on AI's effect on realised scientific output is thinner than the theory and concerns publication rather than validated laboratory output. The largest such study [@kusumegi2025] has had its identification contested: @renault2026comment argue that dating adoption by the first month an author's abstract is flagged is mechanically related to output, since the probability of a flag rises with the number of papers, and show that placebo flags reproduce the reported dynamics. We cite it as the state of that evidence rather than as a settled effect, and we know of no credible direct estimate inside a materials laboratory --- itself part of our motivation.

We take one convention from pharmaceutical cost estimation and nothing else: @dimasi2016 attribute abandoned candidates' cost to the survivors, as we do. Otherwise the figures are incomparable --- theirs capitalised over a decade-long development cycle with allocated company-level fixed cost, ours uncapitalised and charging no *explicit* equipment or capital. Because recharge fees and institutional overhead plausibly embed some depreciation and facility cost, the distinction is absent explicit capital versus implicit capital of unknown size, not some capital versus none; Section 6.3 treats that missing capital term as the largest unmodelled structure in the paper. @buchner2018tea matches cost-estimation method to technology readiness level, licensing our static, order-of-magnitude approach and our omission of a net present value; see also @kobos2020tea.

## 2.3 The synthesis evidence and its contestation

The empirical base for synthesis success is thin and disputed --- the central fact of the paper, not a caveat on it.

The A-Lab campaign reported realising target compounds from computational predictions over 17 days of autonomous operation, two further targets forming after products were manually reground and reheated [@szymanski2023alab]; on the corrected count, 36 of 57 targets. An Author Correction re-analysed the reported successes, found four inconclusive from X-ray diffraction alone, removed one compound that had been included in the training data, and clarified that the authors' "intention was to indicate that the materials were new to the prediction platform, not necessarily new to science" [@szymanski2026correction]. @leeman2024 re-analyse the campaign to a substantially more pessimistic count: of 43 reported products examined in detail --- the 36 classed as successes and seven partial successes --- they report significant issues with 42 of them. Three they regard as synthesised as predicted, of which one, CaFe$_2$(PO$_4$)$_2$O, they call convincingly demonstrated on the deposited diffraction data and the other two too poorly fitted to judge; all three had been reported previously, so they find none of the compounds new. Their headline rate is stated against the full target set: "the success rate would be 3/58, or 5%". The denominators do different work and should not be interchanged --- 43 is the set they inspected, 58 the targets attempted --- and we use 3/58 because it is the rate they publish. @prein2025 report a separate, smaller campaign.

Generative predictions have separately been questioned on novelty: a critique of one 380,000-structure stable set reports the structure of every one of ten randomly sampled entries matching an entry already in the ICSD, usually at higher symmetry, and counts 18,138 compounds of Pm, Ac or Pa and a further 23,529 containing Tc, Np or Pu in that set [@cheetham2024]; the source gives those counts rather than a percentage.

**Gap, and our position in it.** We do not adjudicate the dispute: we propagate all three readings through the cost model and report what each implies. The resulting factor of about 30 is the paper's most policy-relevant number --- the field does not currently know what a validated material costs to within an order of magnitude, and the disagreement is about what was synthesised, not about anything a cheaper or faster computational stage would settle. Resolving it needs agreed phase-identification standards, reconciled denominators, reported experiment counts, and ultimately new synthesis campaigns --- not better models.

# 3. Model

## 3.1 The funnel

Discovery is modelled as a funnel: candidates in, a material made in a laboratory out. Each stage has a cost per candidate entering it and a pass rate; every candidate entering is paid for, including those that fail. Cost per output is total spend divided by survivors at the level in question.

| Pipeline | Stages |
|:--|:-----------|
| A | ion-exchange pool, drop structures already in the reference database, DFT on every candidate, synthesis |
| B | ion-exchange pool, drop known, MLIP relax-and-classify, DFT on the survivors, synthesis |
| C | generative model, drop known, MLIP, DFT, synthesis |

The ion-exchange pool is the data-mined probabilistic ion-substitution model of @hautier2011substitution in pymatgen [@ong2013pymatgen], the substitution baseline of @szymanski2025baselines. The generative pool is a diffusion model for inorganic crystal structures [@zeni2025mattergen] in the MP-20 retrained configuration @szymanski2025baselines evaluate, not the larger released foundation model; our results about it hold for that configuration only. The architecture is not new: screen-then-synthesise dates to @greeley2006, high-throughput DFT screening to the database projects of the following decade [@curtarolo2012aflow; @jain2013mp; @kirklin2015oqmd], reviewed by @curtarolo2013htdft.

Every pipeline pays to generate its own candidates. Checking whether a structure is already in the reference database is not charged --- a simplification: at Materials Project scale matching needs reduced-cell comparison and symmetry analysis, is not free, and we have not measured it. Charged per raw candidate, it falls unequally (larger raw pools pay more) and, sitting upstream of the filter, would compress rather than widen the level-1 gap between A and B.

## 3.2 Three output levels

1. **Per cross-functionally robust DFT-stable prediction** --- a candidate DFT places on or below the convex hull, discounted by the share whose stability does not survive a higher level of theory. We avoid calling this "correct", since the label should not imply established truth; it is not the cost of a DFT-stable verdict, which would be cheaper by a factor of $1/(1-w)$.
2. **Per experimentally validated material** --- one material subsequently synthesised as the target phase.
3. **Per validated new material** --- one such material also new to science rather than new to the prediction platform.

The second and third differ materially: the A-Lab correction states the materials were new to the prediction platform, not necessarily new to science [@szymanski2026correction], so conflating them overstates what the money bought. Both differ from the first for a reason older than this evidence --- thermodynamic stability does not imply that a synthesis route exists [@jansen2002].

## 3.3 Stage costs

**MLIP cost per candidate.** Per-step cost is close to linear in cell size (log--log slope near one), step count independent of size and ranging from 18 to 81 steps. Relaxations that never converge run to the step cap, are charged in full and produce nothing. With $k$ core-seconds per step per atom, $n$ atoms, $\bar{s}$ mean steps, $q$ the non-convergence fraction and $s_{\mathrm{cap}}$ the cap:

$$\text{cost} \;=\; k \cdot n \cdot \frac{(1-q)\,\bar{s} + q\,s_{\mathrm{cap}}}{3600} \quad \text{core-hours}$$

Non-convergence matters: one of three benchmarked potentials failed to converge on six of seven structures started from raw generated geometries, a failure mode invisible in the production pipeline it came from, which always fed it pre-relaxed structures. Effective cost is per-step cost times step count divided by convergence rate, and the third factor is rarely reported.

**DFT cost per candidate.** A span rather than a point (Section 4.3).

**What the filter lets through.** With measured post-filter purity $P$, pool stability $\pi$ and recall $R$, the pass fraction is $\pi R / P$ and the DFT-stable share of what passes is $P$. The alternative formulation, from a benchmark confusion matrix, gives $\pi R + (1-\pi)\,\mathrm{FPR}$; Supplement S1 shows these disagree substantially, and we take measured purity as primary.

**Chaining.** To obtain $N$ candidates absent from the reference database, a method must generate $N$ divided by its novel share; each stage takes what the previous released. One caution: the @szymanski2025baselines stability rates come from samples of 500 *novel* materials per method, each method run until that many were obtained, so they are already conditioned on novelty, and dividing by the novel share again would charge the novelty filter twice. We believe the division applies to the generation count only; it is on the list of checks for the released package.

## 3.4 Wrong verdicts

A share $w$ of DFT "stable" verdicts do not survive scrutiny. Our proxy is the *cross-functional stable-to-unstable transition rate*: the directed fraction of candidates called stable at one level of theory that are called unstable at a higher one. "Wrong verdict" is shorthand; the quantity is a disagreement between two calculations, not experimental ground truth, and a material above the hull is not thereby impossible to synthesise [@kingsbury2022r2scan; @an2026; @merchant2023gnome].

**We take $w = 16$% at base, with 13.2% and 34.3% as the low and high values.** The first two are published: @merchant2023gnome report that 84% of discovered binaries and ternaries present negative phase-separation energies and 86.8% of tested quaternaries remain stable on the r2SCAN hull. Those are two different tests rather than one metric split by composition arity, so we carry them as a range rather than averaging. The high value is weaker and graded accordingly, being our own subtraction from a figure @an2026 do not present as a flip rate, over a population pre-screened on dynamical stability; Appendix A.4 gives the full provenance.

**A single $w$ is a convention, not a property of the quantity, because the flip rate is strongly chemistry-dependent.** A companion audit of the same r2SCAN recompute, by this author and in preparation, finds a global rate of 13.04% against the Materials Project hull --- consistent with the published quaternary figure --- but, holding element count fixed, disjoint composition cells running from 4.0% for intermetallics containing neither a lanthanide nor a 3d element to 30.7% for oxides containing a 3d element and no lanthanide, a spread of 26.7 percentage points. Carrying that range through the model moves level-1 cost for pipeline B from \$16.67 to \$23.09, a spread of 39%:

| Flip rate $w$ | Composition cell | Level 1, B | Level 2, B |
|--:|:--|--:|--:|
| 4.0% | intermetallic, no lanthanide or 3d element | \$16.67 | \$983 |
| 13.0% | the companion's global rate | \$18.40 | \$983 |
| 16.0% | our base value | \$19.05 | \$983 |
| 30.7% | oxide with a 3d element, no lanthanide | \$23.09 | \$983 |

Two things follow. **Cost per robust prediction is a chemistry-specific quantity**, and a reader screening one family should take the rate for that family rather than our base; a programme working in 3d oxides pays about 39% more per robust prediction than one working in simple intermetallics, for verification reasons alone. And **the level-2 column does not move at all**, which is the clearest demonstration of the cancellation argued below: $w$ enters level 1 and is absent from level 2 by construction, so a parameter that changes level-1 cost by 39% changes cost per validated material by nothing.

Three cautions on using that range. It comes from an analysis by the same author that is not yet public, so it is reported as work in preparation rather than cited; it widens the paper's reported uncertainty rather than narrowing it, which is the conservative direction for an unrefereed own result, but a reader should discount it accordingly. The cells are disjoint composition classes at a fixed element count, not a continuous sweep, so the endpoints are the extremes of 23 cells rather than bounds on any individual material. And the companion attributes the gradient to membership of the Materials Project's Hubbard-$U$ element list rather than to open-shell $d$ character; that attribution is contested within the companion's own analysis and nothing here depends on it, only on the spread.

Every candidate sent to synthesis incurs the allocated cost, including targets never made. Observed unconditional campaign success determines experimental-output costing, and synthesis success is **not** conditioned on the verdict being correct: a campaign's observed rate already embeds whatever computational failure it experienced, so dividing by $(1-w)$ too would charge those failures twice. Conditioning one reading and not the others, then dividing all three by $(1-w)$, mixes two definitions of success; removing it lowered cost per validated material by about 16% before the accounting change of Section 4.5. Cross-functional transitions are a separate computational endpoint, not an experimental failure probability: $w$ is retained for the level-1 output and reported separately as a diagnostic. We do not claim that a candidate whose stability flips under a higher level of theory cannot be synthesised --- roughly half of ICSD-reported compounds sit above the computed hull [@sun2016metastability] --- only that it fails the computational test level 1 defines.

The A-Lab campaign supports several success counts. We take 36 of 57, unconditional, as the corrected article prints it; Appendix A.4 gives the alternatives, the counts we discarded and the cautions attaching to the ratio.

## 3.5 Synthesis cost

Within our search scope (Section 6.3) we found no published dollar cost per solid-state synthesis attempt, and none for the capital or operating cost of an autonomous bulk solid-state synthesis laboratory --- search outcomes, not established absences. The attempt cost is built bottom-up:

$$\text{direct} = \text{XRD} + \text{furnace} + \text{labour} + \text{crucible/firings} + \text{precursor mass} \times \text{price} + \text{other consumables}$$
$$\text{per attempt} = \text{direct} + \text{tuition} + r \times (\text{direct} + \text{tuition})$$
$$\text{per target} = \text{recipes per target} \times \text{per attempt}$$

Labour pairs a graduate trainee's stipend and institutional allowance [@nih2026stipends] with a throughput of 10 to 20 compositions per week, so person and throughput match. Two caveats: the NRSA training allowance is a funding instrument, not an ordinary wage fringe rate, and the throughput range is an assumption, graded as such, not a published measurement. The unit is the attempt, not the target; crucible cost is divided by firings survived.

**Recipes per target is campaign-reported wherever a campaign reports it.** @prein2025 attempted each of 24 targets once, so the middle reading, which the base case follows, charges one recipe per target. A-Lab as corrected ran 353 experiments across 57 targets, a mean of 6.193 [@szymanski2023alab; @szymanski2026correction] --- the optimistic reading's charge and the parameter's high end; the 2023 article as printed gives 355 across 58, a mean of 6.121, which the pessimistic reading inherits as the version it re-analyses. Both experiment counts and both target counts changed at the correction, so mixing one document's numerator with the other's denominator is a splice; each reading stays inside one document. Lacking an experiment count, a reading falls back to a budget model: each recipe succeeds independently with probability $q$, a target receives at most $B$ recipes, per-target success is $1 - (1-q)^{B}$ and expected recipes that success divided by $q$. Calibration on A-Lab's two reported figures gives $q = 0.102$ and $B = 9.28$; applied to @leeman2024's success rate, 9.07 recipes per target. A reported mean is an average allocation, not a claim that every target underwent that many attempts --- failed targets consume more of the budget, successes fewer --- so Section 4.4 draws recipes jointly with the success rate under the fallback.

**Phase identification is charged at one tier, and it should not be.** The powder-diffraction service fee is charged at the same identification tier under all three readings. That is internally inconsistent, because what the three readings disagree about *is* the identification standard: a determination strict enough to satisfy @leeman2024 involves refinement and expert judgement, not a routine service slot, while the counts the optimistic reading rests on came from automated analysis. The model therefore pairs a strict reading's low success count with a lenient reading's identification bill. Appendix A.4 bounds the effect with the tiers the fee schedules do supply; that the uniform tier understates the spread between readings under the plausible assignment is not an assumption. Section 5.7 reports the uniform-tier figures and that bound beside them.

Instrument time is otherwise priced at published institutional recharge rates from the fee schedules of three US university facilities, each in the parameter file with its facility, URL, internal and external rate, unit, the quantity we charge and the schedule's effective date where the source gives one, which only Cornell's does. The three are not three independent measurements of an attempt cost but a price range for two line items, from which we take a central value. This may understate the true resource cost: @strom2020 report that user-fee income alone does not fully support most shared instrumentation facilities, so published rates can omit subsidised components. We apply that directionally to the XRD and furnace line items only, not as a bound on the attempt cost as a whole, which contains terms with no such subsidy argument. @sorzano2026 model the full cost of laboratory equipment and shared-versus-dedicated provision, the quantity a recharge rate approximates; the direction favours our conclusion, making those two items conservative while synthesis already dominates.

At base an attempt costs **\$271**: XRD \$80.00, indirect cost \$80.05, labour \$40.47, furnace \$37.90, tuition \$20.51, other consumables \$5.58, crucibles \$3.49 and precursors \$2.64; direct-cost-only, \$191. The parameter file carries the unrounded components and the time, mass and throughput allocation behind each rate. The indirect-cost rate $r$ applies to total direct costs including service-centre fees and tuition, the base its source defines it over; at $r = 0.42$ that base is \$190.59. An MTDC-like variant excluding fees and tuition is retained as a scenario in Section 4.5.

## 3.6 Fixed and marginal cost

Entering a new chemistry can require computing the convex hull's known phases once before any candidate can be judged [@aykol2019network]. That cost amortises over the batch's outputs, halving when the batch doubles --- but only within a single chemical system. For a pool spanning many systems it is closer to linear in the number of distinct systems, so it does not amortise, and it is pipeline-dependent to the extent that pools span different numbers of systems, which we have not measured. We set the reference-phase count to zero at base, reusing the published hull as the source experiments do, and flag both the missing count and the unmodelled pipeline dependence as open gaps.

## 3.7 Dollars

All compute is held in core-hours and GPU-hours until a final step where a single price parameter converts it, isolating the price assumption to one line.

# 4. Parameters

Every parameter carries low, base and high values, a unit, a source URL and an evidence grade. Figures are generated from the parameter file and the benchmark data, and the test suite fails if a printed figure drifts from the model.

## 4.1 Evidence grades

| Grade | Meaning |
|:--|:----------|
| `first_hand` | Measured by us |
| `published` | Stated in the cited source |
| `figure_read` | Read by eye from a published figure |
| `derived` | Arithmetic on published numbers |
| `proxy` | A published number for a related but not identical quantity |
| `assumption` | A modelling convention with no source |
| `missing` | No source found |

Of the 89 parameters, 46 are `published`, 15 `first_hand`, 13 `derived`, eight `proxy`, five `assumption`, one `figure_read` and one `missing` --- the reference-phase count of Section 3.6, held at zero. Grade is provenance, not precision, and the two should not be read off each other in either direction. `synth.success_unconditional` is `published` at every endpoint and still spans a factor of 12, because three published readings of the same evidence disagree that much; `synth.xrd_cost_per_sample` is `published` and spans 30-fold, because self-use, internal and external rates are three different institutional arrangements rather than three estimates of one price. Conversely `dft.cost_per_candidate`, the parameter with the widest range in the model at 336-fold, is graded `derived` and not `published`: its low end is our own measurement and its high end comes from a conference presentation, so the width is a statement about how far apart those two worlds are, not about the quality of either. Section 7 names the parameters whose grade or range to check first. A per-quantity rounding policy is stated in Appendix A.5; the precision printed is the precision computed, not the precision warranted.

## 4.2 First-hand measurements

We benchmarked three MLIPs [@deng2023chgnet; @chen2022m3gnet; @batatia2022mace; @batatia2025macemp] and plane-wave DFT [@giannozzi2009qe; @giannozzi2017qe] on seven structures of 10 to 56 atoms, with repeats and a thread-count sweep, using ASE optimisers [@larsen2017ase] and GBRV ultrasoft pseudopotentials [@garrity2014gbrv]. They are a **screening benchmark in their own right**, not a measurement of the MP-compatible verification workflow, and enter the model only as an illustrative low endpoint (Section 4.3).

Two findings bear on the model. Single-threaded execution is cost-minimising: core-hours are allocated cores times wall time, and twelve threads cost 32 to 90 times the core-hours of one here. And the quantity the model needs --- single-threaded CPU core-seconds per ionic step per atom, with cold-start convergence rates --- does not appear to be published per model; throughput and inference figures are published instead.

Our hardware is unusual, an ARM64 laptop under virtualisation, and DFT timings carry a platform artefact: twelve ranks cost 2.6 to 7.3 times the core-hours of four, so all DFT figures use four ranks, with twelve-rank values retained as documented upper bounds. A 28-atom cell against its own 56-atom supercell, identical in chemistry and pseudopotentials, gives 0.480 against 3.842 core-hours --- a factor of 8.0, an exponent of 3.0.

**The DFT protocol, because a core-hour figure cannot be assessed without it.** Quantum ESPRESSO 6.7MaX, PBE, GBRV ultrasoft pseudopotentials at their design cutoffs of 40 Ry for the wavefunction and 200 Ry for the charge density, identical for every element and structure. A Γ-centred Monkhorst--Pack mesh with $n_i = \max(1, \lceil |b_i| / 0.3\,\text{Å}^{-1} \rceil)$ on the starting cell. Marzari--Vanderbilt cold smearing at 0.01 Ry. Collinear spin polarisation with a ferromagnetic start for the manganese-containing structures and none for the rest; no Hubbard $U$. Self-consistency to $10^{-8}$ Ry with mixing 0.4. Cell relaxations use BFGS on ions and cell with a force threshold of 0.050 eV/Å, chosen to equal the MLIP force threshold so that ionic step counts are comparable between the two. Each figure is the median of three repeats at four MPI ranks. One deviation is worth stating: the plan was SSSP 1.3.0 PBE efficiency, and the Materials Cloud file server returned HTTP 503 throughout the logged attempts, so GBRV was substituted --- also ultrasoft and also built for high-throughput work, but the cutoffs are GBRV's uniform pair rather than SSSP's per-element values, and the cost would differ somewhat under SSSP. The full protocol, every input and output file, and the run log are in the replication package.

## 4.3 DFT cost: a span, not a point

DFT cost per candidate is modelled as a span from 3 to 1,000 core-hours:

- **Low, 2.98 core-hours:** our own *screening relaxation* in Quantum ESPRESSO with GBRV ultrasoft pseudopotentials, not the Materials Project-compatible workflow that produced the hull our stability labels are judged against: illustrative, not a measured cost of the task the model prices, and not a lower bound on it --- we have not measured an MP-compatible calculation on comparable hardware.
- **High, 1,000 core-hours:** a large public database project circa 2012 --- one to five calculations per material at roughly 200 CPU-hours each, a 10 to 20% failure-and-rerun rate, decade-old hardware. The figures come from a presentation by the project's lead on its production workflow [@jain2012nersc], not the database description paper [@jain2013mp], which contains no compute accounting, and they indicate 2012 practice rather than a published measurement.
- **Base, 54.5 core-hours:** the geometric midpoint, a convention; the Monte Carlo samples the span log-uniformly.

Since the low endpoint is illustrative, Section 5.4 treats DFT cost as a direct sensitivity --- the cost at which each decision reaches a given materiality threshold --- rather than resting on the midpoint.

## 4.4 The contested parameter

| Reading | Success | Recipes per target | Standing |
|:--|:--|:--|:-------------|
| Optimistic | 36 of 57 (63.2%) | 6.19, reported | As the corrected article prints it; the 2023 article printed 41 of 58; unconditional [@szymanski2023alab; @szymanski2026correction] |
| Middle | 7 of 24 (29.2%) | 1, reported | Preprint, 24 targets each attempted once [@prein2025] |
| Pessimistic | 3 of 58 (5.2%) | 6.12, reported | Peer-reviewed re-analysis of the first campaign; only one of the three regarded as convincing [@leeman2024] |

The first and third read the *same experiment* and disagree about what was made; the second is a separate, smaller campaign. All three are unconditional rates on their own denominators --- 57 is A-Lab's corrected target count, 24 is Prein's, and @leeman2024 count against 58, the count as originally printed --- and we do not force a common denominator, because part of the disagreement is what counts as a target.

**Each reading carries the recipe multiplicity its own campaign published.** A-Lab as corrected reports 353 experiments across 57 targets, a mean of 6.19; the 2023 article the pessimistic reading re-analyses prints 355 across 58, a mean of 6.12; @prein2025 attempted each of their 24 targets once. The budget model of Section 3.5 is a fallback for a reading that supplies a success rate without an experiment count, and none of the three now needs it: applying it to a campaign that published its own count would here invent about three extra attempts per target. Pairing one campaign's success rate with another's recipe count misprices the result in whichever direction the mismatch runs.

Success, novelty and the cross-functional disagreement rate come from these same re-analyses and are not independent: the Monte Carlo draws one reading per sample and takes all three from it, recipes per target included, since independent sampling would generate combinations corresponding to no coherent reading.

## 4.5 Accounting choices

Overhead is the largest single accounting choice in synthesis cost; at base DFT cost synthesis is 81 to 94% of the level-2 figure.

**The rate.** @azoulay2025icr report, across 354 NIH-funded institutions, *negotiated* indirect-cost rates averaging 58% and *effective* rates averaging 42%. The two are not interchangeable: the effective rate is recovered indirect costs over **total direct costs**, while the negotiated rate applies to **modified total direct costs**, a narrower base. @crs2026indirect quote the same study's 25% to 45% range for effective rates. Its data are NIH indirect-cost records rather than a census of US universities, and are averages across institutions rather than a rate any one laboratory faces.

We take **42% at base on total direct costs**, the base its source defines it over; applying it instead to a narrowed base excluding service-centre fees and tuition was a rate/base mismatch, and correcting it raises the indirect term per attempt from \$21.91 to \$80.05. The high value of 45% tops the effective range, and the 58% row is a negotiated-rate illustration: an average of a different quantity, not a ceiling on an effective rate. We call this indirect cost recovery, not F&A, following the source.

**The base.** The narrowed variant is called *MTDC-like* rather than MTDC because the regulation names services as part of the MTDC base, so excluding recharge fees is not MTDC [@cfr2001]; Appendix A.5 gives the definition and our reasons for testing the variant.

| Basis | \$ per attempt | Level 2: A / B / C |
|:---------|--:|:-----------|
| Direct costs and tuition, no indirect recovery | 191 | \$744 / \$708 / \$874 |
| Effective 42% on an MTDC-like base (fees and tuition excluded) | 213 | \$819 / \$783 / \$949 |
| **Effective 42% on total direct costs (default)** | **271** | **\$1,019 / \$983 / \$1,149** |
| Effective 45% on total direct costs (top of the effective range) | 276 | \$1,038 / \$1,002 / \$1,168 |
| Negotiated 58% on total direct costs (a different quantity) | 301 | \$1,123 / \$1,087 / \$1,253 |

This table prints unrounded figures, against the two-significant-figure policy used elsewhere, because at two significant figures the 42% and 45% rows would be indistinguishable and the table would stop doing its job. Between the extreme variants the level-2 figure moves by 51% for pipeline A, 54% for B and 43% for C; moving from direct costs only to the default is a 37%, 39% and 31% move in its own right, so most of the range is that one step. The second row is the pre-correction treatment, retained so the rate/base change is visible: moving 42% from the narrowed base to total direct costs raises the indirect term from \$21.91 to \$80.05 per attempt. Read in the other direction, the narrowed base put level-2 cost 20% below the default for pipelines A and B and 17% below for C.

**Whose cost, and what it leaves out.** The rows above vary a convention, not three different questions. Of the three perspectives standard in cost accounting, only two are reachable with what is published.

| Perspective | What it asks | Reported here? |
|:--|:---------|:-------|
| Principal investigator's budget | What comes out of the project's own funds, overhead going to the institution rather than the bench | Yes: the first row, \$191 per attempt and \$708 per validated material for pipeline B |
| Funder's outlay | What the award pays in total, bench costs plus the overhead the institution recovers | Yes, and it is the default: \$271 and \$983 |
| Institutional full cost | What the resources actually consume, including the part no fee or rate recovers | **No** |

The third is the one the title question arguably asks about, and we cannot price it. Two terms are missing and both push the same way. @strom2020 report that user-fee income does not fully support most shared instrumentation facilities, so the published recharge rates we use omit a subsidised component of the XRD and furnace line items --- a direction, not a magnitude, since no recovery fraction is reported that we could apply. And no explicit capital or depreciation is charged: Section 6.3 records that no capital figure exists for a platform of the kind producing our success rates, so the term is absent rather than estimated. Full cost is therefore higher than our default by an amount we decline to guess. We attempt no social-cost perspective (Appendix A.5), and not every unmodelled term points upward.

We default to the funder's outlay because every term in it is something someone actually pays and a reader can reconstruct it from published rates. It is not the full resource cost of a validated material, and nothing here should be read as that quantity.

# 5. Results

## 5.1 Base case

| Output | A | B | C |
|:-----------|--:|--:|--:|
| 1. per robust DFT-stable prediction | \$31.48 | \$19.05 | \$76.61 |
| 2. per experimentally validated material | \$1,000 | \$980 | \$1,100 |
| --- of which compute | \$90.65 | \$54.87 | \$221 |
| --- of which synthesis | \$928 | \$928 | \$928 |

The synthesis term is identical across pipelines. This is structural, not coincidental.

The base case is the middle reading throughout: @prein2025's 29.17% unconditional success rate and the one recipe per target their campaign reports, with the attempt cost of Section 3.5. **Success rate and recipe count have to be taken from the same campaign.** They are not independent inputs --- a campaign that retries failed targets records both a higher success rate and a higher recipe count --- so pairing one campaign's success rate with another's recipe multiplicity misprices the result in whichever direction the mismatch runs, and by a large factor: charging the middle reading A-Lab's 6.19 recipes instead of its own one would raise every level-2 figure in this table by a factor of 5.2 to 5.9, depending on the pipeline's synthesis share. Section 5.7 reports the other two readings, each with its own recipe count.

## 5.2 An MLIP pre-filter cuts DFT cost by 39%, not several-fold

Pipeline B costs \$19.05 per robust DFT-stable prediction against A's \$31.48, a ratio of 1.65, so B is 39% cheaper. The filter saves money because DFT then runs on a pool that is 15.2% stable rather than 9.2% [@szymanski2025baselines]. The relaxations themselves cost \$0.0009 per robust prediction, 0.004% of B's level-1 compute, and generating the pool a further \$0.0010: the filter earns its keep entirely by what it removes, not by what it costs to run.

The ratio is not independent of Supplement S1: because DFT spend per stable hit is DFT cost divided by purity, the level-1 cost ratio between two pipelines approaches their purity ratio whenever DFT dominates the compute term --- which it does overwhelmingly at base, the relaxations being 0.01% of B's level-1 compute. So 1.65 here and the ion-exchange acceleration factor of 1.65 in Supplement S1 are very nearly the same quantity reached from two directions; generation, filter and convergence costs account for the small difference. We report both because they answer different questions --- what a filter saves, and whether a benchmark predicts it --- but a reader should not count them as two findings.

**Benchmark classification rates would make the filter look 4.0 times better than the pool rather than 1.65, and the error is easy to repeat.** That route takes classification rates from a benchmark measured on one candidate distribution [@riebesell2025] and applies them to a differently constructed pool. Those rates predict that 37% of filter-passed candidates are DFT-stable; direct measurement on the actual pool gives 15.2%. Substituting the measured value more than halves the estimated benefit. Note that this 4.0 is the *filter* benefit under imported rates, a different quantity from the 4.02 level-1 ratio between the generative and filtered pipelines in Section 5.3; three unrelated quantities in this paper happen to round to four, and we name each where it appears rather than let them merge.

## 5.3 A generative pool costs 1.8 to 4.0 times as much, through purity at the DFT gate

Pipeline C costs \$76.61 per robust DFT-stable prediction against B's \$19.05. Both run the same filter-then-DFT funnel; what differs is what reaches DFT. After filtering, 15.2% of ion-exchange candidates are DFT-stable against 3.8% of generated ones [@szymanski2025baselines]. DFT spend per stable hit is DFT cost divided by purity, so the ratio is approximately 15.2/3.8. Generation cost plays no part: the generative model's GPU time is 0.5% of C's compute spend.

Two qualifications, the second of which limits the result more than the first.

This is not an independent reproduction of @szymanski2025baselines' conclusion, because the model takes their measurements as inputs; it restates them in dollars. Both purities are measured on 300 novel structures per method after filtering, against 500 per method for the unfiltered rates, so the filtered figures carry the sampling error of the smaller sample; the parameter file records a Wilson interval on $n = 300$.

**The magnitude rests on which end of a printed range we take, and the two ends do not support the same conclusion.** The source's main text gives 3.8% to 8.8% as a range spanning two generative models after filtering and does not say in that text which endpoint belongs to which; a supplementary scatter of filtered stability against potential error places the model we study at the low end, which is how we assign it, and that is a figure read by eye rather than a tabulated value. Running the full model at each endpoint rather than approximating by purity alone:

| Generative filter purity | Level 1, C | Level 1, C/B | Level 2, C | Gap to B | Material at 10%? |
|:--|--:|--:|--:|--:|:--|
| 3.8% (used) | \$76.61 | 4.02 | \$1,149 | 16.9% | yes |
| 8.8% | \$33.31 | 1.75 | \$1,024 | 4.2% | no |

The direction never reverses --- the generative pool is dearer at both ends --- but its materiality does. At the low end the generative-pool decision moves cost per validated material by more than 10%; at the high end it moves it by 4.2%, and the claim of Section 5.4 would not hold. So "a generative pool costs about four times as much" is a statement about the low end of a range the source prints without assignment, and a reader who assigns the endpoints differently gets 1.75 rather than 4.02 at level 1 and an immaterial difference at level 2. The unfiltered 3.0% we use for that pool is MatterGen's own rate, not a pooled figure. A range built instead from an uncertainty interval around a single value read off a figure would be narrower than the printed range and would understate this; the printed range is the one to report.

## 5.4 Once synthesis is included, the filter decision is immaterial and the generative-pool decision is not

Two decisions are bundled inside "pipeline choice" and they do not behave alike. Comparing each against pipeline B, the cheapest throughout the range swept below, separates them: $(A-B)/B$ is the value of the MLIP pre-filter, and $(C-B)/B$ the value of sourcing candidates generatively. Both are reported with synthesis success, recipes and attempt cost held shared across pipelines throughout. The two separate by a factor of about five at every verification cost, and at the base value they fall on opposite sides of a 10% gap: 3.6% for the filter decision against 16.9% for the generative one.

**One denominator, stated once.** Every relative cost difference in this section and the next is the gap of the dearer pipeline over the **cheaper** one, $\max/\min - 1$. The two directions are not the same number --- A exceeding B by 10% is B falling short of A by 9.09% --- so measuring against the dearer pipeline would make every difference look smaller and move every threshold here. The cheaper pipeline is the decision-relevant denominator, asking what premium the dearer option carries, and the convention is symmetric in its arguments, which is what makes it usable in Section 5.6 where which pipeline is cheaper varies from draw to draw.

| DFT core-h per candidate | $(C-B)/B$ | $(A-B)/B$ | B compute share |
|--:|--:|--:|--:|
| 3 | 1.1% | 0.2% | 0.3% |
| 10 | 3.3% | 0.7% | 1.1% |
| 30 | 9.6% | 2.1% | 3.2% |
| 54.5 | 16.9% | 3.6% | 5.6% |
| 100 | 29.5% | 6.4% | 9.8% |
| 200 | 53.6% | 11.6% | 17.8% |
| 300 | 73.7% | 16.0% | 24.5% |
| 500 | 105.5% | 22.9% | 35.2% |
| 1,000 | 156.1% | 33.9% | 52.0% |

Ten per cent is a convention, not a decision criterion, so we report three. Holding all other parameters at the baseline, the generative-pool decision reaches a 5% gap at about 15 core-hours per candidate, 10% at about 31, and 20% at about 65. The filter decision reaches the same three at about 77, 170 and 410. Every one of these crossings falls inside the 3-to-1,000-core-hour range we test, so none is an extrapolation of the fitted relationship. They are given to two significant figures under the policy of Appendix A.5, and the distribution reported next is more informative than any of them.

That both decisions cross a 10% gap inside the tested range is the main thing this section establishes, and it is a change of sign from what a more expensive synthesis baseline would give. Verification cost is not a second-order consideration under this calibration: a group paying more than about 31 core-hours per candidate to verify generated candidates is making a pipeline choice that moves its cost per validated material by more than 10%.

**The baseline crossing is one draw, and a low one.** Because the crossing depends on the synthesis expenditure and the compute coefficients, all of which are uncertain, it moves with them. Solving it separately inside each of 1,500 parameter draws puts the 10% generative crossing at a median of 159 core-hours, with a 5th-to-95th-percentile range of 20 to 713 --- more than an order of magnitude. The baseline value of about 31 sits between the 5th and 25th percentiles of that distribution, so quoting it alone understates where the crossing typically falls. At 5% the distribution runs 10 to 382 with a median of 78; at 20%, 43 to 1,877 with a median of 328. In 14 of 1,500 draws the 10% crossing has no solution in the domain at all, because the gap already exceeds 10% at zero verification cost. A reader deciding whether verification cost matters for their own pipeline should take the distribution, not the point.

**Where the crossing comes from, and why it moves with the synthesis bill.** Upstream compute expenditure per candidate is affine in DFT cost, so the crossing has a closed form in the shared synthesis expenditure $b = ra$ --- \$271 at base --- and in the compute coefficients. Appendix A.1 derives it, states the two conditions a usable crossing must satisfy, and reports that the $d$-independent terms contribute only 1.3% of it, which is why the crossings move nearly in proportion to attempt cost:

| Accounting basis | \$ per attempt | Generative, 10% | Filter, 10% |
|:--|--:|--:|--:|
| Direct costs only | 191 | 22 | 118 |
| Effective 42% on an MTDC-like base | 213 | 25 | 131 |
| Effective 42% on total direct costs (default) | 271 | 31 | 167 |
| Negotiated 58% on total direct costs | 301 | 35 | 186 |

Both crossings stay inside the tested range under every accounting treatment, so neither decision is immaterial as a general property of the model: the generative crossing moves only between 22 and 35 core-hours and the filter crossing between 118 and 186. Across the four treatments the attempt cost rises by 58% and both crossings by 58 to 59%. What the accounting choice changes is the size of the crossing, not whether there is one --- which is why we report thresholds rather than a single immateriality claim. The quantity that decides them is the one Section 4.3 says we cannot pin down; the second is an accounting choice.

The convergence at low DFT cost is structural. Level-2 cost is

$$C \;=\; \frac{c_0 \;+\; r\,a}{S}$$

with $c_0$ the upstream compute expenditure per candidate sent to synthesis, $r$ recipes per target, $a$ cost per attempt and $S$ the unconditional synthesis success rate. It does not depend on $w$ at all: the level-1 quantity $c$ is defined per cross-functionally robust prediction, so $c_0 = (1-w)\,c$ and the two factors cancel. At base, $c_0$ is \$26.44 for pipeline A, and $(26.44 + 1.0 \times 270.64)/0.291667 = \$1,019$. Neither $r$ nor $a$ nor $S$ is pipeline-dependent: every DFT-stable verdict proceeds to synthesis, and the disagreement rate, success rate, recipes per target and attempt cost are *assumed* identical however the candidate was found. That is imposed by the model's structure, not tested by it --- sweeping parameters confirms the arithmetic, not the assumption.

| DFT core-h | Level 1: A / B / C | Level 2: A / B / C | Spread | Synthesis share |
|--:|:------|:--------|--:|:--|
| 2.975 | \$2 / \$1 / \$5 | \$930 / \$930 / \$940 | 1.01x | 99%--100% |
| 54.5 | \$31 / \$19 / \$77 | \$1,000 / \$980 / \$1,100 | 1.17x | 81--94% |
| 1,000 | \$577 / \$349 / \$1,398 | \$2,600 / \$1,900 / \$5,000 | 2.56x | 19--48% |

The span is the dominant source of variation here: synthesis falls from essentially the whole of level-2 cost at the bottom of the DFT range to under half at the top, and the pipeline spread goes from 1% to 156%. A reader who treats either end as the base case will reach a different conclusion about whether pipeline choice matters, which is why Section 4.3 privileges neither and this section reports crossings instead.

**The 1.17 spread is conditional, not a bound.** It assumes synthesis success, recipes and attempt cost do not depend on how a candidate was found. There is a plausible direction for the first --- MLIPs are trained on databases dominated by materials that have actually been made, so a pre-filter may favour candidates that are *more* synthesisable, widening the spread --- but plausibility is not proof, and pipeline-specific differences in recipes or attempt cost could push either way. Section 5.5 asks how far the assumption has to fail before the ordering changes.

## 5.5 How far the shared-synthesis assumption has to fail, and for which question

A reader who doubts that synthesis is pipeline-independent needs to know how large a failure would change the answer. Relaxing the assumption gives the general ratio

$$\frac{C_i}{C_j} \;=\; \frac{Q_i}{Q_j}\,\cdot\,\frac{S_j}{S_i}\;,\qquad Q_i \;=\; c_{0i} + r_i a_i$$

and each quantity can be solved for a stated target, holding the others shared. **Two different questions give two different boundaries.** *Parity* is where two pipelines cost the same: with $r$ and $a$ shared, $S_C/S_B = Q_C/Q_B$. A difference slightly beyond it reverses the ranking, but two options that were nearly equal remain nearly equal, so reversal is not economic significance. *Materiality* is where the gap reaches 10%; on the $\max/\min$ convention of Section 5.4 that keeps C and B within 10% of each other while

$$\frac{Q_C/Q_B}{1.10} \;\le\; \frac{S_C}{S_B} \;\le\; 1.10\,\frac{Q_C}{Q_B}$$

Conflating them misstates the result in either direction: a parity boundary read as a materiality boundary overstates how little it takes for pipeline choice to matter, and the reverse overstates how robust the ordering is. Both are reported below.

| DFT core-h per candidate | $S_C/S_B$ for C--B parity | i.e. C better by | $S_C/S_B$ keeping C--B within 10% | Extra recipes in B for B--A parity | and for B 10% dearer than A |
|--:|--:|--:|--:|--:|--:|
| 3 | 1.011x | 1.1% | 0.919--1.112 | 0.21% | 10.27% |
| 10 | 1.033x | 3.3% | 0.939--1.137 | 0.71% | 10.89% |
| 30 | 1.096x | 9.6% | 0.996--1.205 | 2.12% | 12.66% |
| 54.5 | **1.169x** | **16.9%** | **1.062--1.285** | **3.85%** | **14.83%** |
| 100 | 1.295x | 29.5% | 1.177--1.424 | 7.07% | 18.86% |
| 200 | 1.536x | 53.6% | 1.396--1.689 | 14.14% | 27.72% |
| 500 | 2.055x | 105.5% | 1.869--2.261 | 35.35% | 54.31% |
| 1,000 | 2.561x | 156.1% | 2.328--2.817 | 70.71% | 98.62% |

**Units and comparators, because the two headline figures are not interchangeable.** The success columns compare the generative pipeline C against the filtered pipeline B. The recipe columns compare B against the unfiltered pipeline A. Different pairs, different quantities. And 16.9% is a *relative* increase in the success rate, not 16.9 percentage points: against the base reading's $S_B$ of 29.17%, parity puts $S_C$ at 34.08%, an increase of 4.92 percentage points.

The third shared synthesis quantity behaves the same way. Solving for cost per attempt instead, C reaches parity with B when its attempts cost 17.9% less than B's at base verification cost. We report the success and recipe tolerances in the table because those are the quantities campaigns measure; the attempt-cost tolerance is listed here for completeness and is the one a laboratory could most plausibly act on.

**All of these are break-even solves, not measurements.** No source we found reports a pipeline-specific synthesis difference in either direction, so every figure is the size a *hypothetical* difference would have to reach. That is the point of reporting them: they convert an untested assumption into stated tolerances.

**Each boundary varies one synthesis quantity while holding the others fixed**, so these are not joint robustness bounds. Appendix A.2 evaluates the joint condition over a grid of the two ratios and shows the region where the 10% gap is exceeded is not the union of the one-at-a-time boundaries: differences in the same direction compound, in opposite directions they cancel, and the immaterial region is a narrow diagonal band that does not contain equal synthesis behaviour.

Read that way, the table says two things. **Reversing the ranking takes a difference the synthesis literature could in principle resolve**: at base calibration a 16.9% relative success advantage for generative candidates, or 3.85% more recipes in the filtered pipeline, flips which pipeline is cheaper. **And the 10% materiality band no longer contains equal synthesis performance** for the generative comparison: it runs from 6.2% above to 28.5% above equal success, so identical synthesis behaviour already leaves C more than 10% dearer than B. The filter comparison still behaves the other way --- 14.83% of the baseline recipe count, about 0.148 extra recipes per target, is needed before A and B differ materially --- which is the same asymmetry the sweep shows.

**What this does not establish.** No source we found reports a pipeline-specific synthesis difference in either direction, so the plausible range for one is not established and nothing here supports a claim about which boundary is likely to be crossed: an absent measurement is evidence neither of a small effect nor of a large one. These are therefore **conditional tolerances, not demonstrated robustness**. A 16.9% relative success advantage for generative candidates, or 3.85% more recipes in a filtered pipeline, are shown here to be neither plausible nor implausible --- only unmeasured. So the defensible statement is narrower in both directions than "pipeline choice does not matter economically" and than its negation: the filter decision needs a synthesis difference above its materiality boundary before it matters, while the generative decision is already material at equal synthesis performance and would need a success advantage of 6.2% or more to stop being so. Which is cheaper, and by how much, rests on the shared-synthesis assumption and on a baseline calibration the paper itself declines to privilege.

The two columns behave differently in verification cost, and informatively so. The materiality column rises only from 10.27% at 3 core-hours to 14.83% at base, because a 10% gap at level 2 is paid out of the synthesis bill rather than the compute difference; the parity column is driven entirely by that compute difference and rises from 1.1% to 16.9% over the same interval. They answer different questions and should not be quoted as one tolerance. The flatness is weaker than under a larger synthesis bill: with one recipe per target the synthesis denominator is smaller, so verification cost reaches further into both columns.

**An algebraic boundary is not automatically a feasible probability.** A success *ratio* is attainable only while the success *rate* it implies stays within $[0, 1]$, so every interval above must be intersected with that range. At the base reading's $S_B$ of 29.17% the ceiling on the ratio is $1/S_B = 3.429$ and every row of the table above clears it, the largest implied rate being 74.7%. The ceiling is reading-dependent, and counter-intuitively tighter where success is higher: under the optimistic reading's 63.2% it falls to 1.583, because a pipeline already succeeding two times in three has less room to improve. Appendix A.3 reports the parity boundary under six parameter variants, one of which demands a success rate above one.

## 5.6 Under uncertainty: reliably ordered, material in about one draw in ten

Across 20,000 draws respecting the documented correlations, pipelines compared pairwise within each draw. Two quantities, defined because they are easy to confuse: **P(B < A)** is the share of draws in which B's cost is below A's *in the same draw*, and **P(differ > 10%)** the share in which the dearer of the pair exceeds the cheaper by more than 10%, $\max(C_A, C_B)/\min(C_A, C_B) - 1 > 0.10$, on the denominator convention of Section 5.4. Both are paired: each draw is one parameter world seen under two pipelines.

| Level | P(B < A) | P(differ > 10%) | Overlap of marginals |
|:--|--:|--:|--:|
| 1 | 99.4% | 98% | 90% |
| 2 | 99.4% | 10% | 97% |
| 3 | 99.4% | 10% | 99% |

P(B < A) is near one at every level because the two purities are drawn as a bloc from a single source and B's post-filter purity exceeds A's pool prevalence across almost all of that source's range, which is why the figure is identical down the column. The informative number is the second: the dearer of A and B exceeds the cheaper by more than 10% in 10.0% of level-2 draws, and the generative comparison is material in 34.2%. So at level 1 the pipelines separate sharply, while at level 2 the ordering survives draw by draw and the magnitude matters in about one draw in ten for the filter decision and one in three for the generative one. A paper reporting that B beats A in 99.4% of simulations would be stating something true and, nine times in ten, economically immaterial. Both shares are sensitive to the DFT-cost prior, which we chose rather than measured: it is log-uniform over a span whose base Section 4.3 calls a convention, and a reader who believes modern production DFT costs hundreds of core-hours per candidate should read the 1,000-core-hour row of Section 5.4 instead of this table.

**The crossings of Section 5.4 and these material shares are the same comparator, but neither is the other's prior mass.** A crossing is where the gap reaches 10% with every other parameter at base; in simulation the crossing itself moves, because the compute term is measured against the synthesis expenditure $b = ra$ and both recipes and attempt cost are drawn. Synthesis success is not among the quantities that move it: $S$ is shared, so it cancels from the paired ratio and appears nowhere in $d^{*}$. The filter crossing is 167 core-hours with 30.8% of draws above it but only 10.0% material; the generative crossing is 31 core-hours with 59.7% above it against 34.2% material. The prior mass above the baseline crossing overstates the material share by a factor of 1.8 for the generative comparison and 3.1 for the filter one, because draws with a larger synthesis bill push the crossing past their own verification cost --- and the effect runs both ways: material filter draws occur from 60 core-hours, well below the baseline crossing, and immaterial ones as high as 999.

The level-3 row compares pipelines and is not a cost level. It uses a nonzero novelty share, and that share is not a measurement: we found no source publishing a nonzero novelty count for this campaign, @leeman2024 stating that "none of the materials produced by A-lab were new" while the correction declines the claim rather than quantifying it. Every nonzero value we use is therefore a statistical upper bound on a zero count --- the Wilson 95% and 99% bounds on 0 of 36, 9.6% and 15.6% --- which are the most generous rates the data admit and so make cost per new material optimistic. No level-3 cost level appears anywhere in this paper, because at the published count it is unbounded (Limitation 5).

The marginal cost distributions overlap heavily at every level, including level 1: absolute cost is dominated by uncertainty all three pipelines share, and only the paired comparison separates them. The overlap coefficients and their bin-count and resampling diagnostics are in Supplement S2.

## 5.7 The answer depends on which reading is right, and the recipe count matters more than the success rate

The figures below are Monte Carlo medians within each reading, with every other parameter drawn from its distribution. They are not the deterministic point estimates of Section 5.1, which hold all parameters at base; the two differ because the base values are not the medians of their own distributions and several inputs vary within each reading. The base case of Section 5.1 corresponds to the middle reading.

| Reading | Success | Recipes per target | Level 2, pipeline B, scenario median | 5th--95th percentile of draws |
|:--|--:|--:|--:|:--|
| Optimistic (A-Lab) | 63.2% | 6.19, reported | \$3,012 | \$2,130--\$4,076 |
| Middle (Prein) | 29.2% | 1, reported | \$1,147 | \$650--\$2,379 |
| Pessimistic (Leeman) | 5.2% | 6.12, reported | \$34,213 | \$15,275--\$101,952 |

Across the three readings that is a factor of 30 for pipeline B --- across all three, not between the extremes of the success rate, for the reason the next paragraph but one gives.

**Each reading carries the recipe count its own campaign published**, and the first and third read the same campaign, so they share its experiment count: @leeman2024 re-count the outcomes of the 2023 article's 355 experiments across 58 targets, 6.12 per target, while the corrected article's 353 across 57 gives 6.19, the two differing only because the correction removed one target and two experiments. A derived count has no place in either: the budget model of Section 3.5 exists for a reading that supplies a success rate without an experiment count, and applying it to a campaign that published its own would here have invented 2.95 extra attempts per target and raised the pessimistic figure by 48% at base parameters.

**The reading labelled optimistic is not the cheapest**, and that does not follow from the success rates. A-Lab's reading has the highest of the three --- 63.2% against the middle reading's 29.2%, a factor of 2.17 --- yet implies 2.6 times the cost per validated material, because it reached that rate with 6.19 recipes per target against one. On the synthesis term, which dominates at this verification cost, the campaign bought a 2.17-fold improvement in success for a 6.19-fold increase in attempts, so synthesis cost per validated material rose by a factor of 2.86 net of the success gain. The cost ordering is therefore middle, optimistic, pessimistic: the labels rank how optimistic each reading is about what was *made*, not about what it cost.

**That decomposition compares campaigns and is not a measured return to retrying.** @prein2025 and @szymanski2023alab attempted different targets in different chemistries, and a campaign choosing to attempt each target once is also choosing which targets to attempt. We cannot separate the return to additional recipes from the difficulty of the target set, and nothing here says a laboratory would do better by abandoning failed targets after one attempt. What it does establish is that recipe multiplicity is a first-order cost parameter, entering level-2 cost with an elasticity equal to the synthesis share, 0.81 to 0.94 against the success rate's exact one (Section 5.8), and that a cost estimate taking a success rate from one campaign and an attempt count from another can be wrong by a factor of several either way. A paper reporting success rates without experiment counts cannot be costed at all.

**Within a reading, pipeline choice matters most where synthesis is cheapest.** The between-pipeline ratio is $(c_{0i} + r a)/(c_{0j} + r a)$, which cancels the success rate but keeps the recipe count and attempt cost. Since the compute term is a fixed number of dollars and the synthesis bill is not, pipeline choice moves the median by 1.21 times under the middle reading, 1.07 under the pessimistic one and 1.06 under the optimistic one --- the reverse of the intuition that expensive synthesis makes compute decisions matter.

**The factor is not measurement uncertainty, and it is probably understated.** Two readings interpret the same experiment and disagree about what was made; harmonising identification standards and reconciling denominators would narrow the comparison with existing data, and closing it would need new campaigns with phase identification both sides accept. Meanwhile every reading is charged the same \$80.00 diffraction fee although the readings differ precisely in identification strictness. Charging each the tier its own standard implies widens the spread from 33 to 71 if strictness and cost rise together, or narrows it to 15 under the reverse and less plausible assignment. Those three are computed on the deterministic scenarios, where the uniform-tier spread is 33; the factor of 30 quoted above is the same comparison at the Monte Carlo medians. The two differ because the base values are not the medians of their own distributions, and the tier comparison is like-for-like within its own basis. We report the uniform-tier figures as the model's output and that range as its known bias.

Where a single number is unavoidable we quote the middle reading with the spread beside it, and note that it is the least established of the three: it is a preprint reporting the smallest campaign. It is also, now, the cheapest, so quoting it alone is not a conservative choice.

## 5.8 Where the cost sits, and what that implies for improvement

We report elasticities: the percentage fall in cost per 1% proportional improvement in a lever, scale-free so levers in different units compare directly. Note that these are proportional, not absolute: one percentage point of synthesis success is a 1.6% proportional gain under the optimistic reading and a 19.3% proportional gain under the pessimistic one, so percentage-point framings are not comparable across readings and we avoid them.

| Lever | A | B | C |
|:-----|--:|--:|--:|
| Synthesis success rate | 1.000 | 1.000 | 1.000 |
| Recipes per target | 0.911 | 0.944 | 0.808 |
| Cost per synthesis attempt | 0.911 | 0.944 | 0.808 |
| Compute price (best compute lever) | 0.089 | 0.056 | 0.192 |

**The synthesis levers should not be ranked against each other.** Success has elasticity exactly one, because it divides both terms. Recipes and attempt cost have elasticity equal to the *synthesis share* of total cost, and the gap between them and unity *is* the compute share rather than a difference in leverage.

The finding is the magnitude gap, and it is single-digit-to-low-double-digit rather than the two orders of magnitude a larger synthesis bill would produce. At the deterministic base, a 1% proportional improvement in a synthesis term moves level-2 cost 4 times as much as the same improvement in compute price for pipeline C, 10 times for A and 17 times for B; at the Monte Carlo medians the ratios are 16, 37 and 61, because the DFT-cost prior puts most of its mass below the base value. The two are different estimands --- a ratio at one parameter vector against a ratio of median elasticities across 20,000 draws --- and both are ratios of cost shares, not returns: they say where the money is, not what it costs to move it. At the top of the DFT span the ratio falls below one for every pipeline, compute then being 52 to 81% of the total and 81% for the generative one, so synthesis dominance is a property of the lower part of the verification-cost range rather than of the model. That is the single most important qualification on the paper's headline claim, and Section 4.3 is why we cannot resolve it.

**Verification accuracy is not a lever on level-2 cost, and a model that makes it one has double-charged.** With an unconditional success rate, $w$ cancels: compute per candidate sent to synthesis is $c_0 = (1-w)\,c$, so the factor discounting the level-1 quantity and the one that would scale it back are the same. Holding $c_0$, recipes, attempt cost and observed success fixed, changing the diagnostic $w$ does not change the cost of a validated material. The cancellation is easy to lose: pairing a campaign-observed success rate with a label-accuracy factor restores an apparent elasticity of $w/(1-w)$, the signature of charging the same failures twice (Section 3.4). Check any extension against the limiting case: at $w = 1$ no verdict survives the cross-functional check, so level-1 cost is unbounded while level-2 cost must stay finite, because the campaign still made materials. Whether better verification would raise experimental success, and at what compute cost, is a joint relationship this model does not estimate.

**One lever requires no research expenditure.** Switching from on-demand to spot compute pricing carries a discount of about 62% in the compute-optimised instance prices recorded in the parameter file. It requires no research expenditure, which is the sense in which we call it free; it is not operationally free, since spot capacity is interruptible and retries, checkpointing and delay carry costs we do not model, and the discount is provider- and instance-specific. Because it scales the whole compute term, its effect on level-2 cost is 62% of the compute share: 3.5% for pipeline B and 11.8% for C. The levers worth several times more all require synthesis research whose cost we found no measurement of, so we observe only that the free lever is now worth single-digit percentages rather than fractions of one --- a consequence of the base case's small synthesis bill, not of anything about compute pricing.

## 5.9 Break-evens

**The filter has no meaningful break-even batch size.** Loading the potential costs 0.00024 core-hours against a saving of 29.5 core-hours per candidate, so the informative quantity is the per-candidate saving rather than a threshold: any additional fixed cost of $X$ core-hours, such as fine-tuning, repays after $X/29.5$ candidates.

**Synthesis cost at which compute begins to matter --- which, for one pipeline, is already.** Taking "matters" as compute reaching 10% of level-2 cost, the attempt cost at which each pipeline crosses that line is \$144 for B, \$238 for A and \$579 for C. Only C's lies above today's \$271, so C is the one pipeline for which compute already matters: it is 19.2% of level-2 cost there, against 8.9% for the unfiltered pipeline and 5.6% for the filtered one. For C the threshold is therefore the attempt cost at which compute would fall *back* to 10%, not rise to it. The threshold depends only on the compute term, so it is unchanged by the accounting choices of Section 4.5, which move the attempt cost itself. At the top of the DFT span compute matters for all three.

**Generative-pool parity.** C matches B at level 1 when filter purity on the generative pool reaches 15.5%, 4.1 times the measured value.

**How strong would a synthesisability effect have to be?** For pipeline choice to double level-2 cost, an MLIP pre-filter would have to raise synthesis success from 29% to 56% --- which sits below the optimistic reading's own 63.2%, so the required effect is within the range campaigns have reported, though we found no study measuring it by pipeline. It specifies how large an effect the follow-up study would need to detect.

## 5.10 Where the evidence is weakest

A one-at-a-time sweep is led by a single parameter at each level: DFT cost at level 1 and synthesis success at level 2, which account for 99.8% and 50.9% of the summed squared one-at-a-time ranges respectively. The level-1 figure is near-total; the level-2 figure is a bare majority, with the remainder spread across recipes per target, attempt cost and DFT cost, so "dominated" fits the first and not the second. That statistic is not a variance decomposition and should not be read as one; it reflects the width of each parameter's assumed range as much as the model's response to it. **The tornado maps where the evidence is weakest rather than where the leverage is.** The two quantities most in need of better measurement are DFT cost on modern hardware and synthesis success from independent campaigns.

# 6. Discussion

## 6.1 For research groups

At base DFT cost, pipeline choice is a line item worth 6 to 19% of the total; at the top of our DFT span, 52 to 81%, and the argument below reverses accordingly. A group intending to take candidates into the laboratory should optimise the laboratory first: at base the synthesis share is the larger one and the more elastic. But the two pipeline decisions differ --- at base calibration the filter decision moves level-2 cost by 3.6% and the generative-pool decision 16.9%, so only the second is material against the synthesis bill, though above about 31 core-hours per candidate it is material to the total and above about 170 the filter decision too. Stopping at computational screening makes the choice larger: a factor of 1.8 to 4.0 between pipelines.

Two practices. Report an MLIP's convergence rate with its accuracy: one that will not converge from a cold start costs more than its per-step speed implies. And check thread scaling before budgeting --- on our virtualised platform, not to be generalised from, single-threaded across many structures rather than multi-threaded on one was the difference between one core-hour and eighty, since core-hours are billed on allocated cores, wasted or not.

## 6.2 For funders

At base DFT cost synthesis holds the money --- 81 to 94% of the cost of a validated material, a synthesis lever worth 4 to 17 times the best compute lever --- but the margin is a single-digit-to-low-double-digit factor, not the one to two orders of magnitude a larger synthesis bill would give, and it inverts at the top of our verification-cost span, where compute is 52 to 81% of the total. The ordering is not robust to verification cost itself, and we do not claim to know what a dollar spent on synthesis research buys.

The factor of 30 between readings of the synthesis evidence exceeds every methodological difference in the paper combined; the field does not know the number to within an order of magnitude. Independent campaigns with phase identification both sides accept, reporting recipes attempted per target, would help more than better discovery methods. But resolving the identification dispute will not by itself narrow the range, because the cost ordering does not follow the success ordering (Section 5.7). The general problem is the one in @bloom2020ideas and @scannell2012eroom: without a cost per research output there is no productivity denominator, and the missing measurement is experimental, not computational.

## 6.3 For autonomous laboratory programmes

Within our search scope we found no published capital or operating cost for an autonomous *bulk solid-state* synthesis platform. @pilon2026, on a different chemistry, report that high-end self-driving laboratories "often exceed US\$100,000" excluding analytical components, that their predecessor flow-chemistry platform cost approximately US\$50,000 in essential components, and that a human-in-the-loop sampling unit brings their own platform to approximately US\$5,000; such disclosure is the exception, and the only solid-state capital figure we found is a press statement we do not treat as citable. @lo2024frugal review low-cost self-driving laboratories and the "frugal twin" approach, tabulating costs for twenty-five platforms, so the gap is solid-state platforms of the kind that produce our success rates, not platform costing in general --- and a capital figure is what would decompose synthesis into labour, consumables and amortised equipment, the largest unmodelled structure here.

Cost per validated material, not samples per day, is the metric. Peak throughput and realised output differ --- one platform's software paper reports around 3,500 samples over 1.5 years [@fei2024alabos] against a quoted daily capacity --- and converting between them needs utilisation, realised samples over daily capacity times eligible operating days: not hardware duty cycle, though the two are often conflated, and not reported for the platforms we examined. @adesiji2026benchmarking propose benchmarking practice here; cost per validated output belongs in it and is absent.

## 6.4 For benchmark design

Our Supplement S1 result addresses a different literature: measured enrichment on two realistically constructed candidate pools is roughly half the acceleration factor the benchmark reports, lower still on the generative pool. We do not attribute this to the benchmark --- the evaluations differ in reference hull, candidate distribution and threshold, the difference may be definitional, and the benchmark's authors themselves note that their reference-set choice could be read as overestimating performance [@riebesell2025] --- and we specify the experiment that would settle it. Until it is, practitioners budgeting DFT from benchmark classification rates should measure enrichment on their own pool. We do not predict a general factor-of-two overestimate; our own estimate halved when we substituted direct measurements.

## 6.5 For investors and the public account of AI in science

Claims that AI accelerates materials discovery by one or two orders of magnitude are, on our accounting, claims about a stage worth 6 to 19% of the cost of a validated material at base verification cost. They may well be true as stated, but they do not imply a comparable reduction in the cost of discovery, and the gap between the two statements is where most of the money is. The qualification is conditional: at the top of our verification-cost span that stage is 52 to 81% of the total, so a claim about it is a claim about most of the cost --- and which regime a programme is in depends on a quantity nobody has published for a modern workflow.

On the funnel alone: more candidate materials is not more validated materials, and where the terminal stage is unchanged it is not obvious that it is even more discovery.

# 7. Limitations

1. **Primary threat to validity: synthesis success is assumed independent of pipeline.** No source we found measures it. Per Section 5.5 the ordering flips at a 16.9% relative difference in success, which the synthesis literature could in principle resolve; the filter decision needs a substantially larger difference before a 10% gap appears, while the generative decision is already material at equal synthesis performance. Because the differences are unmeasured, neither boundary establishes robustness and which pipeline is cheaper is not established. The follow-up study is to attempt matched sets of filtered and unfiltered DFT-stable candidates and compare success rates.
2. **Filter recall is not measured on these pools** but imported from the benchmark: an assumption, not a measurement, on a different population from our measured purity.
3. **The generative-pool result turns on which end of a printed range we take.** The source gives 3.8% to 8.8% for two models after filtering without assigning endpoints; we take 3.8% off a supplementary figure, read by eye. The level-1 ratio then runs 4.02 to 1.75 and the level-2 gap 16.9% to 4.2%: Section 5.4's conclusion holds only at the low end, and both purities rest on 300 structures.
4. **Overhead treatment is an accounting choice** moving level 2 by 43% to 54% depending on the pipeline between the extreme variants of Section 4.5, and Section 5.4's materiality thresholds nearly in proportion to the attempt cost, a near-proportionality Section 5.4 shows is no identity. The rate averages NIH-funded institutions, not one any laboratory faces.
5. **No level-3 cost is reported.** The novelty share is disputed and the count we would use is zero, at which the implied cost is unbounded; level 3 enters Section 5.6's comparison on a nonzero share with no dollar figure attached.
6. **DFT cost spans more than two orders of magnitude.** Results are reported across the span.
7. **The cross-functional transition rate is a proxy affecting only level 1.** $w$ is a directed functional-disagreement fraction, not an experimental error rate, and disagreement also runs the other way, which we do not credit. Level-2 and level-3 costs use unconditional success rates, so $w$ only defines the level-1 output.
8. **Our DFT measurements are not commensurate with the hull the model uses** (Section 4.3). Our timings are Quantum ESPRESSO with ultrasoft pseudopotentials, the hull defining level 1 is the Materials Project's, so our energies cannot be placed on it and the span's low end is illustrative, not measured. Hence thresholds (Section 5.4), not a base case; this is the paper's most consequential unresolved issue, and closing it needs an MP-compatible calculation on comparable hardware.
9. **One parameter is graded `missing` and five are `assumption`.** The `missing` one is Section 3.6's reference-phase count, held at zero. The assumptions: share sent to DFT, SCF atom count, the pipeline-specific success multiplier (set to one --- Limitation 1's assumption), working weeks per year, firings per crucible. Three more are `proxy`: filter recall (benchmarked on another population, Limitation 2), the tuition term (an NRSA cap, not an observed charge), precursor mass (bench-scale, no autonomous-laboratory figure).
10. **Monte Carlo choices shape the distribution.** The DFT-cost prior is chosen, not measured, and Section 5.6's material shares are sensitive to it; the three readings' equal weighting has no basis. The level-2 95th percentile turns on whose re-analysis you believe: \$64,932 under equal weights, \$3,836 if the pessimistic reading gets zero weight.
11. **The enrichment gap has an unresolved competing explanation:** the two studies judge stability against different reference sets.
12. **Our hardware is unusual.** An ARM64 laptop under virtualisation produced two platform artefacts we correct for; the DFT timings should not be generalised to server hardware.
13. **"Validated" differs across the three readings.** Level 2 is defined once, but they differ on the evidentiary standard: @leeman2024 regard only one of three claimed successes as convincingly demonstrated. Part of the factor of 30 is therefore strictness of counting, not cost, and we do not decompose it.
14. **Published recharge rates may omit subsidised components** [@strom2020] --- directional for the XRD and furnace line items only, not a certification that the attempt cost is conservative.
15. **The base case combines two settings.** Success and recipe multiplicity come from one campaign: @prein2025's 7 of 24 targets, each attempted once. It is paired with a manual-academic attempt cost from fee schedules, whereas the automated campaigns behind our success rates are robotic platforms costed in capital, not bench time. So the attempt cost is campaign-specific in none of the three readings, no fee-schedule equivalent for an autonomous platform exists (Section 6.3), the error's direction is unknown, and capital is absent from our accounting entirely.
16. **Cost per attempt may not be pipeline-independent after all.** Item 1's objection reaches the attempt cost too. @cheetham2024 count 41,667 radioactive-element compounds in a generative stable set of 384,870, not the one we model; they report counts, and the implied fraction is ours. Whether our pool shares that skew is untested; if so the cost channel is handling and disposal, unmodelled here, not precursor mass --- only \$2.64 of a \$271 attempt.

# 8. The replication package

The model, parameters, first-hand benchmark data, analysis code and test suite are *to be* released as a replication package. At the time of writing the repository is not yet public and no archival DOI has been minted, so nothing in this section should be read as a claim that the results have been independently regenerated. Every figure in this paper is generated from the parameter file and the benchmark data, and the build fails if a figure in the text drifts from the model. That is a check on internal consistency, not on the correctness of the model's assumptions or of our reading of the sources.

The model is a pure function from parameters to results, so a reader who disagrees can substitute and rerun --- the overhead treatment, the weighting of the three readings, the DFT cost span, the choice of optimistic success count --- and each takes one edit.

Alongside the code the package carries the manifest of all 89 parameters with ranges, units, evidence grades and sources; the fifteen attempt-cost inputs, each with the usage allocation that converts a published rate into dollars per attempt; the unrounded threshold coefficients with their residuals; the seeded sampler; a worksheet walking the attempt cost, the level-2 equation, the threshold crossings and the decision boundaries of Section 5.5 from inputs to results; and a verification record of the bibliography and claim checks, with what could not be closed listed as open. None of this substitutes for independent reproduction, which has not happened.

# 9. Conclusion

**The strongest conclusion here is methodological.** A complete economic model has to separate computational hit generation, experimental realisation, novelty and utility: they have different costs, evidence and failure modes. The literature does not measure the downstream transitions well enough to support a universal cost figure, and trying to build one shows where the measurements are missing.

Four findings, in order of how well the evidence supports them.

**Computational cost differences between pipelines are real and measurable per computational hit.** An MLIP pre-filter cuts modelled cost per robust prediction by 39%, and a generative pool costs 1.8 to 4.0 times a filtered ion-exchange pool at the same gate, the range spanning the two endpoints the source prints for that purity. These rest on measured pool purities and an assumed verification cost.

**Translating those differences into cost per validated material requires downstream assumptions we found no pipeline-specific measurement of.** Under the illustrated academic cost structure and shared downstream behaviour, synthesis is 81 to 94% of modelled cost at base verification expense, and the two pipeline decisions move the total by 3.6% and 16.9%. Neither establishes that compute improvements are economically unimportant --- at the top of our verification-cost span computation is the larger share, 52 to 81% --- nor the ordering, which reverses under a 16.9% relative difference in synthesis success between pipelines, a quantity no study reports.

**Existing synthesis evidence produces order-of-magnitude variation across scenarios, and the mechanism is not the one the dispute is about.** Three readings of essentially two campaigns give medians from roughly \$1,100 to \$34,000, differing in phase-identification standard, denominator and recipe multiplicity as well as success count: non-equivalent scenarios, not an interval around a single quantity. Multiplicity does more work than the success rate --- the reading with the highest success rate is 2.6 times dearer than the cheapest because it attempted each target six times --- so narrowing the range is partly definitional, and closing it needs new synthesis data reported with experiment counts, not better models.

**Therefore the highest-value empirical work is standardised, pipeline-specific synthesis and costing data.** A campaign reporting the following would collapse most of the uncertainty here, and none of it needs new instrumentation:

- candidate source and selection rule;
- the full compute workload, including failed and re-run jobs;
- the number and type of recipes attempted per target;
- labour and instrument time per attempt;
- capital utilisation and downtime;
- the phase-identification protocol, as a standard not an outcome;
- target-level success and novelty determinations;
- denominators defined for comparison across campaigns.

Until such data exist, statements about what AI-driven materials discovery costs are statements about which re-analysis one believes, and should be written that way.

# Disclosures

**Declaration of generative AI use.** During the preparation of this work I used Claude (Anthropic) to draft and revise text from my outlines and instructions, to write and debug the cost-model code and its test suite, to search for and summarise related literature, and to critique drafts adversarially. The research question, the scope, the choice of modelling framework, the parameter values and the conclusions are my own, and I revised the drafted text into my own words. No parameter value originates from the language model: every value traces to a published source, a first-hand measurement, or an explicitly labelled assumption recorded in the parameter manifest. Every reported figure in this paper is regenerated from that manifest by the released code, and a build step fails if a printed figure drifts from it. All AI-assisted output was reviewed, edited and verified by me, and I take full responsibility for every method, interpretation and claim here.

The bibliography and the substantive claims attached to each source were checked against publisher records and source texts in an AI-assisted pass, recorded in full in the replication package together with the claims it could not close. I have reviewed that record and I am responsible for it.

**Conflict of interest.** The author is the founder of Accretion Labs, a company working in AI-driven materials science, and that affiliation appears on the title page. The computational pipeline used for the first-hand benchmarks in Section 4.2 derives from that company's codebase, though the released replication package depends on no proprietary code.

**Data and code availability.** The replication package --- model, parameter file with every source and evidence grade, first-hand benchmark data, analysis code, test suite and verification record --- is not yet public at the time of writing. The repository URL and an archived DOI will be inserted here on release, and no claim in this paper should be read as independently reproduced until they are.

