---
title: "What Does It Cost to Validate a Predicted Inorganic Material?"
subtitle: "A transparent end-to-end pipeline model, and what its inputs cannot yet support"
author: "Karthikeya"
date: "Working paper --- 11 October 2026"
abstract: |
  Machine-learned potentials and generative models have sharply reduced the cost of parts of the computational materials pipeline, and the field widely asserts that synthesis is now the bottleneck. Within the literature we searched, we did not find that claim priced in dollars. We build a transparent end-to-end model from candidate generation through machine-learned screening, density functional theory verification and laboratory synthesis, reporting modelled cost per PBE-stable prediction surviving an r$^2$SCAN workflow and per experimentally validated target. A third level, per material new to science, we define but cannot price: the only published novelty count for our reference campaign is zero, at which the implied cost is unbounded. A synthesis attempt is modelled at \$190 to \$300 depending on the overhead convention, assembled from eleven US fee schedules with assumed throughput and allocation rules --- a construction, not a cost observed in any laboratory.

  If synthesis success, recipe count and attempt cost are identical across pipelines, a machine-learned prefilter reduces modelled cost per robust prediction by 39%. Once the shared synthesis stage is included the two decisions bundled inside "pipeline choice" separate: at base verification cost the prefilter moves cost per validated material by 3.6% and sourcing candidates generatively by 16.9%, and both cross a 10% gap inside the verification-cost range we test. The conditional matters as much as the result, since no source measures pipeline-specific synthesis behaviour at all.

  The dominant source of variation among the modelled scenarios is the synthesis evidence and its interpretation. Three readings of essentially two campaigns give scenario medians from roughly \$1,200 to \$34,000, a factor of 30. The reading counting the most successes is not the cheapest: it reached a success rate 2.2 times higher using 6.2 recipes per target against another campaign's one, so recipe multiplicity, which synthesis papers often omit, moves cost more than the success rate does. Published evidence is currently insufficient to identify a general cost per experimentally validated inorganic material; what the framework supplies is which measurements would change the answer.
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

**Principal contributions.**

1. **A transparent end-to-end funnel accounting framework** from candidate generation to experimentally validated target, with every parameter documented, graded for evidence quality, and released with the code. The framework is the contribution; the numbers it currently produces are conditional on inputs we grade openly, six of which are modelling conventions with no source and one of which has no source at all.

2. **An illustrative synthesis-attempt cost build-up and scenario analysis.** We price an attempt at \$190 to \$300 depending on the overhead convention, from eleven US institutional fee schedules combined with assumed throughput, a compensation proxy and allocation rules, each graded and individually sourced. The fee schedules are measured inputs; the total is a construction on top of them. It determines the synthesis component of every downstream figure, and it is the one output a reader can lift and reuse independently of any disagreement about readings, pipelines or benchmarks.

3. **Evidence that disagreement about experimental validation dominates current cost estimates.** Cost per validated material spans roughly \$1,200 to \$34,000 across three published readings of essentially two campaigns. The readings differ in phase-identification standard, denominator and recipe multiplicity, so this compares non-equivalent scenarios rather than bounding one quantity — which is itself the finding, because it means no amount of computational improvement resolves it. The reading that counts the most successes is not the cheapest, because it attempted each target six times rather than once.

**Supplementary contributions.** A first-hand MLIP and plane-wave DFT timing benchmark, run because single-threaded core-seconds per ionic step per atom and the cold-start convergence rate do not appear to be published per model, and reported as a protocol demonstration on seven structures rather than a representative study. A verification-cost threshold analysis, which replaces reliance on any single assumed DFT cost by reporting where conclusions change. A break-even analysis for pipeline-specific synthesis behaviour, which converts the model's central untested assumption into stated tolerances. And an uncontrolled cross-setting observation about filter enrichment, reported in the supplement because its confounds are not separable.

# 2. Related work

Three literatures bear on this question and none of them answers it.

## 2.1 Resource accounting of computational discovery

The closest work in structure is @walker2026carbon, which reproduces a DFT workflow for estimating the maximum efficiency of photovoltaic materials, progressively substitutes machine-learned surrogates, and estimates the CO$_2$ emissions of each configuration. The architecture is the same as ours --- a staged pipeline with a substitutable component, costed end to end --- but the unit is carbon rather than money, and the scope is compute: no material is synthesised and synthesis does not enter the accounting. Its conclusion is that machine learning is not yet a complete replacement for DFT, that hybrid workflows therefore sit on an accuracy--emissions frontier with a learned scissor correction as a strong intermediate option, and that carbon cost should be reported alongside predictive performance. Ours concerns what happens when the laboratory is included, which turns out to dominate everything upstream. The two papers agree on the methodological point that resource cost belongs next to accuracy; they differ on which resource binds.

Matbench Discovery frames MLIPs explicitly as triage tools for allocating a DFT budget, and reports a discovery acceleration factor for each model [@riebesell2025]. That is a cost-adjacent framing without a cost: it counts calculations saved rather than money, and stops at the DFT gate. Our Supplement S1 records a cross-setting discrepancy in its metrics. @miller2024flowmm reports a cost per stable material in integration steps, which is a per-method computational cost rather than a pipeline cost.

@szymanski2025baselines compare generative and substitution-based candidate generation on stability, novelty and generation time, and establish that a simple ion-exchange baseline outperforms several generative models. Their comparison is over 500 *novel* materials per method: "For each of these six approaches, 500 materials were considered", with each method run until 500 novel materials were obtained. That is a selection on novelty, not a fixed generation budget, and Section 3.3 notes what it implies for our chaining step. Their measurements are among our most important inputs, and our Section 5.3 restates part of their conclusion in dollars. We emphasise that this is a restatement, not an independent reproduction.

**Gap:** none of these prices the full funnel, and none includes synthesis.

## 2.2 The economics of AI-aided discovery

@agrawal2024 model innovation as sequential search over a combinatorial design space in which a predictive model prioritises costly tests. They show that improvements in prediction fidelity raise the probability of successful innovation and shorten search, and --- centrally for us --- that the gains from better prediction may not be realised without corresponding investment in testing capacity.

@agrawal2026aiinscience sharpen this into a stage-decomposed form: scientific productivity $\omega$ in a knowledge-production function is the product of stage-specific productivity terms, $\omega = \alpha\cdot\beta\cdot\gamma\cdot\delta$, with testing among the stages, and the returns to AI differ by stage. The decomposition is of productivity, not of pass probabilities, so it is an analogue of our result rather than a statement of it. Their model is analytical and uncalibrated; it specifies the conditions under which prediction and testing are complements without saying, for any real discovery problem, how far apart the two stages actually are. Our contribution is to supply that calibration for inorganic materials: at the deterministic baseline, making prediction cheaper has a small modelled effect on the total, because the gap between the compute and synthesis shares is one to two orders of magnitude.

We note a limit on what this calibration can say. The theory is about prediction *fidelity*, and our model varies compute *price*. Better verification might raise experimental success, or lower it by rejecting makeable candidates, and it would certainly cost more compute; we do not estimate that joint relationship, and nothing here should be read as doing so. Cross-functional disagreement between levels of theory is reported separately and is not treated as an experimental failure probability.

Evidence on what AI does to realised scientific output is thinner than the theory, and what exists concerns publication rather than validated laboratory output [@kusumegi2025; @renault2026comment]. We are aware of no credible direct estimate of AI's productivity effect inside a materials laboratory, which is itself part of our motivation.

We borrow one convention from pharmaceutical cost estimation and nothing else: @dimasi2016 attribute the cost of abandoned candidates to the survivors, and we do the same. The figures are not comparable in any other respect, and we make no claim that materials discovery costs resemble drug-development costs: their figure is capitalised over a decade-long development cycle and carries allocated company-level fixed cost, whereas ours is uncapitalised and charges no *explicit* equipment or capital. Recharge fees and institutional overhead plausibly embed some depreciation and facility cost, so the distinction is between absent explicit capital and implicit capital of unknown size, not between some capital and none. For a 17-day campaign the omission of capitalisation is defensible; for a facility it would not be, and Section 6.3 treats the missing capital term as the largest unmodelled structure in the paper. @buchner2018tea matches cost-estimation method to technology readiness level and specifies which profitability measures are legitimate at low TRL; it licenses the static, order-of-magnitude approach we take and explains why we do not compute a net present value. See also @kobos2020tea.

## 2.3 The synthesis evidence and its contestation

The empirical base for synthesis success is thin and disputed, and this turns out to be the central fact of the paper rather than a caveat on it.

