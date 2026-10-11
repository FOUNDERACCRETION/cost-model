# P1 parameter table: compute, MLIP, generation, label reliability, novelty (hunt of 2026-10-09)

Status: first pass. Numbers were read through a web-fetch summary, not by eye. Check each at the URL before it enters the paper. "Derived" = arithmetic done during the hunt, not stated in the source.


**Published versions (added 2026-10-10).** Several sources below were read as preprints and have since been published.
The URLs are kept as the record of what was read; cite the bib key in `paper/references.bib`, which is the single
source of bibliographic truth:

| Read as | Published as | Bib key |
|---|---|---|
| arXiv 2501.02144 (Szymanski & Bartel) | Materials Horizons 12(19), 8000-8011 (2025) | `szymanski2025baselines` |
| arXiv 2401.00096 (MACE-MP-0) | J. Chem. Phys. 163(18), 184110 (2025) | `batatia2025macemp` |
| arXiv 2405.13930 (AlabOS) | Digital Discovery 3(11), 2275-2288 (2024) | `fei2024alabos` |
| arXiv 2401.04070 (Chen et al.) | J. Am. Chem. Soc. 146(29), 20009-20018 (2024); title says "Machine Learning" | `chen2024jacs` |
| arXiv 2308.14920 (Matbench Discovery) | Nat. Mach. Intell. 7(6), 836-847 (2025), title without the "Matbench Discovery --" prefix; Author Correction 7(9), 1586 (2025), revising figures, a table and the SI | `riebesell2025`, `riebesell2025correction` |
| arXiv 2410.12771 (OMat24) | Nat. Comput. Sci. 6(6), 642-652 (2026) | `barrosoluque2026omat24` |
| arXiv 2406.04713 (FlowMM) | ICML 2024, PMLR 235, 35664-35686 | `miller2024flowmm` |
| A-Lab, "...synthesis of novel materials" | Title now "...synthesis of inorganic materials" (changed with the 2026 correction) | `szymanski2023alab`, `szymanski2026correction` |
| Leeman et al. preprint, "...Material Prediction..." | PRX Energy 3(1), 011002 (2024), "...Inorganic Materials Prediction..." (plural) | `leeman2024` |

Cheetham & Seshadri (`cheetham2024`) is a novelty critique of GNoME. It makes no synthesis-bottleneck claim; cite it
for novelty only. The synthesis-bottleneck citations are `montoya2024` (primary), `chung2025synthesizability` and
`aziz2021`. The ion-exchange pool implements the probabilistic substitution model of `hautier2011substitution`.

## 1. DFT cost per calculation

| Item | Value | Source URL | Caveats |
|---|---|---|---|
| Materials Project, early GGA runs | ~200 CPU-h per calculation, 1-5 calculations per material (derived 200-1,000 CPU-h per material); 10-20% of jobs fail and rerun | https://www.nersc.gov/assets/Uploads/NERSCuserday-jain.pdf | Slides, ~2012 hardware |
| Materials Project totals | ~8M CPU-h for >80,000 compounds (derived ~100 CPU-h per compound) | https://perssongroup.lbl.gov/papers/scc2012-materialsproject.pdf | Assumes totals cover same work |
| OMat24 | 400M+ core-h for ~118M labelled structures (derived ~3.4 core-h per structure) | https://arxiv.org/html/2410.12771v1 | Per frame, not per relaxation |
| OC20 | relaxation cap 144 h on 12 cores (derived 1,728 core-h) | https://arxiv.org/pdf/2010.09990v4 | Slabs, not bulk; conflicting cutoff figure, check text |
| r2SCAN vs GGA | 2-4x PBEsol, ~4x PBE | https://perssongroup.lbl.gov/papers/kingsbury_performance_comparison_2021.pdf | Relative only |
| AFLOW ~1,170 CPU-h for ~50 atoms | UNVERIFIED. arXiv 1811.08464 is the Oses thesis; figure not seen on fetched pages | https://arxiv.org/abs/1811.08464 | Open the PDF and find it, or drop it |

## 2. Compute prices (Oct 2026; per-unit prices derived from instance price / count)

