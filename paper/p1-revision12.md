---
title: "What Does It Cost to Discover a Material?"
subtitle: "An end-to-end cost model of AI-driven inorganic materials discovery"
author: "Karthikeya"
date: "Working paper, revision 12 --- 11 October 2026"
abstract: |
  Artificial intelligence has made the computational stages of inorganic materials discovery extremely cheap, and the field widely asserts that synthesis is now the bottleneck. We did not find it priced in dollars anywhere in our search. We build an end-to-end cost model that follows a candidate material from generation through machine-learned screening, density functional theory verification and laboratory synthesis, and report cost at three output levels: a cross-functionally robust DFT-stable prediction, an experimentally validated material, and one genuinely new to science. The third we can define and compare across pipelines but not price, because the only published novelty count for the reference campaign is zero. Along the way we build a bottom-up estimate of a solid-state synthesis attempt, \$271, from eleven US institutional fee schedules together with assumed throughput, a compensation proxy and an overhead treatment.

  The economic significance of computational pipeline choice depends on which decision is being made. A machine-learned interatomic potential pre-filter cuts cost per robust DFT-stable prediction by 39%, and a generative candidate pool costs roughly four times a filtered ion-exchange pool at that stage. But on the assumption that the synthesis term does not depend on how a candidate was found, the two decisions this implies diverge. Whether to pre-filter changes cost per experimentally validated material by under 10% throughout the tested range of verification cost under our default accounting, though not under every accounting variant we carry. Whether to source candidates generatively passes 10% at roughly 200 core-hours per candidate, between 138 and 219 across those variants. In 20,000 simulations the filtered pipeline is cheaper in 99.4% of draws but by more than 10% in only 1%: an ordering that is reliable and a magnitude that is not.

  What governs the answer is the synthesis success rate, which three groups read three ways from essentially two experiments. Cost per validated material runs from about \$3,000 under the most favourable defensible reading of the originating campaign to about \$50,000 under a published re-analysis of that same campaign, a factor of about 17, and cheaper computation does not close it.

  We also measure filter enrichment on two realistically constructed candidate pools at about half the figure a widely used stability-prediction benchmark reports for its own test set. We do not establish that the benchmark overstates performance: the two evaluations differ in reference hull, candidate distribution and threshold, and we have not run the controlled comparison that would separate these.
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

**Keywords:** materials discovery, machine-learned interatomic potentials, cost model, autonomous laboratories, research productivity. **JEL:** O31, O32.

# 1. Introduction

The computational half of inorganic materials discovery has become very cheap very quickly. Graph neural network potentials relax a crystal structure in seconds on a laptop --- for two of the three potentials we benchmarked (Section 4.2); the third failed to converge on six of seven structures under our cold-start protocol [@deng2023chgnet; @chen2022m3gnet; @batatia2025macemp]. Generative models propose candidates at a few hundred structures per GPU-hour --- at the generation times reported by @szymanski2025baselines, roughly 390 per GPU-hour for one diffusion model on an A100. One recent project reported 2.2 million predicted structures, of which roughly 381,000 were placed on or below the convex hull [@merchant2023gnome]. Against that volume, the experimental half has barely moved: a laboratory still makes one material at a time, and the most prominent autonomous synthesis platform realised 36 of 57 target compounds over 17 days of continuous operation, across 353 synthesis experiments [@szymanski2023alab; @szymanski2026correction].

The field's standard account of this asymmetry is that synthesis has become the bottleneck. @montoya2024 state that synthesis "almost always represents the rate-limiting step in getting real-world feedback into AI and DFT-driven discovery processes"; @chung2025synthesizability that "the rate of materials discovery is limited by the experimental validation of promising candidate materials"; see also @aziz2021 and @tom2024chemrev. What we could not find anywhere is a price for it.

This matters for three reasons. A research group choosing between computational pipelines is implicitly making a budget decision without knowing the budget. A funder deciding between a larger compute allocation and a synthesis robot is comparing two numbers, one of which does not exist. And an investor reading that an AI system finds materials ten or a hundred times faster has no way to know what share of the cost that speed-up addresses.

The question also sits inside a larger one. Research productivity has been falling across sectors: ideas per research dollar decline steadily in @bloom2020ideas, and in pharmaceuticals the decline persisted across six decades of dramatic improvement in the underlying tools --- Eroom's Law [@scannell2012eroom]. @jones2009burden attributes part of the pattern to the rising human-capital cost of reaching the research frontier. AI is widely proposed as the reversal, an "invention in the method of invention" in the phrase @cockburn2018 take up from Griliches. Those are time series of output per unit of input, estimated over decades; ours is a single cross-sectional level, and we do not claim it is a point in either series. What it offers is a decomposition: it says which stage a tool would have to improve for such a series to bend, and that is the question those literatures leave open for any particular field.

This paper builds the missing number. We model discovery as a funnel from candidate generation through machine-learned screening and density functional theory verification to laboratory synthesis, with a cost and a pass rate at every stage, and we price the whole of it in dollars. We compare three pipelines: DFT applied to every candidate; a machine-learned interatomic potential (MLIP) used as a pre-filter before DFT; and a generative model supplying the candidate pool. We report three outputs rather than one, because a cost per "discovered material" that does not say whether the material was ever made, or whether it was new, conceals the question being asked.

Our contributions are:

1. **An end-to-end dollar model of materials discovery**, from generation through synthesis, across three pipelines, with every parameter documented and graded by evidence quality --- including the ones graded as assumptions and the three with no source --- and released with the code.

2. **The result that synthesis is 96 to 99% of the modelled cost of a validated material at base DFT cost, and a threshold for when that stops holding.** The share is a modelled quantity throughout, not a measurement: it pairs a manual-laboratory cost build-up with success rates and recipe multiplicity taken from an autonomous campaign, an assumption we state in Section 3.5 and revisit in Section 7. An MLIP pre-filter cuts cost per robust DFT-stable prediction by 39% and a generative pool costs about four times the filtered ion-exchange pool at the same stage. At the level of a validated material these two decisions separate. Under the default accounting treatment, with other parameters at the deterministic baseline, the filter decision stays under a 10% cost difference throughout the tested range of verification cost, while the generative-pool decision passes 10% at about 200 core-hours per candidate. Under a direct-cost accounting basis the filter decision also crosses, at 729 core-hours. Note that this threshold --- the verification cost at which a *pipeline gap* reaches 10% --- is a different quantity from the verification cost at which synthesis stops being 96 to 99% of the total. We report the threshold rather than a single immateriality claim, because the DFT cost that decides it is the quantity we are least able to pin down (Section 4.3).

3. **The finding that the answer is governed by one contested parameter.** Cost per validated material spans a factor of about 17 across three published readings of the synthesis evidence, which is far larger than any difference between methods. The spread is not measurement uncertainty; two of the three readings interpret the same experiment and disagree about what was made.

4. **A decomposition of where cost sits, and therefore where proportional improvement moves the total.** At the deterministic base a 1% proportional improvement in a synthesis term moves cost per validated material 26 to 105 times as much as the same proportional improvement in compute price, and 36 to 136 times when the same ratio is evaluated at the Monte Carlo medians; at the top of the DFT span the ratio falls to single digits. We do not rank these per dollar of research effort, because the cost of achieving each improvement is unknown. The one lever requiring no research expenditure, switching to spot compute pricing, moves cost per validated material by 0.6% to 2.3%, before any allowance for spot interruption and retry.

5. **An independent observation about benchmark transferability, with the model family held fixed.** CHGNet is the filter in both the benchmark and the pool measurements. Neither source names a version or checkpoint, so the comparison is matched on model family rather than on an identical fitted model. Its discovery acceleration factor is 1.65 on a realistically constructed ion-exchange pool against 3.36 reported on the standard benchmark test set, and 1.27 on a generative pool. Classification rates measured on one candidate distribution did not transfer to ours, and substituting direct measurements where we had used benchmark rates more than halved our estimate of what filtering saves. We report this as an observed discrepancy with several candidate causes, not as a demonstrated property of the benchmark.

6. **A bottom-up modelled estimate of the cost of a solid-state synthesis attempt, for which we did not locate a published equivalent.** We price an attempt at \$271 by combining eleven US institutional fee schedules with assumed throughput, usage allocations, a compensation proxy and an overhead treatment, each graded and individually sourced. The fee schedules are measured inputs; the total is an estimate built on top of them, not a measurement. It determines the synthesis component of every downstream figure --- not the level-1 compute figures, which do not depend on it --- and it is the one output a reader can lift and reuse independently of any disagreement about readings, pipelines or benchmarks. It is an illustrative academic manual-laboratory cost and will not transfer unchanged to another facility.

We also report first-hand timing benchmarks for three MLIPs and for plane-wave DFT, because the quantity the cost model needs --- single-threaded CPU core-seconds per ionic step per atom, and the cold-start convergence rate --- does not appear to be published per model.

# 2. Related work

Three literatures bear on this question and none of them answers it.

## 2.1 Resource accounting of computational discovery

