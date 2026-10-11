# What Does It Cost to Discover a Material?

### An end-to-end cost model of AI-driven inorganic materials discovery

*Working paper, first draft*

<!-- Model numbers are followed by a tag of the form k:KEY inside an HTML comment, linking them to
results/key_numbers.json, which scripts/stage2.py regenerates. tests/test_draft.py fails if a tagged number drifts;
`uv run python scripts/fill_draft.py` rewrites them. Citations are pandoc citation keys (at-sign plus key, in square brackets) that must resolve in
paper/references.bib (tests/test_citations.py). -->

---

## Abstract

Artificial intelligence has made the computational stages of inorganic materials discovery extremely cheap, and the field widely asserts that synthesis is now the bottleneck. That assertion has never been priced. We build an end-to-end cost model that follows a candidate material from generation through machine-learned screening, density functional theory verification and laboratory synthesis, and we report the cost of three outputs: a DFT-confirmed stable material, an experimentally validated one, and one that is genuinely new to science. Every parameter is sourced and graded, several are measured first-hand, and the complete model is released.

We find that pipeline choice is economically immaterial once synthesis is included. A machine-learned interatomic potential pre-filter cuts cost per DFT-confirmed stable material by 39%<!--k:l1_B_cheaper_pct-->, and a generative candidate pool costs roughly four times an ion-exchange pool at the same stage, but all three pipelines land within 3%<!--k:l2_spread_base_pct--> of one another on cost per experimentally validated material, because the synthesis term contains no pipeline-dependent quantity. Across 20,000<!--k:mc_draws--> simulations the cheaper pipeline wins in 99.4%<!--k:kill_l2_p_B_lt_A--> of draws and by more than 10% in 1%<!--k:kill_l2_material_BA-->.

The quantity that does govern the answer is the synthesis success rate, which three groups read three ways from essentially two experiments. Cost per validated material ranges from about $2,975<!--k:reading_optimistic_alab_B--> under the originating laboratory's own reading to about $49,917<!--k:reading_pessimistic_leeman_B--> under a published re-analysis of the same campaign, a factor of 17<!--k:reading_factor_B-->. No computational improvement closes this gap: the best compute lever is 26<!--k:returns_ratio_lo--> to 136<!--k:returns_ratio_hi--> times weaker per percentage point than the synthesis levers, and the only lever available at zero cost moves the result by under 3%.

We also report that a widely used stability-prediction benchmark overstates filter performance on realistically constructed candidate pools. The discovery acceleration factor of a standard potential is 1.65 on an ion-exchange pool against 3.36 reported on the benchmark test set, and 1.27 on a generative pool.

**Keywords:** materials discovery, machine-learned interatomic potentials, cost model, autonomous laboratories, research productivity

**JEL:** O31, O32, D24

---

## 1. Introduction

The computational half of inorganic materials discovery has become very cheap very quickly. Graph neural network potentials relax a crystal structure in seconds on a laptop [@deng2023chgnet; @batatia2025macemp; @chen2022m3gnet]. Generative models propose thousands of candidates an hour [@zeni2025mattergen] [CITATION NEEDED: the generation time we use, 9.22 A100-seconds per structure [@szymanski2025baselines], is about 390 an hour per GPU; "thousands an hour" needs several GPUs or a source that states it]. One recent project reported 2.2 million predicted structures, of which roughly 381,000 were placed on or below the convex hull [@merchant2023gnome]. Against that volume, the experimental half has barely moved: a laboratory still makes one material at a time, and the most prominent autonomous synthesis platform reported 36 targets realised from 57 attempts over seventeen days of continuous operation [@szymanski2023alab; @szymanski2026correction].

The field's standard account of this asymmetry is that synthesis has become the bottleneck [@montoya2024; @chung2025synthesizability; @aziz2021]. The claim appears in review after review. What it has never had is a price.

The question has a long pedigree in the economics of research. Research productivity, measured as output per researcher, has been falling across fields for decades [@bloom2020ideas], and artificial intelligence has been proposed as a new general-purpose "method of invention" that might reverse the trend [@cockburn2018]. The closest precedent for our central finding is the pharmaceutical industry, where large gains in the efficiency of early-stage screening coincided with a decline, not a rise, in R&D output per dollar, because the cost and attrition that matter sit downstream of the stage that improved [@scannell2012eroom]. We find the same structure in materials discovery, and we price it.

This matters for three reasons. A research group choosing between computational pipelines is implicitly making a budget decision without knowing the budget. A funder deciding between a larger compute allocation and a synthesis robot is comparing two numbers, one of which does not exist. And an investor reading that an AI system finds materials ten or a hundred times faster has no way to know what share of the cost that speed-up addresses.

This paper builds the missing number. We model discovery as a funnel from candidate generation through machine-learned screening and density functional theory verification to laboratory synthesis, with a cost and a pass rate at every stage, and we price the whole of it in dollars. We compare three pipelines: DFT applied to every candidate; a machine-learned interatomic potential (MLIP) used as a pre-filter before DFT; and a generative model supplying the candidate pool. We report three outputs rather than one, because a cost per "discovered material" that does not say whether the material was ever made, or whether it was new, conceals the question being asked.

Our contributions are:

1. **An end-to-end dollar model of materials discovery**, from generation through synthesis, across three pipelines, with every parameter sourced, graded by evidence quality, and released with the code.

2. **The finding that pipeline choice is economically immaterial once synthesis is included.** An MLIP pre-filter cuts cost per DFT-confirmed stable material by 39%<!--k:l1_B_cheaper_pct--> and a generative pool costs about four times an ion-exchange pool at the same stage, yet the three pipelines differ by 3%<!--k:l2_spread_base_pct--> in cost per experimentally validated material. This is structural: the synthesis term contains no pipeline-dependent quantity.

3. **The finding that the answer is governed by one contested parameter.** Cost per validated material spans a factor of 17<!--k:reading_factor_B--> across three published readings of the synthesis evidence, which is far larger than any difference between methods. The spread is not measurement uncertainty; two of the three readings interpret the same experiment and disagree about what was made.