The A-Lab campaign reported realising a set of target compounds from computational predictions over 17 days of autonomous operation, with two further targets formed after products were manually reground and reheated to higher temperatures [@szymanski2023alab]. On the corrected count it realised 36 of 57 targets. Following publication, concerns were raised about structural identification and novelty. An Author Correction re-analysed the reported successes, found four inconclusive from X-ray diffraction alone, removed one compound that had been included in the training data, and clarified that the authors' "intention was to indicate that the materials were new to the prediction platform, not necessarily new to science" [@szymanski2026correction]. @leeman2024 published a re-analysis of the same campaign reaching a substantially more pessimistic count. They examine 43 of the reported products in detail --- the 36 classed as successes and seven partial successes --- and report significant issues with 42 of them. Three they regard as synthesised as predicted, of which one, CaFe$_2$(PO$_4$)$_2$O, they call convincingly demonstrated on the deposited diffraction data and the other two too poorly fitted to judge; all three had been reported previously, so they find none of the compounds new. Their own headline rate is stated against the full target set: "the success rate would be 3/58, or 5%". The two denominators do different work and should not be interchanged --- 43 is the set they inspected, 58 the targets attempted --- and we use 3/58 because it is the rate they publish. @prein2025 report a separate, smaller campaign.

Separately, large-scale generative predictions have been questioned on novelty grounds: a critique of one 380,000-structure stable set reports that the structure of every one of ten randomly sampled entries could be matched to an entry already in the ICSD, usually at higher symmetry, and counts 18,138 compounds of Pm, Ac or Pa and a further 23,529 containing Tc, Np or Pu in that set [@cheetham2024]. The source gives those counts rather than a percentage.

**Gap, and our position in it.** We do not adjudicate this dispute. We take the three readings as three coherent worldviews, propagate each through the cost model, and report what each implies. The resulting factor of about 30 is, we argue, the most policy-relevant number in the paper: it says that the field does not currently know what a validated material costs to within an order of magnitude, and that the disagreement is about what was synthesised rather than about anything a cheaper or faster computational stage would settle. Resolving it needs agreed phase-identification standards, reconciled denominators and reported experiment counts, and in the end new synthesis campaigns --- not better models.

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

**What the filter lets through.** With measured post-filter purity $P$, pool stability $\pi$ and recall $R$, the pass fraction is $\pi R / P$ and the DFT-stable share of what passes is $P$. The alternative formulation, from a benchmark confusion matrix, gives a pass fraction of $\pi R + (1-\pi)\,\mathrm{FPR}$. Supplement S1 shows these disagree substantially; we take measured purity as primary.

**Chaining.** To obtain $N$ candidates absent from the reference database, a method must generate $N$ divided by its novel share. Each stage takes what the previous one released.

One caution on this step. The stability rates we take from @szymanski2025baselines are measured over samples of 500 *novel* materials per method, each method having been run until that many novel materials were obtained. Those rates are therefore already conditioned on novelty. Dividing by the novel share again would charge the novelty filter twice. We believe the model applies the division only to the generation count and not to the stability rates, but this is exactly the kind of double-count that is easy to introduce, and it is on the list of checks for the released package.

## 3.4 Wrong verdicts

A share $w$ of DFT "stable" verdicts do not survive scrutiny. Our proxy for it is the *cross-functional stable-to-unstable transition rate*: the directed fraction of candidates called stable at one level of theory that are called unstable at a higher one. We use the shorthand "wrong verdict" for readability, but the quantity is a disagreement between two calculations, not experimental ground truth, and a material above the hull is not thereby impossible to synthesise [@kingsbury2022r2scan; @an2026; @merchant2023gnome].

**Where the three values come from, since this parameter is easy to assert and hard to source.** The base and low values are published: @merchant2023gnome report that 84% of discovered binaries and ternaries present negative phase-separation energies and that 86.8% of tested quaternaries remain stable on the r2SCAN hull, giving 16% and 13.2%. Those are two different tests rather than one metric split by composition arity, and we use the pair as a range rather than averaging them. The high value, 34.3%, is weaker and we grade it accordingly: @an2026 report that of 166 *dynamically stable* candidates, 109 sit below 1 meV/atom on the SCAN hull, and the complement is our own subtraction, which that paper does not present as a flip rate. It is also not a flip rate over all PBE-stable candidates, because the higher functional was not run on those eliminated earlier, and its population is pre-screened on dynamical stability while the other two endpoints are not. We found no source reporting the transition rate by chemistry, only by number of elements, so the model does not vary $w$ by chemical system and Section 5.10 does not claim to have tested that dependence. Because $w$ enters only level 1 (Section 3.4 below) and cancels from level 2, the weakness of its upper endpoint does not propagate to the paper's headline figures. The underlying error scale is well documented: GGA formation-energy errors against experiment are of order 0.1 eV/atom [@kirklin2015oqmd]; surrogate models inherit and compound them [@bartel2020]; corrections reduce but do not eliminate them [@wang2021corrections]; and about half of ICSD-reported compounds sit above the computed hull at all [@sun2016metastability].

Every candidate sent to synthesis incurs the allocated cost, including the targets that are never made. Observed unconditional campaign success determines experimental-output costing; cross-functional transitions define a separate computational endpoint and are not treated as an experimental failure probability. We do not claim that a candidate whose stability flips under a higher level of theory cannot be synthesised --- roughly half of ICSD-reported compounds sit above the computed hull [@sun2016metastability] --- only that it fails the computational test level 1 defines.

Synthesis success is **not** conditioned on the verdict being correct. Each campaign's observed success rate already embeds whatever computational failure that campaign experienced, so dividing by $(1-w)$ as well would charge the same failures twice. $w$ is retained for the level-1 output, where the question is what a cross-functionally robust prediction costs, and is reported separately as a diagnostic.

Conditioning one reading and not the others, and then dividing all three by $(1-w)$, mixes two definitions of success and double-charges the failures the campaign already counted; and removing it lowered cost per validated material by about 16% before the accounting change of Section 4.6 is applied.

### Which optimistic value, and why 36 of 57

The A-Lab campaign supports several success counts. Because the model now takes unconditional rates, the choice is narrower than it was, but it still moves the optimistic branch.

| Count | Value | What it includes |
|:--|:--|:---------------|
| 36 / 57 | 63.2% | The corrected figure, unconditional. **Used.** Includes the three targets that failed for computational reasons, as an unconditional rate should. |
| 36 / 54 | 66.7% | Excludes the three computational failures, so it is a conditional rate and overstates unconditional success unless a separate failure multiplier is applied. |

We take **36 of 57, 63.2%**, unconditional. Three things about that ratio are worth stating, because the published record is in two versions. The 2023 article reports 41 realised of 58 targets. The corrected article reports 36 of 57, and those are the numbers we use. The correction *notice* publishes neither total: it states that the platform reached the correct conclusion in 36 of its 40 reported successes, that four compounds are inconclusive from diffraction alone, and that one further compound was removed as training data, from which 41 − 1 − 4 = 36 and 58 − 1 = 57 both follow. So 57 is the original target count less the removed compound, not a number the 2023 article prints. The 36/54 rate excludes computationally attributed failures and therefore does not estimate unconditional campaign success; it would be the right quantity only alongside a separate computational-failure multiplier, which the model no longer applies.

We considered and discarded counts that add the two targets realised only after an operator reground and reheated the products. No published document states such a total, so any version of it is our own composite; the intervention is outside the autonomous protocol being costed, and the model charges none of the extra labour it took. Reporting a count the sources do not print, in a section whose purpose is to pin the count to a document, would work against the rest of the paper.

Two cautions follow. The ratio should be cited to the corrected article rather than to the correction notice, which publishes no total. And the target-level crosswalk that would confirm the four inconclusive targets are not subtracted twice is still outstanding. We therefore treat 36/57 as a proposed baseline rather than a settled count, and a reader who reconstructs it differently from the same two documents is not contradicting a published figure.

## 3.5 Synthesis cost

We did not locate a published dollar cost per solid-state synthesis attempt, or a capital or operating cost for an autonomous bulk solid-state synthesis laboratory, within our search scope (Section 6.3). We state these as search outcomes rather than as established absences. We build the attempt cost bottom-up:

$$\text{direct} = \text{XRD} + \text{furnace} + \text{labour} + \text{crucible/firings} + \text{precursor mass} \times \text{price} + \text{other consumables}$$
$$\text{per attempt} = \text{direct} + \text{tuition} + r \times (\text{direct} + \text{tuition})$$
$$\text{per target} = \text{recipes per target} \times \text{per attempt}$$

Labour pairs a graduate trainee's stipend and institutional allowance [@nih2026stipends] with a trainee throughput of 10 to 20 compositions per week, so person and throughput match. Two caveats: the NRSA training allowance is a funding instrument, not an ordinary wage fringe rate, and the throughput range is an assumption, graded as such, not a published measurement. The composition unit here is the attempt, not the target. Crucible cost is divided by firings survived.