The closest work in structure is @walker2026carbon, which reproduces a DFT workflow for estimating the maximum efficiency of photovoltaic materials, progressively substitutes machine-learned surrogates, and estimates the CO$_2$ emissions of each configuration. The architecture is the same as ours --- a staged pipeline with a substitutable component, costed end to end --- but the unit is carbon rather than money, and the scope is compute: no material is synthesised and synthesis does not enter the accounting. Its conclusion is that machine learning is not yet a complete replacement for DFT, that hybrid workflows therefore sit on an accuracy--emissions frontier with a learned scissor correction as a strong intermediate option, and that carbon cost should be reported alongside predictive performance. Ours concerns what happens when the laboratory is included, which turns out to dominate everything upstream. The two papers agree on the methodological point that resource cost belongs next to accuracy; they differ on which resource binds.

Matbench Discovery frames MLIPs explicitly as triage tools for allocating a DFT budget, and reports a discovery acceleration factor for each model [@riebesell2025]. That is a cost-adjacent framing without a cost: it counts calculations saved rather than money, and stops at the DFT gate. Our Section 5.4 engages directly with the transferability of its metrics. @miller2024flowmm reports a cost per stable material in integration steps, which is a per-method computational cost rather than a pipeline cost.

@szymanski2025baselines compare generative and substitution-based candidate generation on stability, novelty and generation time, and establish that a simple ion-exchange baseline outperforms several generative models. Their comparison is over 500 *novel* materials per method: "For each of these six approaches, 500 materials were considered", with each method run until 500 novel materials were obtained. That is a selection on novelty, not a fixed generation budget, and Section 3.3 notes what it implies for our chaining step. Their measurements are among our most important inputs, and our Section 5.3 restates part of their conclusion in dollars. We emphasise that this is a restatement, not an independent reproduction.

**Gap:** none of these prices the full funnel, and none includes synthesis.

## 2.2 The economics of AI-aided discovery

@agrawal2024 model innovation as sequential search over a combinatorial design space in which a predictive model prioritises costly tests. They show that improvements in prediction fidelity raise the probability of successful innovation and shorten search, and --- centrally for us --- that the gains from better prediction may not be realised without corresponding investment in testing capacity.

@agrawal2026aiinscience sharpen this into a stage-decomposed form: scientific productivity $\omega$ in a knowledge-production function is the product of stage-specific productivity terms, $\omega = \alpha\cdot\beta\cdot\gamma\cdot\delta$, with testing among the stages, and the returns to AI differ by stage. The decomposition is of productivity, not of pass probabilities, so it is an analogue of our result rather than a statement of it. Their model is analytical and uncalibrated; it specifies the conditions under which prediction and testing are complements without saying, for any real discovery problem, how far apart the two stages actually are. Our contribution is to supply that calibration for inorganic materials: at the deterministic baseline, making prediction cheaper has a small modelled effect on the total, because the gap between the compute and synthesis shares is one to two orders of magnitude.

We note a limit on what this calibration can say. The theory is about prediction *fidelity*, and our model varies compute *price*. Better verification might raise experimental success, or lower it by rejecting makeable candidates, and it would certainly cost more compute; we do not estimate that joint relationship, and nothing here should be read as doing so. Cross-functional disagreement between levels of theory is reported separately and is not treated as an experimental failure probability.

Evidence on what AI does to realised scientific output is thinner than the theory. @kusumegi2025, across 2.1 million preprints, report increases in paper production among adopters of large language models ranging from 23.7% to 89.3% across fields, associated with an inversion of the usual relationship between a paper's complexity and its quality --- more output, not more validated output. The association is not identified as causal, and a Comment disputes aspects of the analysis [@renault2026comment]. We therefore treat the finding as suggestive rather than settled. We are aware of no credible direct estimate of AI's productivity effect inside a materials laboratory. The empirical base for this question is close to empty, which is itself part of our motivation.

The methodological template for a cost-per-validated-output figure comes from pharmaceuticals, where @dimasi2016 attribute the cost of abandoned candidates to the survivors. We adopt that survivor-attribution convention and not the rest of their method: their figure is capitalised over a decade-long development cycle and carries allocated company-level fixed cost, whereas ours is uncapitalised and charges no *explicit* equipment or capital. Recharge fees and institutional overhead plausibly embed some depreciation and facility cost, so the distinction is between absent explicit capital and implicit capital of unknown size, not between some capital and none. For a 17-day campaign the omission of capitalisation is defensible; for a facility it would not be, and Section 6.3 treats the missing capital term as the largest unmodelled structure in the paper. @buchner2018tea matches cost-estimation method to technology readiness level and specifies which profitability measures are legitimate at low TRL; it licenses the static, order-of-magnitude approach we take and explains why we do not compute a net present value. See also @kobos2020tea.

## 2.3 The synthesis evidence and its contestation

The empirical base for synthesis success is thin and disputed, and this turns out to be the central fact of the paper rather than a caveat on it.

The A-Lab campaign reported realising a set of target compounds from computational predictions over 17 days of autonomous operation, with two further targets formed after products were manually reground and reheated to higher temperatures [@szymanski2023alab]. On the corrected count it realised 36 of 57 targets. Following publication, concerns were raised about structural identification and novelty. An Author Correction re-analysed the reported successes, found four inconclusive from X-ray diffraction alone, removed one compound that had been included in the training data, and clarified that the authors' "intention was to indicate that the materials were new to the prediction platform, not necessarily new to science" [@szymanski2026correction]. @leeman2024 published a re-analysis of the same campaign reaching a substantially more pessimistic count --- three of 58 successfully synthesised, of which they regard only one, CaFe$_2$(PO$_4$)$_2$O, as convincingly demonstrated --- and finding none of the compounds new. @prein2025 report a separate, smaller campaign falling between the two.

Separately, large-scale generative predictions have been questioned on novelty grounds: a critique of one 380,000-structure stable set reports that a random sample of ten entries all matched known structure types, and that a substantial share contain radioactive elements [@cheetham2024].

**Gap, and our position in it.** We do not adjudicate this dispute. We take the three readings as three coherent worldviews, propagate each through the cost model, and report what each implies. The resulting factor of about 17 is, we argue, the most policy-relevant number in the paper: it says that the field does not currently know what a validated material costs to within an order of magnitude, and that the disagreement is about what was synthesised rather than about anything a cheaper or faster computational stage would settle. Resolving it needs agreed phase-identification standards and reconciled denominators, and in the end new synthesis campaigns --- not better models.

# 3. Model

## 3.1 The funnel

We model discovery as a funnel. A pipeline begins with a batch of candidate structures and ends with a material made in a laboratory. Each stage has a cost per candidate entering it and a pass rate; every candidate entering a stage is paid for, including those that fail. Cost per output is total spend divided by survivors at the output level in question.

| Pipeline | Stages |
|:--|:-----------|
| A | ion-exchange pool, drop structures already in the reference database, DFT on every candidate, synthesis |
| B | ion-exchange pool, drop known, MLIP relax-and-classify, DFT on the survivors, synthesis |
| C | generative model, drop known, MLIP, DFT, synthesis |

The ion-exchange pool is generated by the data-mined probabilistic ion-substitution model of @hautier2011substitution, as implemented in pymatgen [@ong2013pymatgen] and used as the substitution baseline by @szymanski2025baselines. The generative pool is a diffusion model for inorganic crystal structures [@zeni2025mattergen], in the MP-20 retrained configuration evaluated by @szymanski2025baselines rather than the larger released foundation model. Our results about this pool apply to that configuration only. The funnel architecture itself is not new: screen-then-synthesise dates to @greeley2006, and high-throughput DFT screening to the database projects of the following decade [@curtarolo2012aflow; @jain2013mp; @kirklin2015oqmd], reviewed by @curtarolo2013htdft.

Every pipeline pays to generate its own candidates. Checking whether a structure already exists in the reference database is not charged. This is a simplification: structure matching against a database of Materials Project scale involves reduced-cell comparison and symmetry analysis and is not free. We have not measured it. It is charged per raw candidate, so it does not fall equally --- pipelines generating larger raw pools pay more --- and because it sits upstream of the filter it would compress rather than widen the level-1 gap between pipelines A and B.

## 3.2 Three output levels

1. **Per cross-functionally robust DFT-stable prediction** --- one candidate that DFT places on or below the convex hull, discounted by the share whose stability does not survive a higher level of theory. We avoid calling this "correct": $w$ is a disagreement rate between two calculations, not a verdict against experiment, and the label should not imply established truth. The quantity is not the cost of a DFT-stable verdict, which would be cheaper by a factor of $1/(1-w)$.
2. **Per experimentally validated material** --- one material subsequently synthesised as the target phase.
3. **Per validated new material** --- one such material also new to science rather than new to the prediction platform.

The second and third differ materially. The A-Lab correction states that the materials were new to the prediction platform, not necessarily new to science [@szymanski2026correction]. A model that conflates these overstates what the money bought. The second and third also differ from the first for a reason older than any of this evidence: thermodynamic stability does not imply that a synthesis route exists [@jansen2002].

## 3.3 Stage costs

**MLIP cost per candidate.** An MLIP relaxation is a sequence of ionic steps. Our benchmark finds per-step cost close to linear in cell size (log--log slope near one) and step count independent of size, ranging from 18 to 81 steps. A fraction of relaxations never converge and run to the step cap; these are charged in full and produce nothing. With $k$ core-seconds per step per atom, $n$ atoms, $\bar{s}$ mean steps, $q$ the non-convergence fraction and $s_{\mathrm{cap}}$ the cap:

$$\text{cost} \;=\; k \cdot n \cdot \frac{(1-q)\,\bar{s} + q\,s_{\mathrm{cap}}}{3600} \quad \text{core-hours}$$

The non-convergence term deserves emphasis. In our benchmark one of three potentials failed to converge on six of seven structures when started from raw generated geometries --- a failure mode invisible in the production pipeline it came from, because that pipeline always fed it pre-relaxed structures. An MLIP's effective cost is per-step cost times step count divided by convergence rate, and the third factor is rarely reported.

**DFT cost per candidate.** Modelled as a span rather than a point (Section 4.3).

**What the filter lets through.** With measured post-filter purity $P$, pool stability $\pi$ and recall $R$, the pass fraction is $\pi R / P$ and the DFT-stable share of what passes is $P$. The alternative formulation, from a benchmark confusion matrix, gives a pass fraction of $\pi R + (1-\pi)\,\mathrm{FPR}$. Section 5.4 shows these disagree substantially; we take measured purity as primary.

**Chaining.** To obtain $N$ candidates absent from the reference database, a method must generate $N$ divided by its novel share. Each stage takes what the previous one released.

One caution on this step. The stability rates we take from @szymanski2025baselines are measured over samples of 500 *novel* materials per method, each method having been run until that many novel materials were obtained. Those rates are therefore already conditioned on novelty. Dividing by the novel share again would charge the novelty filter twice. We believe the model applies the division only to the generation count and not to the stability rates, but this is exactly the kind of double-count that is easy to introduce, and it is on the list of checks for the released package.

## 3.4 Wrong verdicts

A share $w$ of DFT "stable" verdicts do not survive scrutiny. Our proxy for it is the *cross-functional stable-to-unstable transition rate*: the directed fraction of candidates called stable at one level of theory that are called unstable at a higher one. We use the shorthand "wrong verdict" for readability, but the quantity is a disagreement between two calculations, not experimental ground truth, and a material above the hull is not thereby impossible to synthesise [@kingsbury2022r2scan; @an2026; @merchant2023gnome]. The underlying error scale is well documented: GGA formation-energy errors against experiment are of order 0.1 eV/atom [@kirklin2015oqmd]; surrogate models inherit and compound them [@bartel2020]; corrections reduce but do not eliminate them [@wang2021corrections]; and about half of ICSD-reported compounds sit above the computed hull at all [@sun2016metastability].

Every candidate sent to synthesis incurs the allocated cost, including the targets that are never made. Observed unconditional campaign success determines experimental-output costing; cross-functional transitions define a separate computational endpoint and are not treated as an experimental failure probability. We do not claim that a candidate whose stability flips under a higher level of theory cannot be synthesised --- roughly half of ICSD-reported compounds sit above the computed hull [@sun2016metastability] --- only that it fails the computational test level 1 defines.

Synthesis success is **not** conditioned on the verdict being correct. Each campaign's observed success rate already embeds whatever computational failure that campaign experienced, so dividing by $(1-w)$ as well would charge the same failures twice. $w$ is retained for the level-1 output, where the question is what a cross-functionally robust prediction costs, and is reported separately as a diagnostic.

An earlier version of this model did condition one of the three readings and not the other two, and then divided all three by $(1-w)$. That inconsistency has been removed, and removing it lowered cost per validated material by about 16% before the accounting change of Section 4.5 is applied.

### Which optimistic value, and why 36 of 57

The A-Lab campaign supports several success counts. Because the model now takes unconditional rates, the choice is narrower than it was, but it still moves the optimistic branch.

| Count | Value | What it includes |
|:--|:--|:---------------|
| 36 / 57 | 63.2% | The corrected figure, unconditional. **Used.** Includes the three targets that failed for computational reasons, as an unconditional rate should. |
| 36 / 54 | 66.7% | Excludes the three computational failures, so it is a conditional rate and overstates unconditional success unless a separate failure multiplier is applied. |
| 38 / 57 | 66.7% | The paper's own alternative figure: counts the two targets formed after manual regrinding and reheating, against all 57 targets. |
| 38 / 54 | 70.4% | Excludes computational failures *and* counts the manual-intervention successes. |

We take **36 of 57, 63.2%** --- the corrected count, unconditional, as the campaign reports it. The 36/54 rate excludes computationally attributed failures and therefore does not estimate unconditional campaign success; it would be the right quantity only alongside a separate computational-failure multiplier, which the model no longer applies. The 38/57 count adds two targets realised only after an operator reground and reheated the products, an intervention the autonomous protocol being costed does not include and whose labour the model does not charge.

Two cautions. The 2023 printing reported a higher count, before four targets were found inconclusive from diffraction alone and one was removed as training data; 36/57 is the post-correction figure. And the target-level crosswalk that would confirm the four inconclusive targets are not subtracted twice is still outstanding, so 36/57 is a proposed baseline rather than a settled count.

## 3.5 Synthesis cost

We did not locate a published dollar cost per solid-state synthesis attempt, or a capital or operating cost for an autonomous bulk solid-state synthesis laboratory, within our search scope (Section 6.3). We state these as search outcomes rather than as established absences. We build the attempt cost bottom-up:

$$\text{direct} = \text{XRD} + \text{furnace} + \text{labour} + \text{crucible/firings} + \text{precursor mass} \times \text{price} + \text{other consumables}$$
$$\text{per attempt} = \text{direct} + \text{tuition} + r \times (\text{direct} + \text{tuition})$$
$$\text{per target} = \text{recipes per target} \times \text{per attempt}$$

Labour pairs a graduate trainee's stipend and institutional allowance [@nih2026stipends] with a trainee throughput of 10 to 20 compositions per week, so person and throughput match. Two caveats: the NRSA training allowance is a funding instrument, not an ordinary wage fringe rate, and the throughput range is an assumption, graded as such, not a published measurement. The composition unit here is the attempt, not the target. Crucible cost is divided by firings survived. The reference campaign ran 353 experiments across 57 targets [@szymanski2023alab], a mean of 6.193 recipes per target, and the model charges that mean. It is an average allocation, not a claim that every target underwent 6.193 attempts; failed targets consumed more of the budget and successes fewer, which is why Section 4.4 draws recipes jointly with the success rate.

Instrument time is priced at published institutional recharge rates, taken from the published fee schedules of eleven US university facilities. The parameter file lists each with its facility, date, URL, internal and external rate, unit and the time or quantity we charge. The eleven are not eleven independent measurements of an attempt cost: they are a price range for two line items, from which we take a central value. This may understate the true resource cost: @strom2020 report that user-fee income alone does not fully support most shared instrumentation facilities, which implies that published rates can omit subsidised components. We apply that directionally to the XRD and furnace line items and do not claim it as a bound on the attempt cost as a whole, which also contains terms with no such subsidy argument. @sorzano2026 model the full cost of laboratory equipment and the trade-offs between shared and dedicated provision, which is the quantity a recharge rate approximates. To the extent it holds, the direction is favourable to our conclusion, since it makes those two line items conservative and synthesis already dominates.

At base an attempt costs **\$271**: XRD \$80.00, indirect cost \$80.05, labour \$40.47, furnace \$37.90, tuition \$20.51, other consumables \$5.58, crucibles \$3.49 and precursors \$2.64. On a direct-cost-only basis it is \$191. The parameter file carries the unrounded components and the time, mass and throughput allocation behind each quoted rate. The indirect-cost rate $r$ is applied to total direct costs including service-centre fees and tuition, which is the base its source defines it over; at $r = 0.42$ that base is \$190.59. An MTDC-like variant excluding fees and tuition is retained as a scenario in Section 4.5.

## 3.6 Fixed and marginal cost

Entering a new chemistry can require computing the known phases forming the convex hull once, before any candidate can be judged [@aykol2019network]. That cost is amortised over the batch's outputs and halves when the batch doubles --- but only within a single chemical system. For a pool spanning many systems, reference-phase cost is closer to linear in the number of distinct systems, so it does not amortise, and it is pipeline-dependent to the extent that pools differ in how many distinct chemical systems they span, which we have not measured. We set the reference-phase count to zero at base, reusing the published hull as the source experiments do, and flag both the missing count and the unmodelled pipeline dependence as open gaps.

## 3.7 Dollars

All compute is held in core-hours and GPU-hours until a final step where a single price parameter converts it, isolating the price assumption to one line.

# 4. Parameters

Every parameter carries low, base and high values, a unit, a source URL and an evidence grade. Nothing is hardcoded; figures in this paper are generated from the parameter file and the benchmark data, and the test suite fails if a figure in the text drifts from the model.

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

Grading explicitly matters because the paper's central result is a claim about evidence quality as much as about cost. Three parameters carry grade `missing` and are named as such in Section 7: precursor mass per attempt for the autonomous-laboratory case, the reference-phase count of Section 3.6, and the high value of the tuition term.

## 4.2 First-hand measurements