4. **A quantified ranking of where improvement pays.** Per percentage point, synthesis levers are worth 26<!--k:returns_ratio_lo--> to 136<!--k:returns_ratio_hi--> times the best computational lever. The only lever whose cost is known to be zero, switching to spot compute pricing, moves cost per validated material by 0.6%<!--k:spot_lo--> to 2.3%<!--k:spot_hi-->.

5. **An independent observation about benchmark transferability.** A standard potential's discovery acceleration factor is 1.65 on a realistically constructed ion-exchange pool against 3.36 reported on the standard benchmark test set, and 1.27 on a generative pool. Classification rates measured on one candidate distribution do not transfer to another, and using them where direct measurements exist overstates the value of filtering by more than a factor of two.

We also report first-hand timing benchmarks for three MLIPs and for plane-wave DFT, because per-model MLIP relaxation timings do not appear to be published anywhere, and the cost model needs them.

---

## 2. Related work

Three literatures bear on this question and none of them answers it.

### 2.1 Resource accounting of computational discovery

The closest work in structure is Walker and Butler's analysis of the carbon cost of materials discovery [@walker2026carbon], which reproduces a DFT workflow for photovoltaic screening, progressively substitutes machine-learned surrogates, and quantifies the trade-off between predictive accuracy and emissions. The architecture is the same as ours — a staged pipeline with a substitutable component, costed end to end — but the unit is carbon rather than money, the scope is compute rather than the full funnel, and synthesis does not appear. Its conclusion concerns which hybrid strategies sit on the accuracy–emissions frontier. Ours concerns what happens when the laboratory is included, which turns out to dominate everything upstream.

Matbench Discovery frames MLIPs explicitly as triage tools for allocating a DFT budget, and reports a discovery acceleration factor for each model [@riebesell2025; @riebesell2025correction]. That is a cost-adjacent framing without a cost: it counts calculations saved rather than money, and stops at the DFT gate. Our Section 5.4 engages directly with the transferability of its metrics. FlowMM reports a cost per stable material in integration steps [@miller2024flowmm], which is a per-method computational cost rather than a pipeline cost.

Szymanski and Bartel compare generative and substitution-based candidate generation on stability, novelty and generation time, and establish that a simple ion-exchange baseline, built on the data-mined ionic-substitution model of Hautier and colleagues [@hautier2011substitution], outperforms several generative models [@szymanski2025baselines]. Their measurements are among our most important inputs, and our Section 5.3 restates part of their conclusion in dollars. We emphasise that this is a restatement, not an independent reproduction.

**Gap:** none of these prices the full funnel, and none includes synthesis.

### 2.2 The economics of AI-aided discovery

Agrawal, McHale and Oettl model innovation as sequential search over a combinatorial design space in which a predictive model prioritises costly tests [@agrawal2024; @agrawal2023nber]. They show that improvements in prediction fidelity raise the probability of successful innovation and shorten search, and — centrally for us — that the gains from better prediction may not be realised without corresponding investment in testing capacity.

That is our result in theoretical form. Their model is analytical and uncalibrated; it specifies the conditions under which prediction and testing are complements without saying, for any real discovery problem, how far apart the two stages actually are. Our contribution is to supply that calibration for inorganic materials: prediction is so much cheaper than testing that improving prediction cannot move the total cost, and the ratio is roughly two orders of magnitude per percentage point of improvement.

> **[FOR AUTHOR REVIEW — added overnight; neither Agrawal et al. paper has been read in full.]** The same authors have since extended the argument. Their 2026 working paper "AI in Science" [@agrawal2026aiinscience] decomposes knowledge production into a multi-stage process and argues that the returns to AI are "jagged": they differ across domains and across workflow stages, with strong returns to design aids and subtler returns elsewhere (abstract). Our result is a stage-level statement of that kind for one domain: the returns to computational improvement are concentrated in a stage that carries 1%<!--k:compute_share_lo--> to 4%<!--k:compute_share_hi--> of the cost of a validated material. We are therefore calibrating a claim they made in 2026 as well as the 2024 prioritised-search model. Two cautions before this paragraph stands: their stages are stages of knowledge production (for example question generation versus design), not the prediction-versus-testing split we price, so the mapping needs to be argued rather than asserted; and the summary here rests on the abstract alone.

We also share their caution about where returns accrue. The practical implication of their complementarity result, in our setting, is that computational improvement without synthesis investment buys very little.

### 2.3 The synthesis evidence and its contestation

The empirical base for synthesis success is thin and disputed, and this turns out to be the central fact of the paper rather than a caveat on it.

The A-Lab campaign reported realising a set of targets from computational predictions over seventeen days of autonomous operation [@szymanski2023alab]. Following publication, concerns were raised about structural identification and novelty claims, and a correction was issued [@szymanski2026correction]: the originally reported successes were re-analysed, several were found inconclusive from diffraction alone, one compound was removed, and the authors clarified that the materials were new to the prediction platform rather than necessarily new to science. Leeman and colleagues published a re-analysis of the same campaign reaching a substantially more pessimistic count, including that none of the compounds was new [@leeman2024]. Prein and colleagues report a separate, smaller campaign falling between the two [@prein2025].

Separately, large-scale generative predictions have been questioned on novelty grounds: a critique of one 380,000-structure stable set reports that a random sample of ten entries all matched known structure types, and that a substantial share contain radioactive elements [@cheetham2024]. That critique concerns novelty only; it makes no claim about synthesis as a bottleneck.

**Gap, and our position in it.** We do not adjudicate this dispute. We take the three readings as three coherent worldviews, propagate each through the cost model, and report what each implies. The resulting factor of 17<!--k:reading_factor_B--> is, we argue, the most policy-relevant number in the paper: it says that the field does not currently know what a validated material costs to within an order of magnitude, and that no amount of computational progress will tell it.

---

## 3. Model

### 3.1 The funnel

We model discovery as a funnel. A pipeline begins with a batch of candidate structures and ends with a material made in a laboratory. Each stage has a cost per candidate entering it and a pass rate; every candidate entering a stage is paid for, including those that fail. Cost per output is total spend divided by survivors at the output level in question. This is the attribution convention of the cost-per-approved-drug literature, in which the cost of failed candidates is charged to the successes [@dimasi2016].