| Item | On-demand | Spot | Source URL |
|---|---|---|---|
| AWS c7i.48xlarge | 0.0446 $/vCPU-h | 0.0170 | https://instances.vantage.sh/aws/ec2/c7i.48xlarge |
| AWS c7a.48xlarge | 0.0513 | 0.0177 | https://instances.vantage.sh/aws/ec2/c7a.48xlarge |
| AWS c6i.32xlarge | 0.0425 | 0.0175 | https://instances.vantage.sh/aws/ec2/c6i.32xlarge |
| AWS hpc7a.96xlarge | 0.0473 | none | https://instances.vantage.sh/aws/ec2/hpc7a.96xlarge |
| AWS hpc6a.48xlarge | 0.0346 | none | https://instances.vantage.sh/aws/ec2/hpc6a.48xlarge |
| Azure HB176rs v4 | 0.0409 $/core-h | 0.0076 | https://instances.vantage.sh/azure/vm/hb176rs-v4 |
| Azure HB120rs v3 | 0.030 | 0.0055 | https://instances.vantage.sh/azure/vm/hb120rs-v3 |
| GCP c3-standard-88 | 0.0504 $/vCPU-h | 0.0060-0.0173 | https://gcloud-compute.com/c3-standard-88.html |
| GCP h3-standard-88 | 0.0559 | none | https://gcloud-compute.com/h3-standard-88.html |
| AWS T4 (g4dn.xlarge) | 0.526 $/GPU-h | 0.289 | https://instances.vantage.sh/aws/ec2/g4dn.xlarge |
| AWS L4 (g6.xlarge) | 0.805 | 0.593 | https://instances.vantage.sh/aws/ec2/g6.xlarge |
| AWS A10G (g5.xlarge) | 1.006 | 0.487 | https://instances.vantage.sh/aws/ec2/g5.xlarge |
| AWS A100 (p4d, per GPU) | 2.74 | 2.32 | https://instances.vantage.sh/aws/ec2/p4d.24xlarge |
| AWS H100 (p5, per GPU) | 6.88 | 3.95 | https://instances.vantage.sh/aws/ec2/p5.48xlarge |
| Lambda | H100 3.99; A100-80GB 2.79; A100-40GB 1.99 | - | https://lambda.ai/pricing |
| ARCHER2 (notional) | GBP 0.0016-0.0030 per core-h | - | https://www.archer2.ac.uk/support-access/cu-calc.html |
| UF HiPerGator (subsidised) | $0.0050 internal / $0.0102 external per core-h | - | https://it.ufl.edu/rc/get-started/price-list |

Aggregator pages (Vantage, gcloud-compute.com) are secondary; cite the providers' own price pages in the paper. vCPU vs physical core not confirmed except Azure HB.

## 3. MLIP accuracy (Matbench Discovery, unique-prototype WBM set, 15.3% stable)

| Model | F1 | Precision | DAF | Top-10k precision |
|---|---|---|---|---|
| M3GNet | 0.569 | 0.441 | 2.882 | 0.767 |
| CHGNet | 0.613 | 0.514 | 3.361 | 0.851 |
| MACE-MP-0 | 0.669 | 0.577 | 3.777 | 0.798 |
| EquiformerV2+DeNS (MPtrj) | 0.815 | 0.771 | 5.042 | 0.967 |
| eSEN-30M-OAM | 0.925 | 0.928 | 6.069 | - |
| PET-OAM-XL | 0.924 | 0.929 | 6.075 | - |

Sources: https://matbench-discovery.materialsproject.org/ and https://arxiv.org/abs/2308.14920 (Tables 1, S1, S2). Recall only found for 2023 versions (CHGNet 0.66, M3GNet 0.77, MACE 0.72): https://arxiv.org/html/2308.14920v1

MLIP run time: NOT PUBLISHED per model. Only qualitative ("within seconds"). First-hand benchmark fills this gap.

## 4. Generative and substitution yield