We benchmarked three MLIPs [@deng2023chgnet; @chen2022m3gnet; @batatia2022mace; @batatia2025macemp] and plane-wave DFT [@giannozzi2009qe; @giannozzi2017qe] on seven structures spanning 10 to 56 atoms, with repeats, a thread-count sweep and documented protocols, using ASE optimisers [@larsen2017ase] and GBRV ultrasoft pseudopotentials [@garrity2014gbrv].

These timings are reported as a **screening benchmark in their own right** --- per-model single-threaded CPU cost per ionic step per atom, with cold-start convergence rates, which we could not find published --- and are used in the economic model only as an illustrative low endpoint (Section 4.3). They are not a measurement of the MP-compatible verification workflow.

Two findings bear on the model. First, single-threaded execution is the cost-minimising configuration: core-hours are allocated cores times wall time, and on our platform twelve threads cost 32 to 90 times the core-hours of one. Second, the specific quantity the model needs --- single-threaded CPU core-seconds per ionic step per atom, with cold-start convergence rates --- does not appear to be published per model. Throughput and inference figures are reported in the model papers and in Matbench Discovery; the per-step CPU cost and the cold-start convergence rate are not.

Our hardware is unusual --- an ARM64 laptop under virtualisation --- and we report it as such. DFT timings carry a platform artefact: a twelve-rank configuration cost 2.6 to 7.3 times the core-hours of a four-rank one. All DFT figures therefore use four ranks, with twelve-rank values retained as documented upper bounds. For a controlled scaling measurement we compare a 28-atom cell against its own 56-atom supercell, identical in chemistry and pseudopotentials: 0.480 against 3.842 core-hours, a factor of 8.0, an exponent of 3.0.

## 4.3 DFT cost: a span, not a point

DFT cost per candidate is modelled as a span from 3 to 1,000 core-hours:

- **Low, 2.98 core-hours:** our own measurement. It is a *screening relaxation* in Quantum ESPRESSO with GBRV ultrasoft pseudopotentials, not the Materials Project-compatible workflow that produced the hull our stability labels are judged against, so it is an illustrative low endpoint rather than a measured cost of the verification task the model prices. We do not claim it bounds that cost from below: energy incompatibility and runtime are separate questions, and we have not measured an MP-compatible calculation on comparable hardware.
- **High, 1,000 core-hours:** a large public database project circa 2012, being one to five calculations per material at roughly 200 CPU-hours each with a 10 to 20% failure-and-rerun rate, on decade-old hardware. These operational figures come from a presentation by the project's lead on its production workflow [@jain2012nersc], not from the database description paper [@jain2013mp], which contains no compute accounting. We flag the source type: it is a conference presentation, and the figures should be treated as indicative of 2012 practice rather than as a published measurement.
- **Base, 54.5 core-hours:** the geometric midpoint, a convention rather than a measurement. The Monte Carlo samples the span log-uniformly.

Because the low endpoint is illustrative, we do not treat the span's geometric midpoint as a measured base case. Section 5.5 therefore reports DFT cost as a direct sensitivity, with the cost at which each pipeline decision reaches a given materiality threshold, rather than resting the conclusion on one base value.

## 4.4 The contested parameter

| Reading | Success | Standing |
|:--|:--|:-------------|
| Optimistic | 36 of 57 (63.2%) | Peer-reviewed and corrected; unconditional [@szymanski2023alab; @szymanski2026correction] |
| Middle | 7 of 16 (43.8%) | Preprint, 16 targets [@prein2025] |
| Pessimistic | 3 of 58 (5.2%) | Peer-reviewed re-analysis of the first campaign; only one of the three regarded as convincing [@leeman2024] |

The first and third read the *same experiment* and disagree about what was made. The second is a separate, smaller campaign between them.

All three are now unconditional rates on their own denominators: 57 is A-Lab's corrected target count, 16 is Prein's, and @leeman2024 count against 58, the target count as originally printed. We do not force them onto a common denominator, because part of the disagreement is about what counts as a target.

Synthesis success, novelty and the wrong-verdict share all come from these same re-analyses, so they are not independent. The Monte Carlo draws one reading per sample and takes all three from it; independent sampling would generate combinations corresponding to no coherent reading of the evidence. Recipes per target are drawn jointly too, since failed targets consume more of the recipe budget.

## 4.5 Accounting choices

Institutional overhead is the largest single accounting choice in synthesis cost, and at base DFT cost synthesis is 96 to 99% of the level-2 figure.

**The rate.** @azoulay2025icr report, across 354 NIH-funded institutions, that *negotiated* indirect-cost rates average 58% while *effective* rates average 42%. The two are not interchangeable, and the distinction matters for how we apply them. The effective rate is defined as recovered indirect costs divided by **total direct costs**; the negotiated rate applies to **modified total direct costs**, a narrower base that excludes certain categories. The 25% to 45% range for effective rates is quoted from the same study by @crs2026indirect.

We take **42% at base and apply it to total direct costs**, which is the base its source defines it over. An earlier version applied it to a narrowed base excluding service-centre fees and tuition; that was a rate/base mismatch, and correcting it raises the indirect term per attempt from \$21.91 to \$80.05. The narrowed base is retained below as an accounting scenario, not as an alternative definition. The high value of 45% is the top of the effective range. A 58% row appears as a negotiated-rate illustration: 58% is an average of a different quantity and is not an upper bound on an effective rate. We follow the source's vocabulary in calling this indirect cost recovery rather than F&A.

Two caveats on this source: its data are NIH indirect-cost records rather than a census of US universities, and it reports averages across institutions rather than a rate any one laboratory faces.

**The base.** The retained MTDC scenario excludes service-centre fees on the reasoning that federal rules direct recharge rates to be composed of direct costs and an allocable share of indirect costs [@cfr200468], so applying institution-wide overhead on top risks counting some of it twice. We treat that as an accounting convention rather than a demonstrated fact: the rule does not establish that any particular facility's fee schedule absorbs the same cost pools an institution-wide rate covers, and we have not inspected those pools. It is a scenario in the table below rather than the default, because pairing an effective rate with a narrowed base is a mismatch whatever the merits of the exclusion.

| Basis | \$ per attempt | Level 2: A / B / C |
|:---------|--:|:-----------|
| Direct costs and tuition, no indirect recovery | 191 | \$2,758 / \$2,734 / \$2,845 |
| Effective 42% on an MTDC-like base (fees and tuition excluded) | 213 | \$3,069 / \$3,045 / \$3,155 |
| **Effective 42% on total direct costs (default)** | **271** | **\$3,891 / \$3,868 / \$3,978** |
| Effective 45% on total direct costs (top of the effective range) | 276 | \$3,972 / \$3,948 / \$4,059 |
| Negotiated 58% on total direct costs (a different quantity) | 301 | \$4,323 / \$4,299 / \$4,410 |

Between the extreme variants the level-2 figure moves by 57%. The second row is the pre-correction treatment, retained so the effect of the rate/base change is visible: moving 42% from the narrowed base to total direct costs raises the indirect term from \$21.91 to \$80.05 per attempt and level-2 cost by 27%.

We default to including overhead because the question is the resource cost of a validated material, which a funder bears.

# 5. Results

## 5.1 Base case

| Output | A | B | C |
|:-----------|--:|--:|--:|
| 1. per robust DFT-stable prediction | \$31.48 | \$19.05 | \$76.61 |
| 2. per experimentally validated material | \$3,891 | \$3,868 | \$3,978 |
| --- of which compute | \$60.44 | \$36.58 | \$147 |
| --- of which synthesis | \$3,831 | \$3,831 | \$3,831 |

The synthesis term is identical across pipelines. This is structural, not coincidental.

## 5.2 An MLIP pre-filter cuts DFT cost by 39%, not several-fold

Pipeline B costs \$19.05 per robust DFT-stable prediction against A's \$31.48, a ratio of 1.65, so B is 39% cheaper. The filter saves money because DFT then runs on a pool that is 15.2% stable rather than 9.2% [@szymanski2025baselines]. The relaxations themselves cost about three cents.

The ratio is not independent of Section 5.4: because DFT spend per stable hit is DFT cost divided by purity, the level-1 cost ratio between two pipelines approaches their purity ratio whenever DFT dominates the compute term --- which it does at base, where the relaxations cost about three cents. So 1.65 here and the ion-exchange acceleration factor of 1.65 in Section 5.4 are very nearly the same quantity reached from two directions; generation, filter and convergence costs account for the small difference. We report both because they answer different questions --- what a filter saves, and whether a benchmark predicts it --- but a reader should not count them as two findings.

**An earlier version of this analysis reported a fourfold benefit, and the correction is worth reporting because the error is easy to repeat.** That version took classification rates from a benchmark measured on one candidate distribution [@riebesell2025] and applied them to a differently constructed pool. Those rates predict that 37% of filter-passed candidates are DFT-stable; direct measurement on the actual pool gives 15.2%. Substituting the measured value more than halves the estimated benefit.

## 5.3 A generative pool costs about four times as much, through purity at the DFT gate