**Recipes per target is campaign-reported wherever a campaign reports it.** @prein2025 attempted each of 24 targets once, so the middle reading --- which the base case follows --- charges one recipe per target. The A-Lab campaign as corrected ran 353 experiments across 57 targets, a mean of 6.193 [@szymanski2023alab; @szymanski2026correction], which the optimistic reading charges and which sets the high end of the parameter's range; the 2023 article as originally printed gives 355 across 58, a mean of 6.121, which is the pair the pessimistic reading inherits because that is the version it re-analyses. Both experiment counts and both target counts changed at the correction, so a figure built from one document's numerator and the other's denominator is a splice, and we keep each reading inside one document. Where a reading supplies a success rate but no experiment count, we fall back to a budget model: each recipe succeeds independently with probability $q$, a target receives at most $B$ recipes, so per-target success is $1 - (1-q)^{B}$ and expected recipes is that success divided by $q$. Calibrating $q$ and $B$ on A-Lab's two reported figures gives $q = 0.102$ and $B = 9.28$, and applying them to @leeman2024's success rate gives 9.06 recipes per target. A reported mean is an average allocation, not a claim that every target underwent that many attempts: failed targets consume more of the budget and successes fewer, which is why Section 4.4 draws recipes jointly with the success rate under the fallback.

**Phase identification is charged at one tier, and it should not be.** The attempt cost includes a powder-diffraction service fee, and the model charges the same tier --- the internal service rate of \$80.00 per sample --- under all three readings. That is internally inconsistent, because what the three readings disagree about *is* the identification standard: a determination strict enough to satisfy @leeman2024 involves refinement and expert judgement, not a routine service slot, while the counts the optimistic reading rests on came from automated analysis. The model therefore pairs a strict reading's low success count with a lenient reading's identification bill. We found no published fee for a refinement-grade determination, so rather than invent one we bound the effect with the three tiers the fee schedules do supply --- \$5.00 self-use, \$80.00 internal service, \$150 external service. Changing the tier for all three readings together moves the level by $-37$% to $+35$% and leaves the spread between readings untouched, because the charge is shared. Tying each reading to its own tier is what moves the spread: the factor between the dearest and cheapest readings is 33 at a uniform tier, 71 if the strictest reading pays the dearest tier and the most lenient the cheapest, and 15 under the reverse assignment. Which assignment is right is an assumption; that the uniform tier understates the spread under the plausible assignment is not. Section 5.7 reports the uniform-tier figures and this bound beside them.

Instrument time is otherwise priced at published institutional recharge rates, taken from the published fee schedules of eleven US university facilities. The parameter file lists each with its facility, date, URL, internal and external rate, unit and the time or quantity we charge. The eleven are not eleven independent measurements of an attempt cost: they are a price range for two line items, from which we take a central value. This may understate the true resource cost: @strom2020 report that user-fee income alone does not fully support most shared instrumentation facilities, which implies that published rates can omit subsidised components. We apply that directionally to the XRD and furnace line items and do not claim it as a bound on the attempt cost as a whole, which also contains terms with no such subsidy argument. @sorzano2026 model the full cost of laboratory equipment and the trade-offs between shared and dedicated provision, which is the quantity a recharge rate approximates. To the extent it holds, the direction is favourable to our conclusion, since it makes those two line items conservative and synthesis already dominates.

At base an attempt costs **\$271**: XRD \$80.00, indirect cost \$80.05, labour \$40.47, furnace \$37.90, tuition \$20.51, other consumables \$5.58, crucibles \$3.49 and precursors \$2.64. On a direct-cost-only basis it is \$191. The parameter file carries the unrounded components and the time, mass and throughput allocation behind each quoted rate. The indirect-cost rate $r$ is applied to total direct costs including service-centre fees and tuition, which is the base its source defines it over; at $r = 0.42$ that base is \$190.59. An MTDC-like variant excluding fees and tuition is retained as a scenario in Section 4.6.

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

Grading explicitly matters because the paper's central result is a claim about evidence quality as much as about cost. Of the 88 parameters, 46 are `published`, 14 `first_hand`, 13 `derived`, eight `proxy`, five `assumption`, one `figure_read` and one `missing`. The single `missing` parameter is the reference-phase count of Section 3.6, held at zero. The grades that carry the most weight in the result are not the weakest ones: `dft.cost_per_candidate` is `published` at both endpoints and still spans two and a half orders of magnitude, so a grade describes provenance and not precision. Section 7 names the parameters whose grade or range we think a reader should check first.

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

Because the low endpoint is illustrative, we do not treat the span's geometric midpoint as a measured base case. Section 5.4 therefore reports DFT cost as a direct sensitivity, with the cost at which each pipeline decision reaches a given materiality threshold, rather than resting the conclusion on one base value.

## 4.4 The contested parameter

| Reading | Success | Recipes per target | Standing |
|:--|:--|:--|:-------------|
| Optimistic | 36 of 57 (63.2%) | 6.19, reported | As the corrected article prints it; the 2023 article printed 41 of 58; unconditional [@szymanski2023alab; @szymanski2026correction] |
| Middle | 7 of 24 (29.2%) | 1, reported | Preprint, 24 targets each attempted once [@prein2025] |
| Pessimistic | 3 of 58 (5.2%) | 9.06, derived | Peer-reviewed re-analysis of the first campaign; only one of the three regarded as convincing [@leeman2024] |

The first and third read the *same experiment* and disagree about what was made. The second is a separate, smaller campaign.

All three are unconditional rates on their own denominators: 57 is A-Lab's corrected target count, 24 is Prein's, and @leeman2024 count against 58, the target count as originally printed. We do not force them onto a common denominator, because part of the disagreement is about what counts as a target.

**Each reading now carries its own recipe multiplicity**, which matters more than we first expected. A-Lab reports 353 experiments across 57 targets, a mean of 6.19; @prein2025 attempted each of their 24 targets once. Only the pessimistic reading needs a derived multiplicity, because @leeman2024 re-count the outcomes of the A-Lab campaign without restating its experiment count; we obtain 9.06 from the budget model of Section 3.5 at their success rate. Pairing one campaign's success rate with another's recipe count, which an earlier version of this model did, understates cost under the optimistic reading and overstates it under the middle one.

Synthesis success, novelty and the cross-functional disagreement rate all come from these same re-analyses, so they are not independent. The Monte Carlo draws one reading per sample and takes all three from it; independent sampling would generate combinations corresponding to no coherent reading of the evidence. Recipes per target are drawn jointly too, since failed targets consume more of the recipe budget.

## 4.5 Rounding and precision

Because several figures in Section 5 are solved rather than measured, they can be printed to more digits than they deserve, and the paper would mislead if it printed them without saying which digits are meaningful. The policy, applied throughout:

- **Dollar figures per output are rounded to two significant figures** (\$1,000, not \$1,019). None of the inputs supports more: the attempt cost rests on an assumed throughput, and the verification cost spans two and a half orders of magnitude. Unrounded values are in the replication package.
- **Shares of cost and relative gaps are printed to one decimal place** (16.9%, 3.6%). The decimal distinguishes quantities that are compared against a 10% convention, and nothing turns on it: 16.9% and 17% carry the same conclusion.
- **Break-even boundaries are printed to the precision needed to reproduce the solve** (1.169, 3.85%), because a reader checking the arithmetic against the equation needs the digits the equation consumed. They are not claims about the world to that precision; each inherits the full uncertainty of the synthesis bill it is measured against.
- **Crossings in core-hours are rounded to two significant figures** (31, 170, 410), and the distribution around each is reported alongside, since the point estimate is the least informative thing about it.
- **Threshold coefficients are printed rounded and reproduced unrounded** in the package, because recomputing the crossing from the rounded coefficients shifts it, and Section 5.4 quantifies that shift rather than hiding it.

No figure in this paper is quoted to more digits than the generator produces, and the build fails if a printed figure drifts from the model, so the precision shown is the precision computed --- which is not the same as the precision warranted, and this section is the distinction.

## 4.6 Accounting choices

Institutional overhead is the largest single accounting choice in synthesis cost, and at base DFT cost synthesis is 81 to 94% of the level-2 figure.

**The rate.** @azoulay2025icr report, across 354 NIH-funded institutions, that *negotiated* indirect-cost rates average 58% while *effective* rates average 42%. The two are not interchangeable, and the distinction matters for how we apply them. The effective rate is defined as recovered indirect costs divided by **total direct costs**; the negotiated rate applies to **modified total direct costs**, a narrower base that excludes certain categories. The 25% to 45% range for effective rates is quoted from the same study by @crs2026indirect.

We take **42% at base and apply it to total direct costs**, which is the base its source defines it over. Applying it instead to a narrowed base excluding service-centre fees and tuition; that was a rate/base mismatch, and correcting it raises the indirect term per attempt from \$21.91 to \$80.05. The narrowed base is retained below as an accounting scenario, not as an alternative definition. The high value of 45% is the top of the effective range. A 58% row appears as a negotiated-rate illustration: 58% is an average of a different quantity and is not an upper bound on an effective rate. We follow the source's vocabulary in calling this indirect cost recovery rather than F&A.

Two caveats on this source: its data are NIH indirect-cost records rather than a census of US universities, and it reports averages across institutions rather than a rate any one laboratory faces.