Szymanski & Bartel 2025 (https://arxiv.org/pdf/2501.02144), DFT-checked, 500 per method:

| Method | Stable, strict (<=0 vs MP hull) | Stable, <=100 meV/atom | Novel vs MP+Alexandria+ICSD | After CHGNet filter (strict) | Gen. time s/structure |
|---|---|---|---|---|---|
| Random | 1.4% | 8.2% | 94.0% | 7.6% | 0.14 |
| Ion exchange | 9.2% | 58.4% | 62.8% | 15.2% | 3.45 |
| CrystaLLM | 2.4% | 12.8% | 85.0% | 17.0% | 38.27 |
| CDVAE | 1.8% | 11.2% | 92.0% | 3.8-8.8% | 14.32 |
| FTCP | 2.0% | 20.0% | 35.0% | 22.4% | 0.03 |
| MatterGen | 3.0% (5.4% with Alex-MP-20) | 17.8% | 83.2% | 3.8-8.8% | ~9.22 (A100) |

Other:
- MatterGen (Zeni et al., Nature 2025): 78% within 0.1 eV/atom of MP hull; 13% on/below hull (3% vs Alex-MP-ICSD hull); 61% novel. https://www.nature.com/articles/s41586-025-08628-5
- GNoME hit rate: structural <6% -> >80%; compositional <3% -> 33%. https://www.nature.com/articles/s41586-023-06735-9
- FlowMM (strict, DFT): stable / S.U.N. = CDVAE 1.57/1.43, DiffCSP 5.06/3.34, FlowMM ~4.1-4.7/2.2-2.5 %. https://arxiv.org/html/2406.04713

## 5. DFT label reliability

| Item | Value | Source URL |
|---|---|---|
| GGA formation-energy MAE vs experiment | ~0.1-0.2 eV/atom; decomposition enthalpy as low as ~0.04 | https://www.nature.com/articles/s41524-020-00362-y |
| OQMD MAE | 0.136 uncorrected, 0.081-0.096 corrected; experiment-vs-experiment 0.082 eV/atom | https://www.nature.com/articles/npjcompumats201510 |
| MP corrected | 51 meV/atom MAE; ~50% of unstable entries within 5 meV of hull are inside fit uncertainty | https://www.nature.com/articles/s41598-021-94550-5 |
| ICSD metastable | 50.5% of 29,902; median 15 meV/atom, 90th pct 67 | https://perssongroup.lbl.gov/papers/sun-2016-metastability.pdf |
| GNoME under r2SCAN | 84% of binaries/ternaries and 86.8% of quaternaries stay stable (13-16% flip) | https://www.nature.com/articles/s41586-023-06735-9 |
| PBE -> SCAN funnel (An et al. 2026) | 109 of 166 PBE-stable survive SCAN (65.7%) | https://arxiv.org/html/2607.01713 |
| A-Lab failures | 3 of 16 analysed failures due to computational inaccuracy | https://www.nature.com/articles/s41586-023-06734-w |

No single published "DFT hull verdict error rate vs experiment" found.

## 6. Novelty

| Item | Value | Source URL |
|---|---|---|
| GNoME sample | 10 of 10 random entries match known structure types; ~11% contain radioactive elements (derived) | https://escholarship.org/content/qt9qx9t3kz/qt9qx9t3kz.pdf?t=sd23fh |
| A-Lab (Leeman) | 24 of 36 no evidence of predicted ordering; 3 of 36 already reported; 0 new | https://par.nsf.gov/servlets/purl/10532478 |
| A-Lab correction | "new to the platform, not necessarily new to science" | https://pmc.ncbi.nlm.nih.gov/articles/PMC12872444 |
| Novelty vs reference set size | MatterGen 91.8% -> 83.2%; ion exchange 72.4% -> 62.8% as references grow | https://arxiv.org/pdf/2501.02144 |

## Not found
- GNoME / WBM / OQMD / Alexandria total DFT compute
- Walker & Butler VASP CPU-time table (in SI, not retrieved)
- Origin of the $0.04 per CPU-hour figure (but current on-demand prices of $0.035-0.056 match it)
- Per-model MLIP run times, quantified MLIP-vs-DFT speedups
- GCP/Azure GPU prices, NERSC dollar rates

## Nearest neighbours (no dollar-per-material paper found)
- Szymanski & Bartel 2025: yields and generation time, no dollars
- FlowMM: cost per stable material in integration steps
- Walker & Butler: carbon cost of ML vs DFT workflows
- An et al. 2026: PBE -> MLIP -> SCAN funnel yields, no costs