Pipeline C costs \$76.61 per robust DFT-stable prediction against B's \$19.05. Both run the same filter-then-DFT funnel; what differs is what reaches DFT. After filtering, 15.2% of ion-exchange candidates are DFT-stable against 3.8% of generated ones [@szymanski2025baselines]. DFT spend per stable hit is DFT cost divided by purity, so the ratio is approximately 15.2/3.8. Generation cost plays no part: the generative model's GPU time is 0.5% of C's compute spend.

Two qualifications. This is not an independent reproduction of @szymanski2025baselines' conclusion, because the model takes their measurements as inputs; it restates them in dollars. And its magnitude rests on a value the source prints as a range rather than as a single number: the main text gives 3.8% to 8.8% for diffusion-model candidates after filtering, and assigning 3.8% specifically to the configuration we model is our reading, not the source's statement. Taking the two ends of that printed range against the ion-exchange purity of 15.2%, the DFT-dominated ratio spans roughly 1.7 to 4.0. An earlier draft quoted 2.2 to 6.7 here; that range came from a wider uncertainty interval on a single figure-read value and does not follow from the printed range, so we withdraw it. The 1.7-to-4.0 figures are the simple purity-ratio approximation and have not been regenerated from the full model. The direction never reverses across the range.

## 5.4 Measured enrichment on these pools is about half the benchmark's reported figure

The discovery acceleration factor (DAF) is the ratio of a filter's precision to its pool's prevalence --- how many times more often a filter-passed candidate is stable than a random one. @riebesell2025 define it this way, so the comparison requires no assumption about which classifier rate transfers. The filter is CHGNet in both settings: @szymanski2025baselines state that they "used CHGNet to compute the internal (0 K) energies of all candidate materials", and 3.36 is CHGNet's reported value on the benchmark test set. The comparison is therefore matched on model family. Neither source names a version or checkpoint, so we do not claim identical fitted models.

| Pool | Stable fraction | Purity after filter | DAF |
|:-----|:-----|:--|--:|
| Benchmark test set, CHGNet [@riebesell2025; @riebesell2025correction] | 15.3% (32,942 of 215,488) | --- | 3.36 |
| Ion-exchange pool, CHGNet [@szymanski2025baselines] | 9.2% | 15.2% | **1.65** |
| Generative pool, CHGNet [@szymanski2025baselines] | 3.0% | 3.8% | **1.27** |

On a realistically constructed ion-exchange pool, enrichment is 1.65 against the 3.36 reported. On the generative pool it is 1.27: the filter barely enriches at all. Because the acceleration factor depends on prevalence, applying the benchmark's own rates at each pool's prevalence gives a prevalence-adjusted comparison, 1.65 against 4.05 --- a larger gap still. This adjustment assumes the benchmark's classifier rates transfer to our pools, which is the assumption the rest of this section questions, so we report it as a calculation under that assumption rather than as a like-for-like measurement.

The mechanism, which rests on an assumption, is that if the benchmark's recall transfers, measured purity implies a false-positive rate of 0.43 on the ion-exchange pool against 0.13 on the benchmark. The alternative attribution requires recall of 0.23 on our pool. We cannot rank these two against each other: recall is a population-specific quantity and both values can be correct for their own populations. We report both conditional calculations and resolve neither; the acceleration-factor comparison does not depend on the choice.

**Two explanations, one unresolved.** Distribution shift is a live candidate explanation, and the source itself raises it. It is not the whole story on its face: the benchmark's test set was itself built by elemental substitution from the same database. The construction is not identical, however. The benchmark's set was built over several generations, each substituting into the relaxed outputs of the last, whereas our ion-exchange pool is single-generation. The benchmark's *evaluation* inputs are unrelaxed, as ours are, so the two do not differ in that respect; they may still differ in composition diversity and in the geometry distribution inherited from multi-generation construction. We have not measured either, so we cannot rule distribution shift in or out. The competing explanation is definitional. The two studies judge stability against different reference sets. @riebesell2025 judge against the Materials Project hull; @szymanski2025baselines judge against phase diagrams that "included all entries from MP (as of June 2025) as well as the entries generated from each AI model or baseline approach", which is a stricter test on two counts: the self-inclusion of the candidate pool, and the growth of the reference database between the two studies. A stricter reference lowers both prevalence and the passed-candidate stable share, so part of the gap may be definitional rather than a weakness of the models.

We note that @riebesell2025 do not rule out the stricter construction. They decline a combined reference set, concede that their choice "could consequently be interpreted as overestimating the performance" of the models while noting that the overestimate shrinks as the hull becomes better sampled, and leave the combined set to future work. Their stated reason for declining it is that it would make evaluation path-dependent, not that it is wrong. Public data can resolve this by recomputing the benchmark's acceleration factor against the joint reference set. Until then the gap is a measured fact with an open cause and a specified experiment to close it.

## 5.5 Under the base calibration, pipeline choice moves little once synthesis is included

Two decisions are bundled inside "pipeline choice" and they do not behave alike. Comparing each against pipeline B, the cheapest throughout the range swept below, separates them: $(A-B)/B$ is the value of the MLIP pre-filter, and $(C-B)/B$ the value of sourcing candidates generatively. Both are reported with synthesis success, recipes and attempt cost held shared across pipelines throughout.

**One denominator, stated once.** Every relative cost difference in this section and the next is the gap of the dearer pipeline over the **cheaper** one, $\max/\min - 1$. The convention matters because the two directions are not the same number: A exceeding B by 10% is B falling short of A by 9.09%, so measuring against the dearer pipeline would make the same difference look smaller and would move every threshold reported here. The choice of the cheaper pipeline as denominator is the decision-relevant one --- it asks what premium the dearer option carries --- and it is symmetric in its arguments, so it does not depend on which pipeline is named first. That last property is what makes it usable in Section 5.6, where which pipeline is cheaper varies from draw to draw.

| DFT core-h per candidate | $(C-B)/B$ | $(A-B)/B$ | B compute share |
|--:|--:|--:|--:|
| 3 | 0.2% | 0.0% | 0.1% |
| 10 | 0.5% | 0.1% | 0.2% |
| 30 | 1.6% | 0.3% | 0.5% |
| 54.5 | 2.9% | 0.6% | 0.9% |
| 100 | 5.2% | 1.1% | 1.7% |
| 200 | 10.2% | 2.2% | 3.4% |
| 300 | 15.0% | 3.3% | 5.0% |
| 500 | 24.2% | 5.2% | 8.0% |
| 1,000 | 44.7% | 9.7% | 14.9% |

Taking a 10% cost difference as the materiality threshold and holding all other parameters at the deterministic baseline, the generative-pool decision reaches it at **197 core-hours** per candidate and the filter decision at **1,034**. At a 5% threshold the two are 96 and 474. The 1,034 figure lies beyond the 1,000-core-hour top of the tested range and is an extrapolation of the fitted cost relationship, not an observed crossing.

**Where the crossing comes from.** Upstream compute expenditure per candidate reaching synthesis is affine in DFT cost $d$ (in core-hours per candidate):

$$c_{0i}(d) \;=\; \alpha_i\,d + \beta_i$$

where $\alpha_i$ (dollars per core-hour) carries the compute price and the number of candidates verified per candidate reaching synthesis, and $\beta_i$ (dollars) collects generation, filtering and any cost independent of $d$. Fitting against the model gives $\alpha = 0.485$, $0.293$ and $1.174$ \$/core-h and $\beta = 0.0006$, $0.0016$ and $0.338$ \$ for A, B and C. The relation is affine to machine precision --- worst relative residual $8 \times 10^{-16}$, tested out to 2,000 core-hours --- for the *unrounded* coefficients, not the rounded ones printed here; both, with residuals, are in the replication package. The ratio $\alpha_C/\alpha_B$ is exactly 4.0, which is the purity ratio of Section 5.3 --- an identity, not a coincidence of rounding.

Writing $b = ra$ for the shared synthesis expenditure per target, \$1,676 at base, $(C_C - C_B)/C_B = \tau$ gives

$$d^{*} \;=\; \frac{\tau b + (1+\tau)\beta_B - \beta_C}{\alpha_C - (1+\tau)\,\alpha_B}$$

A positive denominator is necessary but not sufficient for a usable crossing: the solution must also be nonnegative, since $d$ is a verification cost and negative values are outside the domain. A negative $d^{*}$ with a positive denominator means the gap already exceeds $\tau$ at zero verification cost, so there is no crossing to report and the formula returns a number to discard. At our parameters both conditions hold: the denominator is 0.851 and $d^{*}$ is positive at every threshold we report.

At $\tau = 0.10$ the closed form and the model's bisected root are the same number, 196.57, agreeing to a relative $2 \times 10^{-15}$, as they must be if the relation is affine; both round to the 197 above. Reproducing it from the rounded coefficients gives 196.4 instead.

The threshold is therefore **affine in the synthesis bill, not proportional to it**. The intercept terms contribute 0.2% of $d^{*}$ at our parameter values, because generation and filtering cost cents against hundreds of dollars of DFT, so the crossings move almost exactly in proportion to attempt cost across the accounting variants below. That near-proportionality is a property of these parameters, not an identity: a pipeline with a large $d$-independent cost would break it.