**The base.** We call the narrowed variant *MTDC-like* rather than MTDC, and the distinction is worth stating because the regulation is explicit. Modified total direct cost is defined as "all direct salaries and wages, applicable fringe benefits, materials and supplies, **services**, travel, and up to the first \$25,000 of each subaward", excluding equipment, capital expenditures, patient care, rental costs, tuition remission, scholarships and fellowships, participant support, and subaward amounts above \$25,000 [@cfr2001]. So excluding tuition is MTDC; excluding service-centre fees is not, because the definition names services as part of the base. The same section adds that other items "may only be excluded when necessary to avoid a serious inequity in the distribution of indirect costs, and with the approval of the cognizant agency for indirect costs" --- which is to say the regulation anticipates an exclusion of this kind and makes it a case to be approved, not a definition to be applied.

Our reasoning for testing it is that federal rules direct recharge rates to be composed of direct costs and an allocable share of indirect costs [@cfr200468], so applying institution-wide overhead on top risks counting some of it twice. We treat that as a hypothesis rather than a demonstrated fact: the rule does not establish that any particular facility's fee schedule absorbs the same cost pools an institution-wide rate covers, and we have not inspected those pools. It is a scenario in the table below rather than the default, for two reasons --- pairing an effective rate with a narrowed base is a rate/base mismatch whatever the merits of the exclusion, and the exclusion is not one the definition grants.

| Basis | \$ per attempt | Level 2: A / B / C |
|:---------|--:|:-----------|
| Direct costs and tuition, no indirect recovery | 191 | \$744 / \$708 / \$874 |
| Effective 42% on an MTDC-like base (fees and tuition excluded) | 213 | \$819 / \$783 / \$949 |
| **Effective 42% on total direct costs (default)** | **271** | **\$1,000 / \$980 / \$1,100** |
| Effective 45% on total direct costs (top of the effective range) | 276 | \$1,038 / \$1,002 / \$1,168 |
| Negotiated 58% on total direct costs (a different quantity) | 301 | \$1,123 / \$1,087 / \$1,253 |

Between the extreme variants the level-2 figure moves by 51%; moving from direct costs only to the default treatment accounts for 37% of that. The second row is the pre-correction treatment, retained so the effect of the rate/base change is visible: moving 42% from the narrowed base to total direct costs raises the indirect term from \$21.91 to \$80.05 per attempt. Read in the other direction, the pre-correction narrowed base put level-2 cost 20% below the default.

We default to including overhead because the question is the resource cost of a validated material, which a funder bears.

# 5. Results

## 5.1 Base case

| Output | A | B | C |
|:-----------|--:|--:|--:|
| 1. per robust DFT-stable prediction | \$31.48 | \$19.05 | \$76.61 |
| 2. per experimentally validated material | \$1,000 | \$980 | \$1,100 |
| --- of which compute | \$90.65 | \$54.87 | \$221 |
| --- of which synthesis | \$928 | \$928 | \$928 |

The synthesis term is identical across pipelines. This is structural, not coincidental.

The base case is the middle reading throughout: @prein2025's 29.17% unconditional success rate and the one recipe per target their campaign reports, with the attempt cost of Section 3.5. **Success rate and recipe count have to be taken from the same campaign.** They are not independent inputs --- a campaign that retries failed targets records both a higher success rate and a higher recipe count --- so pairing one campaign's success rate with another's recipe multiplicity misprices the result in whichever direction the mismatch runs, and by a large factor: charging the middle reading A-Lab's 6.19 recipes instead of its own one would raise every level-2 figure in this table about fourfold. Section 5.7 reports the other two readings, each with its own recipe count.

## 5.2 An MLIP pre-filter cuts DFT cost by 39%, not several-fold

Pipeline B costs \$19.05 per robust DFT-stable prediction against A's \$31.48, a ratio of 1.65, so B is 39% cheaper. The filter saves money because DFT then runs on a pool that is 15.2% stable rather than 9.2% [@szymanski2025baselines]. The relaxations themselves cost about three cents.

The ratio is not independent of Supplement S1: because DFT spend per stable hit is DFT cost divided by purity, the level-1 cost ratio between two pipelines approaches their purity ratio whenever DFT dominates the compute term --- which it does at base, where the relaxations cost about three cents. So 1.65 here and the ion-exchange acceleration factor of 1.65 in Section 5.4 are very nearly the same quantity reached from two directions; generation, filter and convergence costs account for the small difference. We report both because they answer different questions --- what a filter saves, and whether a benchmark predicts it --- but a reader should not count them as two findings.

**A fourfold benefit is what this analysis yields if benchmark classification rates are used in place of measured ones, and the error is easy to repeat.** That route takes classification rates from a benchmark measured on one candidate distribution [@riebesell2025] and applied them to a differently constructed pool. Those rates predict that 37% of filter-passed candidates are DFT-stable; direct measurement on the actual pool gives 15.2%. Substituting the measured value more than halves the estimated benefit.

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

**One denominator, stated once.** Every relative cost difference in this section and the next is the gap of the dearer pipeline over the **cheaper** one, $\max/\min - 1$. The convention matters because the two directions are not the same number: A exceeding B by 10% is B falling short of A by 9.09%, so measuring against the dearer pipeline would make the same difference look smaller and would move every threshold reported here. The choice of the cheaper pipeline as denominator is the decision-relevant one --- it asks what premium the dearer option carries --- and it is symmetric in its arguments, so it does not depend on which pipeline is named first. That last property is what makes it usable in Section 5.6, where which pipeline is cheaper varies from draw to draw.

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

Ten per cent is a convention, not a decision criterion, so we report three. Holding all other parameters at the baseline, the generative-pool decision reaches a 5% gap at about 15 core-hours per candidate, 10% at about 31, and 20% at about 65. The filter decision reaches the same three at about 77, 170 and 410. Every one of these crossings falls inside the 3-to-1,000-core-hour range we test, so none is an extrapolation of the fitted relationship. They are given to two significant figures under the policy of Section 4.5, and the distribution reported next is more informative than any of them.

That both decisions cross a 10% gap inside the tested range is the main thing this section establishes, and it is a change of sign from what a more expensive synthesis baseline would give. Verification cost is not a second-order consideration under this calibration: a group paying more than about 31 core-hours per candidate to verify generated candidates is making a pipeline choice that moves its cost per validated material by more than 10%.

**The baseline crossing is one draw, and a low one.** Because the crossing depends on the synthesis expenditure and the compute coefficients, all of which are uncertain, it moves with them. Solving it separately inside each of 1,500 parameter draws puts the 10% generative crossing at a median of 159 core-hours, with a 5th-to-95th-percentile range of 21 to 818 --- more than an order of magnitude. The baseline value of about 31 sits between the 5th and 25th percentiles of that distribution, so quoting it alone understates where the crossing typically falls. At 5% the distribution runs 10 to 382 with a median of 78; at 20%, 43 to 1,887 with a median of 328. In 14 of 1,500 draws the 10% crossing has no solution in the domain at all, because the gap already exceeds 10% at zero verification cost. A reader deciding whether verification cost matters for their own pipeline should take the distribution, not the point.

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

The convergence of the three pipelines at low DFT cost is structural. Level-2 cost is

$$C \;=\; \frac{c_0 \;+\; r\,a}{S}$$

with $c_0$ the upstream compute expenditure per candidate sent to synthesis, $r$ recipes per target, $a$ cost per attempt and $S$ the unconditional synthesis success rate. Level-2 cost does not depend on $w$ at all: the level-1 quantity $c$ is defined per cross-functionally robust prediction, so $c_0 = (1-w)\,c$ and the two factors cancel. At base, $c_0$ is \$26.44 for pipeline A, and $(26.44 + 1.0 \times 270.64)/0.291667 = \$1,019$.

Neither $r$ nor $a$ nor $S$ is pipeline-dependent. Every DFT-stable verdict proceeds to synthesis; the disagreement rate, success rate, recipes per target and cost per attempt are *assumed* identical however the candidate was found. This is imposed by the model's structure, not tested by it: sweeping parameters confirms the arithmetic, not the assumption.

| DFT core-h | Level 1: A / B / C | Level 2: A / B / C | Spread | Synthesis share |
|--:|:------|:--------|--:|:--|
| 2.975 | \$2 / \$1 / \$5 | \$930 / \$930 / \$940 | 1.01x | 99%--100% |
| 54.5 | \$31 / \$19 / \$77 | \$1,000 / \$980 / \$1,100 | 1.17x | 81--94% |
| 1,000 | \$577 / \$349 / \$1,398 | \$2,600 / \$1,900 / \$5,000 | 2.56x | 19--48% |

The span is the dominant source of variation in this section. Synthesis falls from essentially the whole of level-2 cost at the bottom of the DFT range to under half of it at the top, and the pipeline spread goes from 1% to 156%. A reader who treats either end as the base case will reach a different conclusion about whether pipeline choice matters, which is why Section 4.3 declines to privilege one and this section reports crossings instead.

**The 1.17 spread is conditional, not a bound.** It assumes synthesis success, recipes and attempt cost do not depend on how a candidate was found. There is a plausible direction for the first --- MLIPs are trained on databases dominated by materials that have actually been made, so a pre-filter may favour candidates that are *more* synthesisable, which would widen the spread --- but plausibility is not a proof, and pipeline-specific differences in recipes or attempt cost could push either way. Rather than leave that as a warning, Section 5.5 asks how far the assumption has to fail before the ordering changes.