| Pipeline | Stages |
|---|---|
| A | ion-exchange pool → drop structures already in the reference database → DFT on every candidate → synthesis |
| B | ion-exchange pool → drop known → MLIP relax-and-classify → DFT on the survivors → synthesis |
| C | generative model → drop known → MLIP → DFT → synthesis |

The ion-exchange pool is generated by data-mined ionic substitution on known prototypes, the probabilistic substitution model of Hautier and colleagues [@hautier2011substitution] as implemented in the baseline study we draw on [@szymanski2025baselines]. The reference database is the Materials Project [@jain2013mp], the MLIP is CHGNet [@deng2023chgnet], and the generative model is MatterGen [@zeni2025mattergen]. Every pipeline pays to generate its own candidates. Checking whether a structure already exists in the reference database is a lookup and is not charged.

The model is a static, order-of-magnitude estimate rather than a discounted cash-flow analysis. Techno-economic assessment frameworks for early-stage technology [@buchner2018tea] treat a static cost estimate as the appropriate method at low technology readiness, where the inputs are too uncertain for a net present value to carry information; this is why we do not compute one.

### 3.2 Three output levels

1. **Per DFT-confirmed stable material** — one candidate that DFT places on or below the convex hull, excluding verdicts expected to be wrong.
2. **Per experimentally validated material** — one material subsequently synthesised as the target phase.
3. **Per validated new material** — one such material also new to science rather than new to the prediction platform.

The second and third differ materially. The A-Lab correction states that the materials were new to the prediction platform, not necessarily new to science [@szymanski2026correction]. A model that conflates these overstates what the money bought.

### 3.3 Stage costs

**MLIP cost per candidate.** An MLIP relaxation is a sequence of ionic steps. Our benchmark finds per-step cost close to linear in cell size (log–log slope near one) and step count independent of size, ranging from 18 to 81 steps. A fraction of relaxations never converge and run to the step cap; these are charged in full and produce nothing. With *k* core-seconds per step per atom, *n* atoms, *s̄* mean steps, *q* the non-convergence fraction and *s_cap* the cap:

> cost = k · n · [(1 − q) · s̄ + q · s_cap] / 3600 core-hours

The non-convergence term deserves emphasis. In our benchmark one of three potentials failed to converge on six of seven structures when started from raw generated geometries — a failure mode invisible in the production pipeline it came from, because that pipeline always fed it pre-relaxed structures. An MLIP's effective cost is per-step cost times step count divided by convergence rate, and the third factor is rarely reported.

**DFT cost per candidate.** Modelled as a span rather than a point (Section 4.3).

**What the filter lets through.** With measured post-filter purity *P*, pool stability *π* and recall *R*, the pass fraction is π·R/P and the DFT-stable share of what passes is *P*. The alternative formulation, from a benchmark confusion matrix [@riebesell2025], gives a pass fraction of π·R + (1 − π)·FPR. Section 5.4 shows these disagree substantially; we take measured purity as primary.

**Chaining.** To obtain *N* candidates absent from the reference database, a method must generate *N* divided by its novel share. Each stage takes what the previous one released.

### 3.4 Wrong verdicts

A share *w* of DFT "stable" verdicts are wrong; our proxy is the fraction flipping to unstable under a higher level of theory [@merchant2023gnome; @an2026]. A wrong verdict is charged twice: the DFT run yields nothing, and since we cannot identify which verdicts are wrong, every DFT-stable candidate proceeds to synthesis, so that share of attempts is also wasted.

Synthesis success is therefore defined *conditional on a correct verdict*. An unconditional rate would charge the same computational failures twice. This is also why we take 38 of 54 (70%) rather than the 63% headline as the optimistic value [@szymanski2026correction]: the headline includes computational failures that the wrong-verdict term already charges.

### 3.5 Synthesis cost

No published dollar cost per solid-state synthesis attempt exists. We build it bottom-up:

> direct = XRD + furnace + labour + crucible/firings + precursor mass × price + other consumables
> per attempt = direct + tuition + indirect rate × (direct − XRD − furnace)
> per target = recipes per target × per attempt

Labour pairs a graduate trainee's stipend and fringe with trainee throughput of 10 to 20 compositions per week [CITATION NEEDED: the Liverpool manual-synthesis throughput estimate, https://pmc.ncbi.nlm.nih.gov/articles/PMC10866347/, has no bib entry yet], so person and throughput match. The labour term is a trainee's because that is who makes materials in academic laboratories, and the cost of reaching the research frontier is itself rising: the training a researcher needs before contributing has lengthened as knowledge accumulates [@jones2009burden]. Crucible cost is divided by firings survived. The reference campaign attempted roughly six recipes per target (353 for 57) [@szymanski2023alab], so each target is charged six attempts, and failed targets still pay for all of theirs.

At base an attempt costs $271<!--k:attempt-->: XRD $80<!--k:attempt_xrd_r-->, furnace $38<!--k:attempt_furnace_r-->, labour $40<!--k:attempt_labour_r-->, indirect cost $80<!--k:attempt_indirect_r-->, tuition $21<!--k:attempt_tuition_r-->, precursors $2.64<!--k:attempt_precursors-->.

### 3.6 Fixed and marginal cost

Entering a new chemistry can require computing the known phases forming the convex hull once, before any candidate can be judged. That cost is amortised over the batch's outputs and halves when the batch doubles. We set the reference-phase count to zero at base, reusing the published hull as the source experiments do, and flag the missing count as an open gap.

### 3.7 Dollars

All compute is held in core-hours and GPU-hours until a final step where a single price parameter converts it, isolating the price assumption to one line.

---

## 4. Parameters

Every parameter carries low, base and high values, a unit, a source URL, a citation key where the source is in the bibliography, and an evidence grade. Nothing is hardcoded; all model figures in this paper are generated from the parameter file and the benchmark data, and the test suite fails if a figure in the text drifts from the model.

### 4.1 Evidence grades

| Grade | Meaning |
|---|---|
| `first_hand` | Measured by us |
| `published` | Stated in the cited source |
| `figure_read` | Read by eye from a published figure |
| `derived` | Arithmetic on published numbers |
| `proxy` | A published number for a related but not identical quantity |
| `assumption` | A modelling convention with no source |
| `missing` | No source found |