| Accounting basis | \$ per attempt | Generative, 10% | Filter, 10% |
|:--|--:|--:|--:|
| Direct costs only | 191 | 138 | **729** |
| Effective 42% on an MTDC-like base | 213 | 154 | 812 |
| Effective 42% on total direct costs (default) | 271 | 197 | 1,034 |
| Negotiated 58% on total direct costs | 301 | 219 | 1,151 |

The generative-pool crossing sits between 138 and 219 core-hours across every accounting treatment we carry, so that result is robust in shape. The filter crossing is not uniformly outside the tested range: under direct-cost accounting it falls at 729 core-hours, **inside** the span. The statement that the filter decision stays below 10% throughout the tested range therefore holds under the default overhead treatment and fails under the direct-cost one, and we report it with that condition attached rather than as a general property.

This is why we report thresholds rather than a single immateriality claim. The quantity that decides them is the one Section 4.3 says we cannot pin down, and the second quantity that decides them is an accounting choice.

The near-equality at low DFT cost is structural. Level-2 cost is

$$C \;=\; \frac{c_0 \;+\; r\,a}{S}$$

with $c_0$ the upstream compute expenditure per candidate sent to synthesis, $r$ recipes per target, $a$ cost per attempt and $S$ the unconditional synthesis success rate. Level-2 cost does not depend on $w$ at all: the level-1 quantity $c$ is defined per cross-functionally robust prediction, so $c_0 = (1-w)\,c$ and the two factors cancel. At base, $c_0$ is \$26.44 for pipeline A, and $(26.44 + 6.193 \times 270.64)/0.4375 = \$3,891$.

Neither $r$ nor $a$ nor $S$ is pipeline-dependent. Every DFT-stable verdict proceeds to synthesis; the wrong-verdict share, success rate, recipes per target and cost per attempt are *assumed* identical however the candidate was found. This is imposed by the model's structure, not tested by it: sweeping parameters confirms the arithmetic, not the assumption.

| DFT core-h | Level 1: A / B / C | Level 2: A / B / C | Spread | Synthesis share |
|--:|:------|:--------|--:|:--|
| 2.975 | \$1.72 / \$1.04 / \$4.56 | \$3,834 / \$3,833 / \$3,840 | 1.00x | ~100% |
| 54.5 | \$31.48 / \$19.05 / \$76.61 | \$3,891 / \$3,868 / \$3,978 | 1.03x | 96--99% |
| 1,000 | \$577 / \$349 / \$1,398 | \$4,939 / \$4,502 / \$6,514 | 1.45x | 59--85% |

A separate sensitivity varies the span's *low endpoint* and recomputes the geometric midpoint. That tests the base-selection convention rather than DFT cost, and we note it only to distinguish the two: the pipeline spread there runs from 3% to 22% as the low endpoint moves from 3 to 200 core-hours. The replication package will regenerate it.

**The 1.03 is conditional, not a bound.** It assumes synthesis success, recipes and attempt cost do not depend on how a candidate was found. There is a plausible direction for the first --- MLIPs are trained on databases dominated by materials that have actually been made, so a pre-filter may favour candidates that are *more* synthesisable, which would widen the spread --- but plausibility is not a proof, and pipeline-specific differences in recipes or attempt cost could push either way. Section 7 treats this as the primary threat to validity.

## 5.6 Under uncertainty: ordered but immaterial

Across 20,000 draws respecting the documented correlations, with pipelines compared pairwise within each draw:

Three quantities, defined precisely because they are easy to confuse. **P(B < A)** is the share of draws in which B's cost is below A's *in the same draw*, so both see one parameter world. **P(differ > 10%)** is the share of draws in which the dearer of the pair exceeds the cheaper by more than 10%, $\max(C_A, C_B)/\min(C_A, C_B) - 1 > 0.10$, again paired within a draw and on the same denominator convention as Section 5.5. **Overlap of marginals** is the overlap coefficient of the two marginal cost distributions, on a 60-bin histogram of $\log_{10}$ cost over the pooled finite range of all three pipelines, summed as $\sum_k \min(h^A_k, h^B_k)$; its bins hold normalised probabilities, not densities, each count divided by the number of draws, so the bins sum to one and the coefficient is scale-free, but it is not divided by bin width. The first two are paired comparisons; the third deliberately is not, which is why it can be high while the ordering is near-certain.

**The crossings of Section 5.5 and the material shares here are the same comparator, but neither is the other's prior mass.** A crossing is where the gap reaches 10% with every other parameter at base; in simulation the crossing itself moves, because the compute term is measured against the synthesis expenditure $b = ra$ and both recipes and attempt cost are drawn. Synthesis success is not among the quantities that move it: $S$ is shared, so it cancels from the paired ratio and appears nowhere in $d^{*}$; sweeping it across the three readings' full range leaves both crossings unchanged. The filter case shows what follows. Its crossing is 1,034 core-hours, above the prior's 1,000-core-hour ceiling, so no draw has a verification cost beyond it --- yet 0.9% of draws are material, at verification costs of 439 to 999, median 864, all below the crossing. A low synthesis bill in those draws pulled the crossing down to meet them. The generative case inverts it: 28.0% of draws exceed its 197-core-hour crossing but only 20.7% are material. Either percentage recovered from the other crossing would be wrong, because the threshold is a function of the synthesis bill rather than a constant.

| Level | P(B < A) | P(differ > 10%) | Overlap of marginals |
|:--|--:|--:|--:|
| 1 | 99.4% | 98% | 89% |
| 2 | 99.4% | 1% | 99% |
| 3 | 99.4% | 1% | 99% |

The level-3 row is a comparison of pipelines, not a cost level: it uses a nonzero novelty share drawn from the range in the parameter file. The cost *level* at level 3 is not reported anywhere in this paper, because the one published count is zero of 36 and the implied cost is unbounded (Section 7, item 5).

Most of this follows analytically from Section 5.5, and the simulation is a numerical check rather than a discovery. B's compute term is below A's in all but a small tail of draws, because the two purities are drawn as a bloc from a single source and B's post-filter purity exceeds A's pool prevalence across almost all of that source's range. P(B < A) is therefore near one at every level for the same reason, which is why the figure is identical down the column. The informative number is the second one: the dearer of A and B exceeds the cheaper by more than 10% in only 0.9% of level-2 draws. That is the paired condition itself, not a statement about the compute share --- the two are different events, though they are closely related here because the pipelines differ only through compute.

That 0.9% is sensitive to the DFT-cost prior, which we chose rather than measured: it is log-uniform over a span whose base Section 4.3 calls a convention. A prior weighted towards the top of the span would raise it substantially, and a reader who believes modern production DFT costs hundreds of core-hours per candidate should read the 1,000-core-hour row of Section 5.5 instead of this table.

At level 1 the pipelines separate. At level 2 the ordering survives draw by draw but the magnitude does not matter. The distinction is the familiar one between the sign of an effect and its size, and it is worth stating here only because comparisons of this kind are usually reported as the former: a paper reporting that B beats A in 99.4% of simulations would be stating something true and economically empty.

The marginal distributions overlap heavily at every level, including level 1. Absolute cost is dominated by uncertainty all pipelines share. Only the paired comparison separates them, and only at level 1.

The overlap coefficient depends on the bin count, so we report the dependence rather than one figure. Over 20 to 240 bins the A--B overlap moves from 91% to 87% at level 1 and from 99% to 97% at level 2, spans of 3.3 and 1.6 percentage points, so the qualitative statement --- near-complete overlap at level 2, substantial overlap even at level 1 --- is not a binning artefact over this range, though the second decimal of any single figure is. It does keep falling with much finer bins, reaching 53% at level 1 with as many bins as draws, but that reflects A and B differing in nearly every draw rather than a property of the statistic: identical samples retain overlap one at any bin count. The sweep is in the replication package.

## 5.7 The answer depends on which reading is right

The figures below are Monte Carlo medians within each reading, with every other parameter drawn from its distribution. They are not the deterministic point estimates of Section 5.1, which hold all parameters at base; the two differ because the base values are not the medians of their own distributions and several inputs vary within each reading. We report the gap as an empirical property of the sampler rather than deriving it. The base case of Section 5.1 corresponds to the middle reading.

| Reading | Level 2, pipeline B | 90% interval |
|:--|--:|:--|
| Optimistic | \$2,975 | \$2,000--\$4,379 |
| Middle | \$5,008 | \$2,724--\$10,109 |
| Pessimistic | \$49,917 | \$21,013--\$149,247 |

Between the extremes that is a factor of about 17. The simulated spread is wider than the ratio of the success rates alone (36/57 against 3/58 is 12.2) because recipes per target are drawn jointly with the reading: a pessimistic reading also draws a higher recipe count. Within any one reading, pipeline choice moves the median by at most 1.07 times --- and at base parameters by the 1.03 of Section 5.5. The between-pipeline ratio is $(c_{0i} + ra)/(c_{0j} + ra)$, which cancels the success rate but retains the recipe count and attempt cost, both drawn jointly with the reading. So the ratio is invariant to success alone, not to the choice of reading, and the 1.07 reflects both those remaining inputs and high-DFT-cost draws.

**This factor is not measurement uncertainty.** Two of the three readings interpret the same experiment and disagree about what was made. Harmonising the identification standards and reconciling the denominators would narrow the comparison and is worth doing with existing data. Closing it would need new synthesis campaigns with phase identification both sides accept.