## 5.5 How far the shared-synthesis assumption has to fail, and for which question

A reader who doubts that synthesis is pipeline-independent does not need to be told the assumption might fail; they need to know how large a failure would change the answer. Relaxing the assumption gives the general ratio

$$\frac{C_i}{C_j} \;=\; \frac{Q_i}{Q_j}\,\cdot\,\frac{S_j}{S_i}\;,\qquad Q_i \;=\; c_{0i} + r_i a_i$$

and each quantity can be solved for a stated target, holding the others shared.

**Two different questions, two different boundaries.** *Parity* is where two pipelines cost the same: with $r$ and $a$ shared, $S_C/S_B = Q_C/Q_B$. A difference slightly beyond it reverses the ranking --- but two options that were nearly equal remain nearly equal, so reversal is not economic significance. *Materiality* is where the gap reaches 10%, the standard used throughout these results; on the $\max/\min$ convention of Section 5.4 that keeps C and B within 10% of each other while

$$\frac{Q_C/Q_B}{1.10} \;\le\; \frac{S_C}{S_B} \;\le\; 1.10\,\frac{Q_C}{Q_B}$$

The two are easy to conflate, and conflating them in either direction misstates the result: reading a parity boundary as a materiality boundary overstates how little it takes for pipeline choice to matter, and reading a materiality boundary as a parity boundary overstates how robust the ordering is. They are reported separately below.

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

**All of these are break-even solves, not measurements.** No source reports a pipeline-specific synthesis difference in either direction, so every figure is the size a *hypothetical* difference would have to reach. That is the point of reporting them: they convert an untested assumption into stated tolerances.

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

Read that way, the table says two things, and the second has changed sign relative to a model with a larger synthesis bill. **Reversing the ranking takes a difference the synthesis literature could in principle resolve**: at base calibration a 16.9% relative success advantage for generative candidates, or 3.85% more recipes in the filtered pipeline, flips which pipeline is cheaper. **And the 10% materiality band no longer contains equal synthesis performance** for the generative comparison: it runs from 6.2% above to 28.5% above equal success, so identical synthesis behaviour already leaves C more than 10% dearer than B. The filter comparison still behaves the other way --- 14.83% of the baseline recipe count, about 0.148 extra recipes per target, is needed before A and B differ materially --- which is the same asymmetry the sweep shows.

**What this does not establish.** We stated above that no source reports a pipeline-specific synthesis difference in either direction. That means the plausible range for such a difference is not established, and it therefore cannot support any claim about which of these boundaries is likely to be crossed. An absent measurement is evidence neither of a small effect nor of a large one. So these boundaries are **conditional tolerances, not demonstrated robustness**: they say what size of difference would change each conclusion, and the paper cannot say where real pipeline-specific differences sit relative to them. A 16.9% relative success advantage for generative candidates, or 3.85% more recipes in a filtered pipeline, are shown here to be neither plausible nor implausible --- only unmeasured.

So the defensible statement is narrower in both directions than "pipeline choice does not matter economically" and than its negation. At the deterministic baseline the two comparisons behave differently: the filter decision needs a synthesis difference above its materiality boundary before it matters, while the generative decision is already material at equal synthesis performance and would need a success advantage of 6.2% or more to stop being so. Which is cheaper, and by how much, therefore rests on the shared-synthesis assumption and on a baseline calibration the paper itself declines to privilege, and the ordering should not be treated as established.

The two columns behave differently in verification cost, and the difference is informative. The materiality column rises only from 10.27% at 3 core-hours to 14.83% at base, because a 10% gap at level 2 has to be paid out of the synthesis bill rather than out of the compute difference. The parity column is driven entirely by that compute difference and so rises steeply, from 1.1% to 16.9% over the same interval. They answer different questions and should not be quoted as one tolerance. The flatness is weaker than it would be under a larger synthesis bill: with one recipe per target the synthesis denominator is smaller, so verification cost reaches further into both columns.

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

## 5.6 Under uncertainty: reliably ordered, material in about one draw in ten

Across 20,000 draws respecting the documented correlations, with pipelines compared pairwise within each draw:

Three quantities, defined precisely because they are easy to confuse. **P(B < A)** is the share of draws in which B's cost is below A's *in the same draw*, so both see one parameter world. **P(differ > 10%)** is the share of draws in which the dearer of the pair exceeds the cheaper by more than 10%, $\max(C_A, C_B)/\min(C_A, C_B) - 1 > 0.10$, again paired within a draw and on the same denominator convention as Section 5.4. Both are paired comparisons: each draw is one parameter world seen under two pipelines.

**The crossings of Section 5.4 and the material shares here are the same comparator, but neither is the other's prior mass.** A crossing is where the gap reaches 10% with every other parameter at base; in simulation the crossing itself moves, because the compute term is measured against the synthesis expenditure $b = ra$ and both recipes and attempt cost are drawn. Synthesis success is not among the quantities that move it: $S$ is shared, so it cancels from the paired ratio and appears nowhere in $d^{*}$; sweeping it across the three readings' full range leaves both crossings unchanged. The two cases show the gap in both directions. The filter crossing is 167 core-hours and 31.1% of draws have a verification cost above it, but only 10.0% of draws are material; the generative crossing is 31 core-hours with 60.3% of draws above it against 34.2% material. In both the prior mass above the baseline crossing overstates the material share by a factor of two to three, because draws with a larger synthesis bill push the crossing up past their own verification cost. The effect runs both ways within each case: material filter draws occur at verification costs from 60 core-hours, well below the baseline crossing, and immaterial ones occur as high as 999. Either share recovered from the other crossing would be wrong, because the threshold is a function of the synthesis bill rather than a constant.

| Level | P(B < A) | P(differ > 10%) | Overlap of marginals |
|:--|--:|--:|--:|
| 1 | 99.5% | 98% | 90% |
| 2 | 99.5% | 10% | 97% |
| 3 | 99.5% | 10% | 99% |

The level-3 row is a comparison of pipelines, not a cost level: it uses a nonzero novelty share drawn from the range in the parameter file. That range needs stating precisely, because it is not a measurement. No source publishes a nonzero novelty count for this campaign: @leeman2024 state that "none of the materials produced by A-lab were new", and the correction declines the claim rather than quantifying it. So every nonzero value we use is a statistical upper bound on a zero count --- the Wilson 95% and 99% bounds on 0 of 36, 9.6% and 15.6% --- chosen because they are the most generous rates the data admit and therefore make cost per new material optimistic. The cost *level* at level 3 is not reported anywhere in this paper, because at the published count the implied cost is unbounded (Section 7, item 5).

Most of this follows analytically from Section 5.4, and the simulation is a numerical check rather than a discovery. B's compute term is below A's in all but a small tail of draws, because the two purities are drawn as a bloc from a single source and B's post-filter purity exceeds A's pool prevalence across almost all of that source's range. P(B < A) is therefore near one at every level for the same reason, which is why the figure is identical down the column. The informative number is the second one: the dearer of A and B exceeds the cheaper by more than 10% in 10.0% of level-2 draws. That is the paired condition itself, not a statement about the compute share --- the two are different events, though they are closely related here because the pipelines differ only through compute.

That 10.0% is sensitive to the DFT-cost prior, which we chose rather than measured: it is log-uniform over a span whose base Section 4.3 calls a convention. A prior weighted towards the top of the span would raise it substantially, and a reader who believes modern production DFT costs hundreds of core-hours per candidate should read the 1,000-core-hour row of Section 5.4 instead of this table. The generative comparison is material in 34.2% of draws on the same prior.

At level 1 the pipelines separate sharply. At level 2 the ordering survives draw by draw, while the magnitude matters in about one draw in ten for the filter decision and about one in three for the generative one. The distinction is the familiar one between the sign of an effect and its size, and it is worth stating here because comparisons of this kind are usually reported as the former: a paper reporting that B beats A in 99.5% of simulations would be stating something true and, nine times in ten, economically immaterial.

The marginal cost distributions overlap heavily at every level, including level 1: absolute cost is dominated by uncertainty all three pipelines share. Only the paired comparison separates them, and only at level 1. The overlap coefficients and their bin-count and resampling diagnostics are in Supplement S2, because the paired difference and the probability of exceeding a materiality threshold are the decision-relevant quantities and the coefficient adds nothing to either.

## 5.7 The answer depends on which reading is right, and the recipe count matters more than the success rate

The figures below are Monte Carlo medians within each reading, with every other parameter drawn from its distribution. They are not the deterministic point estimates of Section 5.1, which hold all parameters at base; the two differ because the base values are not the medians of their own distributions and several inputs vary within each reading. The base case of Section 5.1 corresponds to the middle reading.

| Reading | Success | Recipes per target | Level 2, pipeline B, scenario median | 5th--95th percentile of draws |
|:--|--:|--:|--:|:--|
| Optimistic (A-Lab) | 63.2% | 6.19, reported | \$3,005 | \$2,137--\$4,106 |
| Middle (Prein) | 29.2% | 1, reported | \$1,159 | \$648--\$2,337 |
| Pessimistic (Leeman) | 5.2% | 6.12, reported | \$34,286 | \$14,807--\$100,835 |