Grading explicitly matters because the paper's central result is a claim about evidence quality as much as about cost.

### 4.2 First-hand measurements

We benchmarked three MLIPs [@deng2023chgnet; @batatia2025macemp; @chen2022m3gnet] and plane-wave DFT (Quantum ESPRESSO [@giannozzi2009qe; @giannozzi2017qe] with GBRV pseudopotentials [@garrity2014gbrv]) on seven structures spanning 10 to 56 atoms, with repeats, a thread-count sweep and documented protocols. Relaxations were driven through ASE [@larsen2017ase].

Two findings bear on the model. First, single-threaded execution is the cost-minimising configuration: core-hours are allocated cores times wall time, and on our platform twelve threads cost 32 to 90 times the core-hours of one. Second, per-model MLIP relaxation timings do not appear to be published, so these measurements fill a gap.

Our hardware is unusual — an ARM64 laptop under virtualisation — and we report it as such. DFT timings carry a platform artefact: a twelve-rank configuration cost 2.6 to 7.3 times the core-hours of a four-rank one, with the penalty largest for the smallest cell. All DFT figures therefore use four ranks, with twelve-rank values retained as documented upper bounds. For a controlled scaling measurement we compare a 28-atom cell against its own 56-atom supercell, identical in chemistry and pseudopotentials: 0.480 against 3.842 core-hours, a factor of 8.0, an exponent of 3.0.

### 4.3 DFT cost: a span, not a point

DFT cost per candidate is modelled as a span from 3 to 1,000 core-hours:

- **Low, 2.98 core-hours:** our measurement.
- **High, 1,000 core-hours:** a large public database project circa 2012, being one to five calculations per material at roughly 200 CPU-hours each with a 10 to 20% failure-and-rerun rate, on decade-old hardware [CITATION NEEDED: Materials Project NERSC user-day slides, https://www.nersc.gov/assets/Uploads/NERSCuserday-jain.pdf, have no bib entry; a citable Materials Project source for per-calculation CPU-hours would be better].
- **Base, 54.5 core-hours:** the geometric midpoint, a convention rather than a measurement. The Monte Carlo samples the span log-uniformly.

We report results across the span. The useful statement is that the conclusion holds at every point in it.

### 4.4 The contested parameter

| Reading | Success | Standing |
|---|---|---|
| Optimistic [@szymanski2023alab; @szymanski2026correction] | 38 of 54 (70%) | Peer-reviewed, 57 targets |
| Middle [@prein2025] | 7 of 16 (44%) | Preprint, no venue listed, 16 targets |
| Pessimistic [@leeman2024] | 3 of 58 (5%) | Peer-reviewed re-analysis of the first campaign |

The first and third read the *same experiment* and disagree about what was made. The second is a separate, smaller campaign between them.

Synthesis success, novelty and the wrong-verdict share all come from these same re-analyses, so they are not independent. The Monte Carlo draws one reading per sample and takes all three from it; independent sampling would generate combinations corresponding to no coherent reading of the evidence. Recipes per target are drawn jointly too, since failed targets consume more of the recipe budget.

### 4.5 Accounting choices

Institutional overhead is the largest single accounting choice in synthesis cost, and synthesis is 96%<!--k:span_base_share_lo--> to 99%<!--k:span_base_share_hi--> of the level-2 figure. Two choices are involved: the rate, and the base it is charged on.

**The rate.** We use the *effective* indirect cost recovery rate, 42%<!--k:indirect_rate-->: the average that NIH actually pays across more than 350 grantee institutions [@azoulay2025icr]. The same study puts the average *negotiated* rate at 45%<!--k:indirect_rate_high-->, the ceiling an institution may charge; applying it would overstate indirect cost by about a third, raising the attempt cost to $276<!--k:attempt_at_negotiated--> and level 2 for pipeline B by 2%<!--k:negotiated_l2_rise_pct--> to $3,948<!--k:l2_B_at_negotiated-->. The negotiated rate is our high value and the low end of the typical effective range, 25%<!--k:indirect_rate_low-->, our low. Two caveats: the data are NIH indirect-cost records, covering universities, independent hospitals and research institutes, not a census of US universities; and the effective rate is measured against total direct costs, a wider base than the one we charge it on, so 42% leans low.

**The base.**

| Basis | $ per attempt | Level 2: A / B / C |
|---|---|---|
| Direct costs only | $191<!--k:basis_bench_attempt--> | $2,758<!--k:basis_bench_l2_A--> / $2,734<!--k:basis_bench_l2_B--> / $2,845<!--k:basis_bench_l2_C--> |
| Overhead, service fees outside the base (default) | $271<!--k:basis_funder_attempt--> | $3,891<!--k:basis_funder_l2_A--> / $3,868<!--k:basis_funder_l2_B--> / $3,978<!--k:basis_funder_l2_C--> |
| Overhead, service fees inside the base | $271<!--k:basis_funder_fees_in_attempt--> | $3,891<!--k:basis_funder_fees_in_l2_A--> / $3,868<!--k:basis_funder_fees_in_l2_B--> / $3,978<!--k:basis_funder_fees_in_l2_C--> |

We default to including overhead because the question is the resource cost of a validated material, which a funder bears. We exclude service-centre fees from the overhead base because federal rules require recharge rates to consist of direct costs and an allocable share of indirect costs [@cfr200468], so charging institutional overhead on top counts it twice. Practice varies and a reviewer may reject this.

---

## 5. Results

### 5.1 Base case

| Output | A | B | C |
|---|---|---|---|
| 1. per DFT-confirmed stable material | $31.48<!--k:l1_A--> | $19.05<!--k:l1_B--> | $76.61<!--k:l1_C--> |
| 2. per experimentally validated material | $3,891<!--k:l2_A--> | $3,868<!--k:l2_B--> | $3,978<!--k:l2_C--> |
| — of which compute | $60.44<!--k:l2_compute_A--> | $36.58<!--k:l2_compute_B--> | $147<!--k:l2_compute_C--> |
| — of which synthesis | $3,831<!--k:l2_synthesis_A--> | $3,831<!--k:l2_synthesis_B--> | $3,831<!--k:l2_synthesis_C--> |

The synthesis term is identical across pipelines. This is structural, not coincidental.

### 5.2 An MLIP pre-filter cuts DFT cost by about 40%, not several-fold

Pipeline B costs $19.05<!--k:l1_B--> per DFT-confirmed stable material against A's $31.48<!--k:l1_A-->, a ratio of 1.65<!--k:l1_ratio_A_B-->, so B is 39%<!--k:l1_B_cheaper_pct--> cheaper. The filter saves money because DFT then runs on a pool that is 15.2% stable rather than 9.2%. The relaxations themselves cost about three cents.

**An earlier version of this analysis reported a fourfold benefit, and the correction is worth reporting because the error is easy to repeat.** That version took classification rates from a benchmark measured on one candidate distribution [@riebesell2025] and applied them to a differently constructed pool. Those rates predict that 37% of filter-passed candidates are DFT-stable; direct measurement on the actual pool gives 15.2% [@szymanski2025baselines]. Substituting the measured value more than halves the estimated benefit.

### 5.3 A generative pool costs about four times as much, through purity at the DFT gate

Pipeline C costs $76.61<!--k:l1_C--> per DFT-confirmed stable material against B's $19.05<!--k:l1_B-->. Both run the same filter-then-DFT funnel; what differs is what reaches DFT. After filtering, 15.2% of ion-exchange candidates are DFT-stable against 3.8% of generated ones [@szymanski2025baselines]. DFT spend per stable hit is DFT cost divided by purity, so the ratio is approximately 15.2/3.8. Generation cost plays no part: the generative model's GPU time is 0.5% of C's compute spend.

Two qualifications. This is not an independent reproduction of the source experiment's conclusion, because the model takes that experiment's measurements as inputs; it restates them in dollars. And its magnitude rests on a value read from a supplementary figure rather than printed as a number. Across that value's plausible range the ratio spans 2.2 to 6.7, though its direction never reverses.

### 5.4 Filter enrichment on realistic pools is half what the benchmark reports

The discovery acceleration factor is the ratio of a filter's precision to its pool's prevalence — how many times more often a filter-passed candidate is stable than a random one. The benchmark defines it this way [@riebesell2025], so the comparison requires no assumption about which classifier rate transfers.

| Pool | Stable fraction | Purity after filter | DAF |
|---|---|---|---|
| Benchmark test set | 15.3% | — | 3.36 |
| Ion-exchange pool | 9.2% | 15.2% | **1.65** |
| Generative pool | 3.0% | 3.8% | **1.27** |

On a realistically constructed ion-exchange pool, enrichment is 1.65 against the 3.36 reported. On the generative pool it is 1.27: the filter barely enriches at all. Because the acceleration factor depends on prevalence, applying the benchmark's own rates at each pool's prevalence gives the like-for-like comparison, 1.65 against 4.01 — a larger gap still.

The mechanism, which rests on an assumption, is that if the benchmark's recall transfers, measured purity implies a false-positive rate of 0.43 on the ion-exchange pool against 0.13 on the benchmark. The alternative attribution requires recall to collapse to 0.23, which is implausible. The acceleration-factor result does not depend on this attribution.

**Two explanations, one unresolved.** Distribution shift is weak: the benchmark's test set was itself built by chemical-similarity elemental substitution from the same database, the same construction as ion exchange. The competing explanation is definitional. The two studies judge stability against different convex hulls — one against the database hull alone, explicitly rejecting a joint hull, the other against a newer snapshot plus the generated candidates, close to the formulation the first rejects. A stricter hull lowers both prevalence and the passed-candidate stable share, so part of the gap may be definitional. Public data can resolve this by recomputing the benchmark's acceleration factor against the joint hull. Until then the gap is a measured fact with an open cause. (The benchmark's published version carries an Author Correction that revised figures, a table and the supplementary information [@riebesell2025correction]; the values used here should be checked against the corrected version.)

### 5.5 Pipeline choice is immaterial once synthesis is included

At base DFT cost the pipelines are 1.03<!--k:l2_spread_base-->× apart at level 2; at the top of the span, 1.45<!--k:l2_spread_high-->×. The near-equality is structural. Level-2 cost is

> compute per DFT-confirmed stable / success + recipes × cost per attempt / ((1 − w) × success)

and the second term contains no pipeline-dependent quantity. Every DFT-stable verdict proceeds to synthesis; the wrong-verdict share, success rate, recipes per target and cost per attempt are identical however the candidate was found. We verify this across every parameter level and configuration.

| DFT core-h | Level 1: A / B / C | Level 2: A / B / C | Spread | Synthesis share |
|---|---|---|---|---|
| 2.975 | $1.72<!--k:span_low_l1_A--> / $1.04<!--k:span_low_l1_B--> / $4.56<!--k:span_low_l1_C--> | $3,834<!--k:span_low_l2_A--> / $3,833<!--k:span_low_l2_B--> / $3,840<!--k:span_low_l2_C--> | 1.00<!--k:span_low_spread-->× | 100%<!--k:span_low_share--> |
| 54.5 | $31.48<!--k:span_base_l1_A--> / $19.05<!--k:span_base_l1_B--> / $76.61<!--k:span_base_l1_C--> | $3,891<!--k:span_base_l2_A--> / $3,868<!--k:span_base_l2_B--> / $3,978<!--k:span_base_l2_C--> | 1.03<!--k:span_base_spread-->× | 96%<!--k:span_base_share_lo-->–99%<!--k:span_base_share_hi--> |
| 1,000 | $577<!--k:span_high_l1_A--> / $349<!--k:span_high_l1_B--> / $1,398<!--k:span_high_l1_C--> | $4,939<!--k:span_high_l2_A--> / $4,502<!--k:span_high_l2_B--> / $6,514<!--k:span_high_l2_C--> | 1.45<!--k:span_high_spread-->× | 59%<!--k:span_high_share_lo-->–85%<!--k:span_high_share_hi--> |

**The 1.03<!--k:l2_spread_base-->× is a lower bound.** It assumes synthesis success does not depend on how a candidate was found, and that assumption has a likely direction: MLIPs are trained on databases dominated by materials that have actually been made, so a pre-filter plausibly favours candidates that are *more* synthesisable. If so the true spread is wider. Section 7 treats this as the primary threat to validity.

### 5.6 Under uncertainty: ordered but immaterial

Across 20,000<!--k:mc_draws--> draws respecting the documented correlations, with pipelines compared pairwise within each draw:

| Level | P(B < A) | P(differ > 10%) | Overlap of marginals |
|---|---|---|---|
| 1 | 99.4%<!--k:kill_l1_p_B_lt_A--> | 98%<!--k:kill_l1_material_BA--> | 89%<!--k:kill_l1_overlap_BA--> |
| 2 | 99.4%<!--k:kill_l2_p_B_lt_A--> | 1%<!--k:kill_l2_material_BA--> | 99%<!--k:kill_l2_overlap_BA--> |
| 3 | 99.4%<!--k:kill_l3_p_B_lt_A--> | 1%<!--k:kill_l3_material_BA--> | 99%<!--k:kill_l3_overlap_BA--> |

At level 1 the pipelines separate. At level 2 the ordering survives draw by draw — B is cheaper in 99.4%<!--k:kill_l2_p_B_lt_A--> of worlds, because the synthesis term is shared and the compute term is not — but the difference exceeds 10% in only 1%<!--k:kill_l2_material_BA--> of draws. We call this *ordered but immaterial*.

The marginal distributions overlap heavily at every level, including level 1. Absolute cost is dominated by uncertainty all pipelines share. Only the paired comparison separates them, and only at level 1.

### 5.7 The answer depends on which reading is right

| Reading | Level 2, pipeline B (90% interval) |
|---|---|
| Optimistic | $2,975<!--k:reading_optimistic_alab_B--> ($2,000–$4,379<!--k:reading_optimistic_alab_B_interval-->) |
| Middle | $5,008<!--k:reading_middle_prein_B--> ($2,724–$10,109<!--k:reading_middle_prein_B_interval-->) |
| Pessimistic | $49,917<!--k:reading_pessimistic_leeman_B--> ($21,013–$149,247<!--k:reading_pessimistic_leeman_B_interval-->) |

Between the extremes that is a factor of 17<!--k:reading_factor_B-->. Within any one reading, pipeline choice moves the median by at most 1.07<!--k:within_reading_max-->×.

**This factor of 17<!--k:reading_factor_B--> is not measurement uncertainty.** Two of the three readings interpret the same experiment and disagree about what was made. No reanalysis of existing data closes the gap; it requires new synthesis campaigns with phase identification both sides accept.

Where a single number is unavoidable we quote the middle reading with the spread beside it, and note that the middle reading is the least established of the three.

### 5.8 Marginal returns

We report log-elasticity: the percentage fall in cost per 1% improvement in a lever, scale-free so levers in different units compare directly.

| Lever | A | B | C |
|---|---|---|---|
| Synthesis success rate | 1.000<!--k:el_success_A--> | 1.000<!--k:el_success_B--> | 1.000<!--k:el_success_C--> |
| Recipes per target | 0.984<!--k:el_recipes_A--> | 0.991<!--k:el_recipes_B--> | 0.963<!--k:el_recipes_C--> |
| Cost per synthesis attempt | 0.984<!--k:el_attempt_A--> | 0.991<!--k:el_attempt_B--> | 0.963<!--k:el_attempt_C--> |
| Best compute lever | 0.016<!--k:el_compute_A--> | 0.009<!--k:el_compute_B--> | 0.037<!--k:el_compute_C--> |

**The synthesis levers are tied at unit elasticity and should not be ranked against each other.** Level-2 synthesis cost is recipes times cost per attempt divided by success, so each has elasticity one by construction. Success is exactly one because it also divides the compute term; the other two equal the synthesis share of total cost, and the small gap between them *is* the compute share rather than a difference in leverage.

The finding is the magnitude gap: per percentage point, synthesis levers are worth 26<!--k:returns_ratio_lo--> to 136<!--k:returns_ratio_hi--> times the best computational lever.

**One lever's cost is known, and it is zero.** Switching from on-demand to spot compute pricing is a 62%<!--k:spot_cpu_discount--> discount available today at no research cost. It changes cost per validated material by 0.6%<!--k:spot_lo--> to 2.3%<!--k:spot_hi-->. The levers worth up to two orders of magnitude more all require synthesis research whose cost nobody has measured. Ranking returns per dollar rather than per percentage point would need those costs; we observe only that the free lever is the negligible one.

### 5.9 Break-evens

**The filter's fixed cost is a non-result.** There is no batch size at which it fails to pay for itself: loading the potential costs 0.00024<!--k:fixed_extra_core_h--> core-hours and the filter saves 29.5<!--k:fixed_saving_core_h--> core-hours per candidate. The informative quantity is the per-candidate saving — any additional fixed cost of X core-hours, such as fine-tuning, repays after X/29.5<!--k:fixed_saving_core_h--> candidates.

**Synthesis cost at which compute begins to matter.** Taking "matters" as compute reaching 10% of level-2 cost: at base DFT cost, attempt cost would have to fall from $271<!--k:attempt--> to between $23.26<!--k:threshold_lo--> and $93.52<!--k:threshold_hi--> depending on pipeline. At the top of the DFT span compute already matters at today's attempt cost.

**Generative-pool parity.** C matches B at level 1 when filter purity on the generative pool reaches 15.5%<!--k:parity_purity-->, 4.1<!--k:parity_ratio--> times the measured value.

**How strong would a synthesisability effect have to be?** For pipeline choice to double level-2 cost, an MLIP pre-filter would have to raise synthesis success from 44%<!--k:mult_2x_success_from--> to 87%<!--k:mult_2x_success_to--> — above the optimistic reading's own figure. This specifies how large an effect the follow-up study would need to detect.

### 5.10 Where the evidence is weakest

One-at-a-time sensitivity is dominated by a single parameter at each level: DFT cost at level 1 (99.8%<!--k:tornado_l1_share--> of variance) and synthesis success at level 2 (98.6%<!--k:tornado_l2_share-->). These dominate because they have the widest ranges, not because cost responds most strongly to them. **The tornado maps where the evidence is weakest rather than where the leverage is.** The two quantities most in need of better measurement are DFT cost on modern hardware and synthesis success from independent campaigns.

---

## 6. Discussion

### 6.1 For research groups

The choice between computational pipelines is, in cost terms, a choice about a line item worth 1%<!--k:compute_share_lo--> to 4%<!--k:compute_share_hi--> of the total. A group that intends to take candidates into the laboratory should optimise the laboratory. A group that stops at computational screening faces a real and substantial choice — the pipelines differ by a factor of four at that stage — but should not describe that choice as affecting the cost of discovering a material, because it does not.

Our results also suggest two specific practices. Report an MLIP's convergence rate alongside its accuracy, because a potential that fails to converge on most structures from a cold start has an effective cost unrelated to its per-step speed. And run screening single-threaded across many structures rather than multi-threaded on one, which on our platform was the difference between one core-hour and eighty.

### 6.2 For funders

The next dollar of improvement goes to synthesis, by between one and two orders of magnitude. That is the paper's clearest practical conclusion and it is robust across every parameter configuration we tested.

But the more valuable expenditure may be one the model cannot price. The factor of 17<!--k:reading_factor_B--> between readings of the synthesis evidence exceeds every methodological difference in the paper combined. Funding independent synthesis campaigns with phase identification that both sides of the current dispute would accept would do more to establish what materials discovery costs than any improvement to the discovery methods themselves. At present the field does not know this number to within an order of magnitude.

### 6.3 For autonomous laboratory programmes

We could not find published capital or operating cost for any autonomous solid-state synthesis platform. The one capital figure we located for a comparable system is a press statement [CITATION NEEDED: the press figure, https://mse.engin.umich.edu/about/news/better-battery-manufacturing-robotic-lab-vets-new-reaction-design-strategy, has no bib entry]. Component costs are published for some self-driving laboratories in other domains, from a few thousand to over a hundred thousand dollars [@lo2024frugal; @pilon2026], but none of these is a solid-state powder platform. This is a striking gap: these platforms are justified on economic grounds — they make materials faster and therefore cheaper — and the cost side of that argument is not in the literature.

Our model suggests the relevant metric is cost per validated material rather than samples per day, since throughput claims and cost claims diverge sharply. The press figure for one platform is 100 to 200 samples per day [CITATION NEEDED: Berkeley Lab news release, https://newscenter.lbl.gov/2023/04/17/meet-the-autonomous-lab-of-the-future/, has no bib entry]; its own software paper reports just over 2,500 samples in about a year [@fei2024alabos]. A programme reporting cost per validated material, with its capital amortisation stated, would be able to make its economic case directly.

### 6.4 For benchmark design

Our Section 5.4 result is addressed to a different literature than the rest of the paper. A standard benchmark's acceleration factor overstates enrichment on realistically constructed candidate pools by roughly a factor of two, and possibly more on generative pools. Part of this may be definitional rather than a weakness of the models, and we specify the experiment that would settle it. Until it is settled, practitioners using benchmark classification rates to plan a DFT budget should expect to overestimate what filtering saves — as we did, by more than a factor of two, until we substituted direct measurements.

### 6.5 For investors and the public account of AI in science

Claims that AI accelerates materials discovery by one or two orders of magnitude are, on our accounting, claims about a stage representing 1%<!--k:compute_share_lo--> to 4%<!--k:compute_share_hi--> of the cost of producing a validated material. They may well be true as stated. They do not imply a comparable reduction in the cost of discovery, and the gap between the two statements is where most of the money is. The same caution applies to output measures more generally: large language models have measurably raised the volume of scientific writing [@kusumegi2025], and volume of output is not the cost of a validated result.

---

## 7. Limitations

1. **Primary threat to validity: synthesis success is assumed independent of pipeline.** No source we found measures this. The expected direction makes the 1.03<!--k:l2_spread_base-->× spread a lower bound. The follow-up study is to attempt matched sets of filtered and unfiltered DFT-stable candidates and compare success rates.
2. **Filter recall is not measured on these pools.** Measured purity and benchmark recall come from different sources and cannot both be exactly right.
3. **The generative-pool result's magnitude depends on a figure-read value.** Across its range the ratio spans 2.2 to 6.7; the direction does not change.
4. **Overhead treatment is an accounting choice** moving level 2 by 41%<!--k:basis_move_pct--> between extreme variants, though not the spread. The rate is the effective indirect cost recovery rate from NIH records [@azoulay2025icr], not a census of universities.
5. **Level 3 rests on one disputed count** of zero of 36 and is reported only as a lower bound. At the observed share of zero the cost is unbounded.
6. **DFT cost spans more than two orders of magnitude.** Results are reported across the span.
7. **The wrong-verdict share is a proxy** — flips under a higher level of theory, not failures against experiment.
8. **Precursor mass per attempt is unsourced** for the autonomous-laboratory case.
9. **Monte Carlo choices shape the distribution.** The three readings receive equal weight, an assumption with no basis; named scenarios are reported so readers can apply their own. The level-2 95th percentile is a statement about whose re-analysis to believe and falls from about $94,000<!--k:mc_l2_B_p95_thousands--> to $8,507<!--k:mc_l2_B_p95_no_leeman--> if the pessimistic reading is given zero weight.
10. **The enrichment gap has an unresolved competing explanation:** the two studies judge stability against different convex hulls.
11. **Our hardware is unusual.** An ARM64 laptop under virtualisation produced two platform artefacts that we document and correct for; the DFT timings should not be generalised to server hardware.
12. **Facility recharge rates understate true resource cost.** User-fee income alone does not fully support most shared instrumentation facilities [@strom2020], so the XRD and furnace fees we use, which are recharge rates, are lower bounds on the resources an attempt consumes. Our synthesis cost is therefore conservative. A higher synthesis cost widens the gap between synthesis and compute, so this strengthens the conclusion rather than weakening it.

---

## 8. The released model

The complete model, every parameter with its source, citation and evidence grade, the first-hand benchmark data, the analysis code and the test suite are released as a replication package. Every model figure in this paper is generated from the parameter file; none is typed by hand, and the test suite fails if a figure in the text drifts from the model.

The model is a pure function from parameters to results, so a reader who disagrees with a parameter can substitute their own and rerun. We expect disagreement about several — the overhead treatment, the weighting of the three readings, the DFT cost span — and the package is structured so that each takes one edit.

---

## 9. Conclusion

The field's standard claim that synthesis is the bottleneck in AI-driven materials discovery is correct, and we can now say by how much: per percentage point of improvement, synthesis levers are worth between 26<!--k:returns_ratio_lo--> and 136<!--k:returns_ratio_hi--> times the best computational lever, and the single compute improvement available at zero cost moves the total by under 3%.

The consequence is that the choice between computational pipelines, which the field treats as consequential, is economically immaterial once the laboratory is included. An MLIP pre-filter cuts computational cost by 39%<!--k:l1_B_cheaper_pct--> and a generative candidate pool costs four times an ion-exchange one at the DFT gate, yet all three pipelines deliver a validated material within 3%<!--k:l2_spread_base_pct--> of the same price.

What does govern the price is a number the field does not currently know. Three groups read the synthesis evidence three ways, producing cost estimates spanning a factor of 17<!--k:reading_factor_B-->, and two of those readings interpret the same experiment. Closing that gap requires new synthesis data, not better analysis and not better models. Until it closes, statements about what AI-driven materials discovery costs are statements about which re-analysis one believes.

---

## Disclosures

**AI assistance.** This paper was written with substantial assistance from a large language model. The author directed the research, ran and debugged all computational work, verified the results, and takes full responsibility for the content. Drafting, literature search, and methodological review were AI-assisted.

**Conflict of interest.** The author is the founder of a company working in AI-driven materials science. The computational pipeline used for the first-hand benchmarks in Section 4.2 derives from that company's codebase, though the released replication package depends on no proprietary code.

**Data and code availability.** [Repository URL and archived DOI to be inserted on release.]

---

---

# NOTES — not part of the paper

## Citations inserted overnight that are not fully verified

Every key below resolves in `paper/references.bib`, and its bibliographic fields were checked against the Crossref record (or the NBER page). What is NOT verified is that the source says what the sentence uses it for: none of these papers was read in full overnight. Check each before submission.

- **§1, [@scannell2012eroom]** as the closest precedent ("screening efficiency rose while R&D output per dollar fell, because cost sits downstream"). This is my summary of the paper's well-known argument, not checked against its text.
- **§1, [@bloom2020ideas]** (falling research productivity) and **[@cockburn2018]** (AI as a general-purpose "method of invention"): standard readings of both, not checked against the text.
- **§1, [@montoya2024; @chung2025synthesizability; @aziz2021]** for "synthesis is the bottleneck". Titles verified; that each paper makes the bottleneck claim in so many words is not.
- **§1, [@zeni2025mattergen]** for "thousands of candidates an hour": the claim may not be supported (see the CITATION NEEDED next to it).
- **§2.1, [@walker2026carbon]**: the bib entry is new (Materials Horizons 13(4), 1993-2004, 2026; first author Matthew Walker). The characterisation in §2.1 still comes from abstracts and search extracts (your original note).
- **§2.2, [@agrawal2024; @agrawal2023nber]** and the new **[@agrawal2026aiinscience]** paragraph: from abstracts only. Marked FOR AUTHOR REVIEW in the text.
- **§3.1, [@dimasi2016]** as the precedent for funnel attribution (cost of failures charged to successes). Standard reading, not checked against the text.
- **§3.1, [@buchner2018tea]** as licensing a static order-of-magnitude estimate at low TRL and explaining why we compute no NPV. Taken from the brief and the bib note, not from the paper's text.
- **§3.5, [@jones2009burden]** at the labour term. The link (rising training burden → who does the synthesis) is my framing; check that it reads as intended.
- **§6.3, [@lo2024frugal; @pilon2026]** for SDL component costs. Pilon's US$5,000 and US$50,000 were verified in the paper's own introduction (the US$50,000 is the earlier RoboChem platform). The "few thousand to over a hundred thousand" range rests on Pilon's text; Lo et al.'s "50 USD to 40M USD" range came from a web-fetch summary.
- **§6.5, [@kusumegi2025]**: "LLMs measurably raised the volume of scientific writing" is a reading of the title and venue, not of the text. The year is 2025, not 2026.
- **§7.12, [@strom2020]**: the bibliographic record is verified, but the claim that user-fee income alone does not fully support most facilities was NOT checked against the article text (Springer blocked every fetch).
- **§4.5, [@azoulay2025icr]**: verified against the paper's PDF (abstract; Table 1; section 3.3).

## Places marked CITATION NEEDED

- §1: "thousands of candidates an hour".
- §3.5: Liverpool trainee-throughput estimate (source URL known; no bib entry).
- §4.3: Materials Project 2012 CPU-hours (NERSC slides; no bib entry).
- §6.3: autonomous-lab capital press figure; A-Lab press throughput figure (URLs known; no bib entries).

## What I could not do properly

**Related work (Section 2) is written from abstracts and search extracts, not full reads.** I have not read Walker & Butler or Agrawal, McHale & Oettl end to end. The *shape* of the positioning is right — same structure different unit; theory versus calibration — but the specifics may be wrong, and this is the section a reviewer probes first. Read both, then rewrite §2.1 and §2.2 yourself. If my characterisation of either is wrong, the contribution claims in §1 need revising too.

**Numbers unverified by eye.** Everything from the parameter tables. Assume errors until checked.

## Decisions you should examine

1. **Three readings as the headline** rather than a point estimate. The biggest framing call in the paper.
2. **§5.2 names your own earlier error explicitly.** Honest and useful; it also advertises a mistake. I think it earns its place.
3. **§5.4 as a named finding** rather than a footnote. It is arguably a contribution to a different literature.
4. **§6.5 on investor claims** is the most pointed thing in the paper. It is defensible from your results but it is a claim about other people's rhetoric. Decide if you want it.
5. **Title.** Alternatives: "The Price of a Validated Material"; "Where the Money Goes in AI-Driven Materials Discovery".
6. **JEL codes and keywords** are my guesses. Check them against SSRN's categories.

## Format

Markdown, so you can rewrite fast. `pandoc --citeproc --bibliography references.bib -o paper.tex p1-full-draft.md` converts it, citations included, when you're ready for Overleaf. The `<!--k:...-->` tags are HTML comments and do not appear in the output.