Where a single number is unavoidable we quote the middle reading with the spread beside it, and note that the middle reading is the least established of the three: it is a preprint reporting the smallest campaign.

## 5.8 Where the cost sits, and what that implies for improvement

We report elasticities: the percentage fall in cost per 1% proportional improvement in a lever, scale-free so levers in different units compare directly. Note that these are proportional, not absolute: one percentage point of synthesis success is a 1.5% proportional gain under the optimistic reading and a 19% proportional gain under the pessimistic one, so percentage-point framings are not comparable across readings and we avoid them.

| Lever | A | B | C |
|:-----|--:|--:|--:|
| Synthesis success rate | 1.000 | 1.000 | 1.000 |
| Recipes per target | 0.984 | 0.991 | 0.963 |
| Cost per synthesis attempt | 0.984 | 0.991 | 0.963 |
| Compute price (best compute lever) | 0.016 | 0.009 | 0.037 |

**The synthesis levers should not be ranked against each other.** Success has elasticity exactly one, because it divides both terms. Recipes and cost per attempt have elasticity equal to the *synthesis share* of total cost --- approximately one at base, not exactly --- and the gap between them and unity *is* the compute share rather than a difference in leverage.

The finding is the magnitude gap. At the deterministic base, a 1% proportional improvement in a synthesis term moves level-2 cost 26 times as much as a 1% proportional improvement in compute price for pipeline C, 63 times for A and 105 times for B. Evaluated instead at the Monte Carlo medians the same ratios are 36, 83 and 136. We report the two separately because they are different estimands: the first is a ratio at one parameter vector, the second a ratio of median elasticities across 20,000 draws. This is a ratio of cost shares, not a return: it says where the money is, not what it costs to move it. At the top of the DFT span the same ratio falls to single digits, because compute is then 15 to 41% of the total.

**A correction, because an earlier version of this paper claimed otherwise.** We previously reported that verification accuracy was a computational lever worth about 18% of level-2 cost, with elasticity $w/(1-w)$. That result was an artefact of the accounting error described in Section 3.4. Once synthesis success is unconditional, $w$ cancels out of level-2 cost entirely: compute per candidate sent to synthesis is $c_0 = (1-w)\,c$, so the $(1-w)$ that discounts the level-1 quantity and the one that would scale it back are the same factor. Holding $c_0$, recipes, attempt cost and observed success fixed, changing the diagnostic $w$ does not change the cost of a validated material. We withdraw the claim rather than preserve it by reinstating the double-count that produced it. Whether better verification would raise experimental success, and at what compute cost, is a joint relationship this model does not estimate.

**One lever requires no research expenditure.** Switching from on-demand to spot compute pricing carries a discount of about 62% in the compute-optimised instance prices recorded in the parameter file, with provider, region, instance type and date. It requires no research expenditure, which is the sense in which we call it free; it is not operationally free, since spot capacity is interruptible and retries, checkpointing and delay carry costs we do not model. The discount is also provider- and instance-specific and does not apply uniformly to GPU and CPU pricing. Because it scales the whole compute term, its effect on level-2 cost is 62% of the compute share: 0.6% for pipeline B, 1.0% for A, 2.3% for C. The levers worth up to a hundred times more all require synthesis research whose cost nobody has measured. Ranking returns per dollar would need those costs; we observe only that the free lever is the negligible one.

## 5.9 Break-evens

**The filter has no meaningful break-even batch size.** Loading the potential costs 0.00024 core-hours against a saving of 29.5 core-hours per candidate, so the informative quantity is the per-candidate saving rather than a threshold: any additional fixed cost of $X$ core-hours, such as fine-tuning, repays after $X/29.5$ candidates.

**Synthesis cost at which compute begins to matter.** Taking "matters" as compute reaching 10% of level-2 cost: at base DFT cost, attempt cost would have to fall from \$271 to between \$23 and \$94 depending on pipeline. This threshold does not depend on today's attempt cost, only on the compute term, so it is unchanged by the accounting choices of Section 4.5. At the top of the DFT span compute already matters at today's attempt cost.

**Generative-pool parity.** C matches B at level 1 when filter purity on the generative pool reaches 15.5%, 4.1 times the measured value.

**How strong would a synthesisability effect have to be?** For pipeline choice to double level-2 cost, an MLIP pre-filter would have to raise synthesis success from 44% to 87% --- above the optimistic reading's own figure. This specifies how large an effect the follow-up study would need to detect.

## 5.10 Where the evidence is weakest

A one-at-a-time sweep is dominated by a single parameter at each level: DFT cost at level 1 and synthesis success at level 2, which account for 99.8% and 98.6% of the summed squared one-at-a-time ranges respectively. That statistic is not a variance decomposition and should not be read as one; it reflects the width of each parameter's assumed range as much as the model's response to it. **The tornado maps where the evidence is weakest rather than where the leverage is.** The two quantities most in need of better measurement are DFT cost on modern hardware and synthesis success from independent campaigns.

# 6. Discussion

## 6.1 For research groups

At base DFT cost, the choice between computational pipelines is a choice about a line item worth 1 to 4% of the total; at the top of our DFT span the line item is 15 to 41%, and the argument below weakens accordingly. A group that intends to take candidates into the laboratory should optimise the laboratory. A group that stops at computational screening faces a real and substantial choice --- the pipelines differ by a factor of four at that stage --- but should describe that choice as affecting a small share of the cost of a validated material rather than as not affecting it. The effect is below a practical threshold under our base calibration; it is not zero, and it grows with DFT cost.

Our results also suggest two specific practices. Report an MLIP's convergence rate alongside its accuracy, because a potential that fails to converge on most structures from a cold start has an effective cost unrelated to its per-step speed. And check the thread scaling of a screening configuration before committing a budget to it: on our platform, which is virtualised and should not be generalised from, running single-threaded across many structures rather than multi-threaded on one was the difference between one core-hour and eighty. The general point is that core-hours are billed on allocated cores, so a configuration that scales poorly is charged in full for the cores it wastes.

## 6.2 For funders

Synthesis is where the money is, by between one and two orders of magnitude at base DFT cost and by a single-digit factor even at the top of our DFT span. The ordering is robust across every parameter configuration we tested; the magnitude is not, and we do not claim to know what a dollar spent on synthesis research buys.

But the more valuable expenditure may be one the model cannot price. The factor of about 17 between readings of the synthesis evidence exceeds every methodological difference in the paper combined. Funding independent synthesis campaigns with phase identification that both sides of the current dispute would accept would do more to establish what materials discovery costs than any improvement to the discovery methods themselves. At present the field does not know this number to within an order of magnitude.

This is a specific instance of the general problem in @bloom2020ideas and @scannell2012eroom: when the cost per research output is unknown, there is no denominator against which to judge whether a new tool has improved productivity. Materials discovery currently lacks that denominator, and the missing measurement is experimental, not computational.

## 6.3 For autonomous laboratory programmes

Within our search scope we did not find a published capital or operating cost for an autonomous *bulk solid-state* synthesis platform. The only figures we located are for a different chemistry. @pilon2026 report that high-end self-driving laboratories "often exceed US\$100,000" excluding analytical components, that their predecessor flow-chemistry platform cost approximately US\$50,000 in essential components, and that substituting a human-in-the-loop sampling unit brings their own platform to approximately US\$5,000. That is the right disclosure, and it is the exception. For solid-state platforms the only capital figure we found is a press statement, which we do not treat as a citable number.

@lo2024frugal review low-cost self-driving laboratories and the "frugal twin" approach, and tabulate estimated dollar costs for twenty-five platforms. That is a cost literature, and it narrows our claim considerably: what we could not find is a capital or operating cost for an autonomous *bulk solid-state* synthesis platform of the kind that produces our success rates, not an absence of platform costing in general. The absence of any published capital figure for a solid-state platform is a striking gap, because these platforms are justified on economic grounds --- they make materials faster and therefore cheaper --- and for the solid-state case the cost side of that argument is not in the literature. It also matters for our model specifically: a capital figure is what would let the synthesis term be decomposed into labour, consumables and amortised equipment, which is currently the largest unmodelled structure in the paper.

Our model suggests the relevant metric is cost per validated material rather than samples per day, since throughput claims and cost claims diverge sharply. Reported peak throughput and realised output are different quantities --- one platform's software paper reports around 3,500 samples over 1.5 years [@fei2024alabos] against a quoted daily capacity --- and converting between them requires a utilisation figure: realised samples divided by daily capacity times the number of eligible operating days. That is not the same as hardware duty cycle, and the two are often conflated. Utilisation is what converts a capacity figure into a cost per sample, and we did not find it reported for the platforms we looked at. A programme reporting cost per validated material, with its capital amortisation stated, would be able to make its economic case directly. @adesiji2026benchmarking propose benchmarking practice for self-driving laboratories; cost per validated output belongs in such a benchmark and is currently absent from it.

## 6.4 For benchmark design