Across the three readings that is a factor of 30 for pipeline B. Note that it is a factor across all three and not between the two extremes of the success rate, because the reading with the highest success rate is not the cheapest.

**Each reading carries the recipe count its own campaign published.** The first and third read the same campaign, so they share its experiment count: @leeman2024 re-count the outcomes of the 2023 article's 355 experiments across 58 targets, which is 6.12 per target, while the corrected article's 353 across 57 gives 6.19. The two differ only because the correction removed one target and two experiments. A derived recipe count has no place in either reading: the budget model of Section 3.5 exists for a reading that supplies a success rate without an experiment count, and applying it to a campaign that published its own would here have invented about three extra attempts per target and raised the pessimistic figure by about 46%.

**The reading labelled optimistic is not the cheapest.** This is the clearest single result of the comparison and it does not follow from the success rates. A-Lab's reading has the highest success rate of the three --- 63.2% against the middle reading's 29.2%, a factor of 2.17 --- and yet implies 2.6 times the cost per validated material, because it reached that success rate with 6.19 recipes per target against one. Decomposed on the synthesis term, which dominates at this verification cost, the campaign bought a 2.17-fold improvement in success for a 6.19-fold increase in attempts per target, so the synthesis cost of a validated material rose by a factor of 2.86 net of the success gain. The ordering of the three readings by cost is therefore middle, optimistic, pessimistic, and the labels refer to how optimistic each reading is about what was *made*, not about what it cost.

**That decomposition is a comparison across campaigns, not a measured return to retrying.** @prein2025 and @szymanski2023alab attempted different targets in different chemistries, and a campaign choosing to attempt each target once is also choosing which targets to attempt. We cannot separate the return to additional recipes from the difficulty of the target set, and nothing here establishes that a laboratory would do better by abandoning failed targets after one attempt. What it does establish is that recipe multiplicity is a first-order cost parameter --- it enters level-2 cost with the same unit elasticity as the success rate (Section 5.8) --- and that a cost estimate taking a success rate from one campaign and an attempt count from another can be wrong by a factor of several in either direction. Both of our campaigns report an experiment count; many synthesis papers do not, and a paper reporting success rates without them cannot be costed.

**Within a reading, pipeline choice matters most where synthesis is cheapest.** The between-pipeline ratio is $(c_{0i} + r a)/(c_{0j} + r a)$, which cancels the success rate but retains the recipe count and attempt cost. Since the compute term is a fixed number of dollars and the synthesis bill is not, pipeline choice moves the median by 1.21 times under the middle reading, 1.07 under the pessimistic one and 1.06 under the optimistic one. The reading that makes a validated material cheapest is the one in which the choice of computational pipeline matters most, which is the reverse of the intuition that expensive synthesis makes compute decisions matter.

**This factor is not measurement uncertainty.** Two of the three readings interpret the same experiment and disagree about what was made. Harmonising the identification standards and reconciling the denominators would narrow the comparison and is worth doing with existing data. Closing it would need new synthesis campaigns with phase identification both sides accept.

**And the factor is probably understated, because identification is priced at one tier.** As Section 3.5 sets out, every reading is charged the same \$80.00 diffraction service fee although the readings differ precisely in how strictly they identify a phase. Charging each reading the tier its own standard implies would widen the factor from 33 to 71 if strictness and cost rise together, or narrow it to 15 under the reverse assignment, which we regard as the less plausible of the two. We report the uniform-tier figures as the model's output and this range as its known bias, rather than selecting an assignment we cannot source.

Where a single number is unavoidable we quote the middle reading with the spread beside it, and note that it is the least established of the three: it is a preprint reporting the smallest campaign. It is also, now, the cheapest, so quoting it alone is not a conservative choice.

## 5.8 Where the cost sits, and what that implies for improvement

We report elasticities: the percentage fall in cost per 1% proportional improvement in a lever, scale-free so levers in different units compare directly. Note that these are proportional, not absolute: one percentage point of synthesis success is a 1.5% proportional gain under the optimistic reading and a 19% proportional gain under the pessimistic one, so percentage-point framings are not comparable across readings and we avoid them.

| Lever | A | B | C |
|:-----|--:|--:|--:|
| Synthesis success rate | 1.000 | 1.000 | 1.000 |
| Recipes per target | 0.911 | 0.944 | 0.808 |
| Cost per synthesis attempt | 0.911 | 0.944 | 0.808 |
| Compute price (best compute lever) | 0.089 | 0.056 | 0.192 |

**The synthesis levers should not be ranked against each other.** Success has elasticity exactly one, because it divides both terms. Recipes and cost per attempt have elasticity equal to the *synthesis share* of total cost, and the gap between them and unity *is* the compute share rather than a difference in leverage.

The finding is the magnitude gap, and it is a single-digit-to-low-double-digit gap rather than the two orders of magnitude a larger synthesis bill would produce. At the deterministic base, a 1% proportional improvement in a synthesis term moves level-2 cost 4 times as much as a 1% proportional improvement in compute price for pipeline C, 10 times for A and 17 times for B. Evaluated instead at the Monte Carlo medians the same ratios are 19, 42 and 70, because the DFT-cost prior puts most of its mass below the base value. We report the two separately because they are different estimands: the first is a ratio at one parameter vector, the second a ratio of median elasticities across 20,000 draws. This is a ratio of cost shares, not a return: it says where the money is, not what it costs to move it. At the top of the DFT span the ratio falls below one for every pipeline --- compute is then 52 to 81% of the total, and 81% for the generative one --- so synthesis dominance is a property of the lower part of the verification-cost range rather than of the model. This is the single most important qualification on the paper's headline claim, and Section 4.3 is why we cannot resolve it: we do not know where in that range a modern verification workflow sits.

**Verification accuracy is not a lever on level-2 cost, and a model that makes it one has double-charged.** With an unconditional success rate, $w$ cancels out of level-2 cost entirely: compute per candidate sent to synthesis is $c_0 = (1-w)\,c$, so the $(1-w)$ that discounts the level-1 quantity and the one that would scale it back are the same factor. Holding $c_0$, recipes, attempt cost and observed success fixed, changing the diagnostic $w$ does not change the cost of a validated material. The cancellation is easy to lose: pairing a campaign-observed success rate with a label-accuracy factor restores an apparent elasticity of $w/(1-w)$, which is the signature of charging the same failures twice (Section 3.4). Anyone extending this model should check that result against the limiting case: at $w = 1$ no verdict survives the cross-functional check, so level-1 cost is unbounded while level-2 cost must stay finite, because the campaign still made materials. Whether better verification would raise experimental success, and at what compute cost, is a joint relationship this model does not estimate.

**One lever requires no research expenditure.** Switching from on-demand to spot compute pricing carries a discount of about 62% in the compute-optimised instance prices recorded in the parameter file, with provider, region, instance type and date. It requires no research expenditure, which is the sense in which we call it free; it is not operationally free, since spot capacity is interruptible and retries, checkpointing and delay carry costs we do not model. The discount is also provider- and instance-specific and does not apply uniformly to GPU and CPU pricing. Because it scales the whole compute term, its effect on level-2 cost is 62% of the compute share: 3.5% for pipeline B and 11.8% for C. The levers worth several times more all require synthesis research whose cost nobody has measured. Ranking returns per dollar would need those costs; we observe only that the free lever is now worth single-digit percentages rather than fractions of one, which is a consequence of the base case's small synthesis bill and not of anything about compute pricing.

## 5.9 Break-evens

**The filter has no meaningful break-even batch size.** Loading the potential costs 0.00024 core-hours against a saving of 29.5 core-hours per candidate, so the informative quantity is the per-candidate saving rather than a threshold: any additional fixed cost of $X$ core-hours, such as fine-tuning, repays after $X/29.5$ candidates.

**Synthesis cost at which compute begins to matter --- which, for one pipeline, is already.** Taking "matters" as compute reaching 10% of level-2 cost, the attempt cost at which each pipeline crosses that line is \$144 for B, \$238 for A and \$579 for C. Only B's lies below today's \$271: compute is already 19.2% of level-2 cost for the generative pipeline and 8.9% for the unfiltered one, so for C the threshold is the attempt cost at which compute would fall *back* to 10%. The threshold depends only on the compute term, so it is unchanged by the accounting choices of Section 4.6, which move the attempt cost itself. At the top of the DFT span compute matters for all three.

**Generative-pool parity.** C matches B at level 1 when filter purity on the generative pool reaches 15.5%, 4.1 times the measured value.

**How strong would a synthesisability effect have to be?** For pipeline choice to double level-2 cost, an MLIP pre-filter would have to raise synthesis success from 29% to 56% --- below the optimistic reading's own 63.2%, so unlike the previous calibration this is no longer an effect larger than anything observed. It remains an effect no study has measured by pipeline, and it specifies how large an effect the follow-up study would need to detect.

## 5.10 Where the evidence is weakest

A one-at-a-time sweep is led by a single parameter at each level: DFT cost at level 1 and synthesis success at level 2, which account for 99.8% and 50.9% of the summed squared one-at-a-time ranges respectively. The level-1 figure is near-total; the level-2 figure is a bare majority, with the remainder spread across recipes per target, attempt cost and DFT cost, so "dominated" fits the first and not the second. That statistic is not a variance decomposition and should not be read as one; it reflects the width of each parameter's assumed range as much as the model's response to it. **The tornado maps where the evidence is weakest rather than where the leverage is.** The two quantities most in need of better measurement are DFT cost on modern hardware and synthesis success from independent campaigns.

# 6. Discussion

## 6.1 For research groups

At base DFT cost, the choice between computational pipelines is a choice about a line item worth 6 to 19% of the total; at the top of our DFT span it is 52 to 81%, and the argument below reverses accordingly. A group that intends to take candidates into the laboratory should still optimise the laboratory first, because the synthesis share is the larger one at base and because its elasticity is higher. But the two decisions inside "pipeline choice" should be treated differently: at base calibration the filter decision moves level-2 cost by 3.6% and the generative-pool decision by 16.9%, so the first is a rounding error against the synthesis bill and the second is not. A group that stops at computational screening faces a larger choice again --- the pipelines differ by a factor of 1.8 to 4.0 at that stage. None of this survives a change in verification cost: a group paying more than about 31 core-hours per candidate should treat the generative-pool decision as material to its total, and more than about 170 the filter decision too.

Our results also suggest two specific practices. Report an MLIP's convergence rate alongside its accuracy, because a potential that fails to converge on most structures from a cold start has an effective cost unrelated to its per-step speed. And check the thread scaling of a screening configuration before committing a budget to it: on our platform, which is virtualised and should not be generalised from, running single-threaded across many structures rather than multi-threaded on one was the difference between one core-hour and eighty. The general point is that core-hours are billed on allocated cores, so a configuration that scales poorly is charged in full for the cores it wastes.

## 6.2 For funders

Synthesis is where the money is at base DFT cost --- 81 to 94% of the cost of a validated material, with a synthesis lever worth 4 to 17 times the best compute lever --- but the margin is a single-digit-to-low-double-digit factor, not the one to two orders of magnitude a larger synthesis bill would give, and it inverts at the top of our verification-cost span, where compute is 52 to 81% of the total. The ordering at base is robust across every parameter configuration we tested at that verification cost; it is not robust to verification cost itself, and we do not claim to know what a dollar spent on synthesis research buys.

But the more valuable expenditure may be one the model cannot price. The factor of 30 between readings of the synthesis evidence exceeds every methodological difference in the paper combined. Funding independent synthesis campaigns with phase identification that both sides of the current dispute would accept would do more to establish what materials discovery costs than any improvement to the discovery methods themselves. At present the field does not know this number to within an order of magnitude --- and, as Section 5.7 shows, the reading that counts the most successes is not the one that implies the lowest cost, so resolving the identification dispute will not by itself narrow the cost range. Campaigns also need to report how many recipes they attempted per target, a figure Section 5.7 shows moves cost more than the success rate does.

This is a specific instance of the general problem in @bloom2020ideas and @scannell2012eroom: when the cost per research output is unknown, there is no denominator against which to judge whether a new tool has improved productivity. Materials discovery currently lacks that denominator, and the missing measurement is experimental, not computational.

## 6.3 For autonomous laboratory programmes

Within our search scope we did not find a published capital or operating cost for an autonomous *bulk solid-state* synthesis platform. The only figures we located are for a different chemistry. @pilon2026 report that high-end self-driving laboratories "often exceed US\$100,000" excluding analytical components, that their predecessor flow-chemistry platform cost approximately US\$50,000 in essential components, and that substituting a human-in-the-loop sampling unit brings their own platform to approximately US\$5,000. That is the right disclosure, and it is the exception. For solid-state platforms the only capital figure we found is a press statement, which we do not treat as a citable number.

@lo2024frugal review low-cost self-driving laboratories and the "frugal twin" approach, and tabulate estimated dollar costs for twenty-five platforms. That is a cost literature, and it narrows our claim considerably: what we could not find is a capital or operating cost for an autonomous *bulk solid-state* synthesis platform of the kind that produces our success rates, not an absence of platform costing in general. The absence of any published capital figure for a solid-state platform is a striking gap, because these platforms are justified on economic grounds --- they make materials faster and therefore cheaper --- and for the solid-state case the cost side of that argument is not in the literature. It also matters for our model specifically: a capital figure is what would let the synthesis term be decomposed into labour, consumables and amortised equipment, which is currently the largest unmodelled structure in the paper.

Our model suggests the relevant metric is cost per validated material rather than samples per day, since throughput claims and cost claims diverge sharply. Reported peak throughput and realised output are different quantities --- one platform's software paper reports around 3,500 samples over 1.5 years [@fei2024alabos] against a quoted daily capacity --- and converting between them requires a utilisation figure: realised samples divided by daily capacity times the number of eligible operating days. That is not the same as hardware duty cycle, and the two are often conflated. Utilisation is what converts a capacity figure into a cost per sample, and we did not find it reported for the platforms we looked at. A programme reporting cost per validated material, with its capital amortisation stated, would be able to make its economic case directly. @adesiji2026benchmarking propose benchmarking practice for self-driving laboratories; cost per validated output belongs in such a benchmark and is currently absent from it.

## 6.4 For benchmark design

Our Supplement S1 result is addressed to a different literature than the rest of the paper. Measured enrichment on two realistically constructed candidate pools is roughly half the acceleration factor the benchmark reports, and lower still on the generative pool. We do not attribute this to the benchmark: the evaluations differ in reference hull, candidate distribution and threshold, and the difference may be definitional rather than a weakness of the models --- the benchmark's authors themselves note that their reference-set choice could be read as overestimating performance [@riebesell2025] --- and we specify the experiment that would settle it. Until it is settled, practitioners using benchmark classification rates to plan a DFT budget should measure enrichment on their own pool rather than assuming the benchmark's figure transfers. We do not predict a general factor-of-two overestimate; we report that our own estimate halved when we substituted direct measurements.

## 6.5 For investors and the public account of AI in science

Claims that AI accelerates materials discovery by one or two orders of magnitude are, on our accounting, claims about a stage representing 6 to 19% of the cost of producing a validated material at base verification cost. They may well be true as stated. They do not imply a comparable reduction in the cost of discovery, and the gap between the two statements is where most of the money is. That qualification is itself conditional: at the top of our verification-cost span the computational stage is 52 to 81% of the total, and a claim about it would then be a claim about most of the cost. Which regime a given programme is in depends on a quantity nobody has published for a modern workflow.

The narrower point stands on the funnel alone: more candidate materials is not more validated materials, and where the terminal stage is unchanged it is not obvious that it is even more discovery.

# 7. Limitations