Our Section 5.4 result is addressed to a different literature than the rest of the paper. Measured enrichment on two realistically constructed candidate pools is roughly half the acceleration factor the benchmark reports, and lower still on the generative pool. We do not attribute this to the benchmark: the evaluations differ in reference hull, candidate distribution and threshold, and the difference may be definitional rather than a weakness of the models --- the benchmark's authors themselves note that their reference-set choice could be read as overestimating performance [@riebesell2025] --- and we specify the experiment that would settle it. Until it is settled, practitioners using benchmark classification rates to plan a DFT budget should measure enrichment on their own pool rather than assuming the benchmark's figure transfers. We do not predict a general factor-of-two overestimate; we report that our own estimate halved when we substituted direct measurements.

## 6.5 For investors and the public account of AI in science

Claims that AI accelerates materials discovery by one or two orders of magnitude are, on our accounting, claims about a stage representing 1 to 4% of the cost of producing a validated material at base DFT cost, and no more than about half of it anywhere in our DFT span. They may well be true as stated. They do not imply a comparable reduction in the cost of discovery, and the gap between the two statements is where most of the money is.

The pattern may resemble what @kusumegi2025 observe in publishing, where adoption of AI raises output substantially while the relationship between a work's complexity and its quality inverts --- though that finding is disputed (Section 2.2), and this paper, AI-assisted by its own disclosure, is not well placed to press the analogy. The narrower point stands without it: more candidate materials is not more validated materials, and in a funnel whose terminal stage is unchanged, it is not obvious that it is even more discovery.

# 7. Limitations

1. **Primary threat to validity: synthesis success is assumed independent of pipeline.** No source we found measures this. The expected direction would widen the 1.03 spread, but we do not claim it as a bound. The follow-up study is to attempt matched sets of filtered and unfiltered DFT-stable candidates and compare success rates.
2. **Filter recall is not measured on these pools.** We import it from the benchmark, which is an assumption, not a measurement. Measured purity and imported recall describe different populations, so both can be correct and still be mismatched for our use.
3. **The generative-pool result's magnitude depends on which end of a printed range we take.** The source gives 3.8% to 8.8% for diffusion-model candidates after filtering; we take 3.8% for the configuration we model, which is our reading rather than the source's assignment. Across the range the DFT-dominated ratio spans roughly 1.7 to 4.0 rather than the 2.2 to 6.7 quoted in earlier drafts; the direction does not change.
4. **Overhead treatment is an accounting choice** moving level 2 by 57% between the extreme variants of Section 4.5, while barely moving the pipeline spread. It also moves the materiality thresholds of Section 5.5 approximately in proportion to the attempt cost, a near-proportionality that holds under these parameters because generation and filtering cost almost nothing beside verification, and that Section 5.5 shows is not an identity. The rate itself is an average across NIH-funded institutions, not a rate any one laboratory faces.
5. **No level-3 cost is reported.** The novelty share for the reference campaign is disputed, and the count we would have to use is zero, at which the implied cost is unbounded. Level 3 appears in the pipeline comparison of Section 5.6, which uses a nonzero novelty share from the parameter file, but no dollar figure for it appears in this paper.
6. **DFT cost spans more than two orders of magnitude.** Results are reported across the span.
7. **The cross-functional transition rate is a proxy, and it now affects only level 1.** $w$ is the directed fraction of candidates called stable at one level of theory and unstable at a higher one. It is not an experimental error rate, a material above the hull is not thereby impossible to synthesise, and functional disagreement also runs the other way, which we do not credit. Since level-2 and level-3 costs now use unconditional success rates, $w$ no longer enters them; it defines the level-1 output and is otherwise reported as a diagnostic.
8. **Our DFT measurements are not commensurate with the hull the model uses.** The first-hand timings are Quantum ESPRESSO with GBRV ultrasoft pseudopotentials; the convex hull that defines level 1 is the Materials Project's, built with a different code, pseudopotential family and correction scheme. A total energy from our calculation cannot be placed on that hull without a mixing scheme we do not apply. We therefore retain the timings as a screening benchmark and treat the low end of the DFT span as illustrative. **We do not establish a bound on verification cost in either direction**: energy incompatibility and runtime are separate questions, and we have not measured an MP-compatible calculation on comparable hardware. The consequence is handled by reporting thresholds (Section 5.5) rather than a single base-case claim, and it remains the most consequential unresolved issue in the paper.
9. **Three parameters are graded `missing`:** precursor mass per attempt for the autonomous-laboratory case; the reference-phase count of Section 3.6; and the high value of the tuition term, which we could not locate in the cited stipend notice and which should be treated as an unsourced upper bound.
10. **Monte Carlo choices shape the distribution.** The DFT-cost prior is chosen, not measured, and Section 5.6's "1% of draws" figure is sensitive to it. The three readings receive equal weight, an assumption with no basis; named scenarios are reported so readers can apply their own. The level-2 95th percentile is a statement about whose re-analysis to believe: \$94,204 under equal weights, falling to \$8,507 if the pessimistic reading is given zero weight.
11. **The enrichment gap has an unresolved competing explanation:** the two studies judge stability against different reference sets.
12. **Our hardware is unusual.** An ARM64 laptop under virtualisation produced two platform artefacts that we document and correct for; the DFT timings should not be generalised to server hardware.
13. **"Validated" does not mean the same thing in all three readings.** Level 2 is defined once, but the readings differ on the evidentiary standard for identifying the target phase: @leeman2024 regard only one of three claimed successes as convincingly demonstrated. Part of the factor of 17 is therefore a difference in how strictly an output is counted, not a difference in what it costs to produce one. We do not decompose the factor into these two components, and a reader should not read all of it as a cost spread.
14. **Published recharge rates may omit subsidised components** [@strom2020]. We treat this as directional for the XRD and furnace line items only, not as a certification that the whole attempt cost is conservative.
15. **We price a manual campaign using an autonomous campaign's recipe multiplicity and success rate.** The labour term is a graduate trainee's time at a trainee's throughput; the six-recipes-per-target figure and the success fractions come from a robotic platform running continuously, whose cost structure is commissioning, supervision and amortised capital rather than bench time. We borrow only the per-target recipe count and the success fraction, and we have no manual-campaign equivalent for either.
16. **Cost per attempt may not be pipeline-independent after all.** Item 1 above concerns the success rate; the same objection reaches the attempt cost. @cheetham2024 report that a substantial share of one large generative stable set --- a different set from the one we model --- contains radioactive elements. Whether our generative pool shares that composition skew is untested. If it does, the cost channel is handling and disposal, which we do not model at all, rather than precursor mass, which is only \$2.64 of a \$271 attempt.

# 8. The replication package

The complete model, every parameter with its source and evidence grade, the first-hand benchmark data, the analysis code and the test suite are *to be* released as a replication package. At the time of writing the repository is not yet public and no archival DOI has been minted, so nothing in this section should be read as a claim that the results have been independently regenerated. A passing test that the text matches the model confirms internal consistency, not the correctness of the model's assumptions or of our reading of the sources. Every figure in this paper is generated from the parameter file and the benchmark data, and the test suite fails if a figure in the text drifts from the model.

The model is a pure function from parameters to results, so a reader who disagrees with a parameter can substitute their own and rerun. We expect disagreement about several --- the overhead treatment, the weighting of the three readings, the DFT cost span, the choice of optimistic success count --- and the package is structured so that each takes one edit.

# 9. Conclusion

The field's standard claim that synthesis is the bottleneck is a claim about rate, and we do not test it: we price nothing in time. What we can now say is that synthesis is also where the money is, and by how much: at the deterministic base a proportional improvement in a synthesis term is worth between 26 and 105 times the same proportional improvement in compute price, and the single compute improvement requiring no research expenditure moves the total by under 3%.

The consequence, on the assumption that the synthesis term does not depend on how a candidate was found, is that the two decisions bundled inside "pipeline choice" separate. Using an MLIP pre-filter changes the cost of a validated material by under 10% throughout the tested range of verification cost, under our default accounting. Sourcing candidates generatively is immaterial only while verification stays below roughly 200 core-hours per candidate, and we cannot say with confidence that it does. Both thresholds scale with the synthesis bill, so both are accounting-dependent as well as calibration-dependent. The synthesis-independence assumption is imposed rather than tested, and is the primary threat to both statements.  An MLIP pre-filter cuts computational cost by 39% and a generative candidate pool costs four times the filtered ion-exchange one at the DFT gate, yet at base DFT cost all three deliver a validated material within 3% of the same price.

What does govern the price is a number the field does not currently know. Three groups read the synthesis evidence three ways, producing cost estimates spanning a factor of about 17, and two of those readings interpret the same experiment. Narrowing that gap is partly an exercise in harmonising definitions across the existing campaigns; closing it needs new synthesis data, not better models. Until it closes, statements about what AI-driven materials discovery costs are statements about which re-analysis one believes.

# Disclosures

**AI assistance.** This paper was written with substantial assistance from a large language model. The author directed the research, ran and debugged all computational work, verified the results, and takes full responsibility for the content. Drafting, literature search, and methodological review were AI-assisted.

**Conflict of interest.** The author is the founder of a company working in AI-driven materials science. The computational pipeline used for the first-hand benchmarks in Section 4.2 derives from that company's codebase, though the released replication package depends on no proprietary code.

**Data and code availability.** [Repository URL and archived DOI to be inserted on release.]