1. **Primary threat to validity: synthesis success is assumed independent of pipeline.** No source we found measures this. Section 5.5 gives the tolerances: the ordering flips at differences too small for the synthesis literature to resolve, a 10% gap needs substantially larger ones, and because the differences are unmeasured neither boundary establishes robustness. Which pipeline is cheaper should not be treated as established. The follow-up study is to attempt matched sets of filtered and unfiltered DFT-stable candidates and compare success rates.
2. **Filter recall is not measured on these pools.** We import it from the benchmark, which is an assumption, not a measurement. Measured purity and imported recall describe different populations, so both can be correct and still be mismatched for our use.
3. **The generative-pool result's magnitude, and its materiality, depend on which end of a printed range we take.** The source's main text gives 3.8% to 8.8% for two generative models after filtering without assigning the endpoints; we take 3.8% for the configuration we model on the strength of a supplementary figure read by eye. Across the range the level-1 ratio runs from 4.02 to 1.75 and the level-2 gap from 16.9% to 4.2%, so the direction does not change but the conclusion of Section 5.4 holds only at the low end. Both purities rest on 300 structures per method.
4. **Overhead treatment is an accounting choice** moving level 2 by 51% between the extreme variants of Section 4.6, while barely moving the pipeline spread. It also moves the materiality thresholds of Section 5.4 nearly in proportion to the attempt cost, a near-proportionality that holds under these parameters because generation and filtering cost almost nothing beside verification, and that Section 5.4 shows is neither an identity nor as tight here as under a larger synthesis bill. The rate itself is an average across NIH-funded institutions, not a rate any one laboratory faces.
5. **No level-3 cost is reported.** The novelty share for the reference campaign is disputed, and the count we would have to use is zero, at which the implied cost is unbounded. Level 3 appears in the pipeline comparison of Section 5.6, which uses a nonzero novelty share from the parameter file, but no dollar figure for it appears in this paper.
6. **DFT cost spans more than two orders of magnitude.** Results are reported across the span.
7. **The cross-functional transition rate is a proxy, and it now affects only level 1.** $w$ is the directed fraction of candidates called stable at one level of theory and unstable at a higher one. It is not an experimental error rate, a material above the hull is not thereby impossible to synthesise, and functional disagreement also runs the other way, which we do not credit. Since level-2 and level-3 costs now use unconditional success rates, $w$ no longer enters them; it defines the level-1 output and is otherwise reported as a diagnostic.
8. **Our DFT measurements are not commensurate with the hull the model uses** (Section 4.3). The timings are Quantum ESPRESSO with ultrasoft pseudopotentials; the hull defining level 1 is the Materials Project's, so our energies cannot be placed on it and the low end of the span is illustrative rather than a measured cost of the task the model prices. We handle the consequence by reporting thresholds (Section 5.4) rather than a base-case claim. This remains the most consequential unresolved issue in the paper, and closing it needs an MP-compatible calculation on comparable hardware.
9. **One parameter is graded `missing` and five are `assumption`.** The `missing` one is the reference-phase count of Section 3.6, held at zero. The five `assumption` parameters are the share of filter-passed candidates sent to DFT, the reference atom count for the SCF scaling check, the pipeline-specific success multiplier (set to one, which is the assumption Limitation 1 is about), working weeks per year, and firings per crucible. Three further parameters are `proxy` in a way worth naming: filter recall is imported from a benchmark measured on a different population (Limitation 2); the tuition term takes the NRSA predoctoral tuition-allowance cap, which is a published figure for a training grant rather than an observed charge on a research project; and precursor mass per attempt takes a bench-scale range for which we found no autonomous-laboratory figure.
10. **Monte Carlo choices shape the distribution.** The DFT-cost prior is chosen, not measured, and Section 5.6's material-share figures are sensitive to it. The three readings receive equal weight, an assumption with no basis; named scenarios are reported so readers can apply their own. The level-2 95th percentile is a statement about whose re-analysis to believe: \$64,269 under equal weights, falling to \$3,876 if the pessimistic reading is given zero weight.
11. **The enrichment gap has an unresolved competing explanation:** the two studies judge stability against different reference sets.
12. **Our hardware is unusual.** An ARM64 laptop under virtualisation produced two platform artefacts that we document and correct for; the DFT timings should not be generalised to server hardware.
13. **"Validated" does not mean the same thing in all three readings.** Level 2 is defined once, but the readings differ on the evidentiary standard for identifying the target phase: @leeman2024 regard only one of three claimed successes as convincingly demonstrated. Part of the factor of 30 is therefore a difference in how strictly an output is counted, not a difference in what it costs to produce one. We do not decompose the factor into these two components, and a reader should not read all of it as a cost spread.
14. **Published recharge rates may omit subsidised components** [@strom2020]. We treat this as directional for the XRD and furnace line items only, not as a certification that the whole attempt cost is conservative.
15. **The base case still combines two settings, though no longer three.** Synthesis success and recipe multiplicity now come from one campaign: @prein2025's 7 of 24 targets, each attempted once. What they are combined with is an attempt cost built for a manual academic laboratory --- a graduate trainee's time at a trainee's throughput, priced from institutional fee schedules --- whereas both automated campaigns we draw success rates from are robotic platforms whose cost structure is commissioning, supervision and amortised capital rather than bench time. So the attempt cost is not campaign-specific in any of the three readings, and we have no fee-schedule equivalent for an autonomous platform (Section 6.3). The direction of the resulting error is not known: a robotic platform may run an attempt for less in consumables and more in capital, and the capital term is absent from our accounting entirely.
16. **Cost per attempt may not be pipeline-independent after all.** Item 1 above concerns the success rate; the same objection reaches the attempt cost. @cheetham2024 count 41,667 compounds of radioactive elements in one large generative stable set of 384,870 --- a different set from the one we model. They report counts, not a share; the implied fraction is ours. Whether our generative pool shares that composition skew is untested. If it does, the cost channel is handling and disposal, which we do not model at all, rather than precursor mass, which is only \$2.64 of a \$271 attempt.

# 8. The replication package

The complete model, every parameter with its source and evidence grade, the first-hand benchmark data, the analysis code and the test suite are *to be* released as a replication package. At the time of writing the repository is not yet public and no archival DOI has been minted, so nothing in this section should be read as a claim that the results have been independently regenerated. Every figure in this paper is generated from the parameter file and the benchmark data, and the build fails if a figure in the text drifts from the model. That is a check on internal consistency, not on the correctness of the model's assumptions or of our reading of the sources.

The model is a pure function from parameters to results, so a reader who disagrees with a parameter can substitute their own and rerun. We expect disagreement about several --- the overhead treatment, the weighting of the three readings, the DFT cost span, the choice of optimistic success count --- and the package is structured so that each takes one edit.

**What the package contains, and the standard it is built to.** The test a reader should be able to apply is whether they can reconstruct the headline numbers without asking us what an input means. To that end the package carries, alongside the code: a manifest of all 88 parameters with low, base and high values, units, evidence grade, source URL and the source passage or derivation behind each; a separate manifest of the fourteen inputs to the attempt-cost estimate, each with the **usage allocation** that converts a published rate into dollars per attempt, since that allocation is the part a reader cannot infer from a fee schedule; the unrounded threshold coefficients with their residuals; the seeded sampler with its rejection handling; and a worksheet that walks the attempt cost, the level-2 equation, the threshold crossings and the decision boundaries of Section 5.5 from inputs to results with the arithmetic shown at each line, so each can be checked on paper. A build step compares every number printed in this manuscript against the generated figures and fails on any disagreement; figures the manuscript deliberately does not quote are listed with a reason rather than silently skipped. The package also carries a verification record: every bibliography entry resolved to its DOI and checked field by field against the publisher record, and every substantive claim checked against the source text, with the claims that could not be closed listed as open rather than resolved. None of this substitutes for independent reproduction, which has not happened.

# 9. Conclusion

**The strongest conclusion here is methodological.** A complete economic model of materials discovery has to separate computational hit generation, experimental realisation, novelty and utility, because they have different costs, different evidence and different failure modes. The current literature does not measure the downstream transitions well enough to support a universal cost figure, and the exercise of trying to build one is what shows where the measurements are missing.

Four findings, in order of how well the evidence supports them.

**Computational cost differences between pipelines are real and measurable per computational hit.** An MLIP pre-filter cuts modelled cost per robust prediction by 39%, and a generative pool costs 1.8 to 4.0 times a filtered ion-exchange pool at the same gate, the range spanning the two endpoints of the only figure the source prints for that purity. These rest on measured pool purities and an assumed verification cost.

**Translating those differences into cost per validated material requires downstream assumptions that nobody has measured by pipeline.** Under the illustrated academic cost structure and shared downstream behaviour, synthesis is 81 to 94% of modelled cost at base verification expense, and the two pipeline decisions move the total by 3.6% and 16.9% respectively. Each statement is conditional in both directions. It does not establish that compute improvements are economically unimportant --- and at the top of our verification-cost span computation is the larger share, 52 to 81%. Nor does it establish the ordering, which reverses under a 16.9% relative difference in synthesis success between pipelines, a quantity no study reports.

**Existing synthesis evidence produces order-of-magnitude variation across scenarios, and the mechanism is not the one the dispute is about.** Three readings of essentially two campaigns give medians from roughly \$1,200 to \$34,000. The readings differ in phase-identification standard, denominator and recipe multiplicity as well as success count, so this is a comparison of non-equivalent scenarios, not an interval around a single quantity. Within it, the multiplicity does more work than the success rate: the reading with the highest success rate is 2.6 times dearer than the cheapest because it attempted each target six times. Narrowing the range is partly definitional work on existing campaigns; closing it needs new synthesis data, reported with experiment counts, rather than better models.

**Therefore the highest-value empirical work is standardised, pipeline-specific synthesis and costing data.** A campaign that reported the following would collapse most of the uncertainty in this paper, and none of it requires new instrumentation:

- candidate source and the selection rule applied;
- the full compute workload, including failed and re-run jobs;
- the number and type of recipes attempted per target;
- labour and instrument time per attempt;
- capital utilisation and downtime;
- the phase-identification protocol, stated as a standard rather than an outcome;
- target-level success and novelty determinations;
- denominators defined so that campaigns can be compared.

Until such data exist, statements about what AI-driven materials discovery costs are statements about which re-analysis one believes, and should be written that way.

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

# Disclosures

**AI assistance.** I used Claude (Anthropic) to assist with drafting, literature search, and methodological review. I defined the research question and scope, selected the modelling framework and assumptions, conducted and debugged the computational work, verified the sources and numerical results, and revised the final manuscript. No parameter value originates from the language model: every value traces to a published source, a first-hand measurement, or an explicitly labelled assumption recorded in the parameter manifest. Every reported figure is generated from the parameter file, and I take responsibility for all methods, interpretations, and claims in this paper.

**Conflict of interest.** The author is the founder of a company working in AI-driven materials science. The computational pipeline used for the first-hand benchmarks in Section 4.2 derives from that company's codebase, though the released replication package depends on no proprietary code.

**Data and code availability.** [Repository URL and archived DOI to be inserted on release.]

