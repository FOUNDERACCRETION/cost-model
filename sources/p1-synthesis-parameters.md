# P1 parameter table: synthesis cost and synthesis success (hunt of 2026-10-09)

Status: first pass. Every number was read through a web-fetch summary, not by eye. Spot-check each at the URL before it enters the paper. No currency conversions made.


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

## A. Synthesis success rate

| Source | Rate | What counts as success | Selection caveats | URL |
|---|---|---|---|---|
| A-Lab, corrected article (Szymanski et al., Nature 2023, corrected Jan 2026) | 36/57 (63%); 40/57 if 4 inconclusive count; 38/54 (70%) excluding computational errors | Target phase in XRD refinement; disordered versions count; many samples not phase-pure | 432 candidates -> 146 air-stable -> 57 with available precursors; oxides and phosphates; 50 on hull, 7 near; 353 recipes in 17 days, 30% hit target (VERIFY: original may have said 355 and 37%) | https://pmc.ncbi.nlm.nih.gov/articles/PMC10700133 |
| A-Lab Author Correction (Nature 650, E1) | 36 of 40 reported successes confirmed, 4 inconclusive | Manual re-analysis of diffraction | "Novel" reworded as new to the platform, not to science; Zn2Cr3FeO8 removed | https://www.nature.com/articles/s41586-025-09992-y |
| Leeman et al., PRX Energy 2024 | 3/58 (5%); zero new materials | Convincingly made, by their reading | Issues with 42 of 43 examined; about two thirds likely known disordered phases | https://par.nsf.gov/servlets/purl/10532478 |
| Prein et al. 2025 (arXiv 2511.01790) | 7/16 characterized (44%); 7/24 (29%) if 8 uncharacterizable count as failures | Automated XRD plus expert check | Pre-filtered by synthesizability model from ~4.4M structures; oxides | https://arxiv.org/html/2511.01790v1 |
| Chen et al. 2024 (Microsoft/PNNL) | 1 of 4 targets made as predicted | PXRD match | Funnel 32.6M -> 589,609 -> 147 -> 23; halides | https://ar5iv.labs.arxiv.org/html/2401.04070 |
| Sun et al., Nat. Mater. 2019 (nitrides) | 7 synthesized of 203 predicted; number attempted not reported | Thin film, synchrotron XRD | Not a hit rate | https://arxiv.org/pdf/1809.09202 |
| GNoME (Merchant et al., Nature 2023) | 736 matches vs 381k new stable | Retrospective ICSD match | NOT a hit rate: the rest were never attempted | https://pmc.ncbi.nlm.nih.gov/articles/PMC10700131 |
| Cheetham & Seshadri, Chem. Mater. 2024 | No rate; 10 of 10 sampled matched known structure types | Novelty critique | Use for the novelty parameter | https://pmc.ncbi.nlm.nih.gov/articles/PMC11044265 |

## B. Cost per synthesis attempt: components

No published dollar cost per solid-state sample, and no A-Lab capex or operating cost, was found anywhere. This parameter has to be built bottom-up from the rows below.

### Powder XRD
| Institution | Fee | URL |
|---|---|---|
| UIUC | 22.39-44.78 USD/hr internal staff-run; 5.20-11.94 self-run; 80.94-102.83 industry | https://answers.uillinois.edu/106355 |
| Univ. of Houston | 10 self-run / 20 staff-run internal; 52.02 external academic (USD/hr) | https://www.uh.edu/nsm/chemistry/resources/x-ray-core-billing-rate_fy24-fy25.pdf |
| Cornell CCMR | 49.60-55.00 internal; 168.80-187.15 industry (USD/hr) | https://www.ccmr.cornell.edu/sites/default/files/2025-07/FY26%20Cornell.pdf |
| UT Austin | 11-15 USD/hr self-use; 80 USD/sample internal service; 150 USD/sample external | https://sites.utexas.edu/chem-x-ray/xrd-pricing/ |
| Caltech | 30 internal / 50 external non-profit (USD/hr); staff help 100/hr | https://xrcf.caltech.edu/fees |
| Oregon State | 5 USD per 30-min slot self-use; 100 USD/hr staff collection | https://xrd.science.oregonstate.edu/fees |
| IIT Madras | 200 internal / 400 external academic / 2,000 industry (INR per measurement) | https://chem.iitm.ac.in/assets/images/Charges-1.pdf |
| IIT Jodhpur | 400 academic / 600 industry (INR/sample) | https://www.iitj.ac.in/PageImages/Gallery/01-2026/Equipment-User-Charges-for-External-Users-CRF-639046068920681958.pdf |
| Univ. of Bern | 55 internal / 110 Swiss academic / 275 industry (CHF per service item) | https://xrd.dcbp.unibe.ch/Costs_for_the_XRD_Service_at_the_DCBP_2026.pdf |
| UNSW | 35 internal / 70 external academic / 150 commercial (AUD/hr) | https://www.analytical.unsw.edu.au/sites/default/files/facility_related_files/SSEAU%20Access%20Costs%202023.pdf |
| Monash | 44-54 internal / 90 standard (AUD/hr) | https://www.monash.edu/researchinfrastructure/x-ray/access/charges |

### Furnace, SEM, consumables
| Item | Value | URL |
|---|---|---|
| Cornell furnace, internal | 6 USD fixed + 3.15-3.75 USD/hr | https://www.ccmr.cornell.edu/sites/default/files/2025-07/FY26%20Cornell.pdf |
| Cornell furnace, industry | 13 USD fixed + 7.88-9.45 USD/hr | https://www.ccmr.cornell.edu/sites/default/files/2025-07/FY26%20Industry.pdf |
| Cornell SEM | 86.40-92.50 internal; 294-566 industry (USD/hr) | same two sheets |
| IIT Jodhpur SEM+EDX | 300 academic / 1,000 industry (INR/hr) | IIT Jodhpur URL above |
| Alumina crucible 10 mL (retail, reusable) | 37.85 USD | https://www.cplabsafety.com/high-alumina-crucible-cylindrical-form-10ml-each/un-jay010 |
| Precursor prices | NOT FOUND (vendor prices behind login) | - |

### Labor
| Item | Value | URL |
|---|---|---|
| NIH NRSA postdoc stipend FY2026 | 63,480 (yr 0) to 77,076 (yr 7+) USD/yr, unloaded | https://grants.nih.gov/grants/guide/notice-files/not-od-26-044.html |
| NIH NRSA predoc stipend FY2026 | 29,364 USD/yr | same |
| Stanford fringe FY2026 | 27.4% postdocs; 7.5% grad assistants | https://ora.stanford.edu/news/final-fringe-benefits-rates-fy2026 |
| Caltech F&A FY2026 | 70% on-campus (high end) | https://www.fundingopportunities.caltech.edu/static/guides/FY26_Rate_Memo.pdf |
| UKRI minimum PhD stipend 2025-26 | 20,780 GBP/yr | https://ukri.org/news/ukri-is-increasing-phd-stipends-and-improving-student-support |

### Throughput (human vs robot)
| Item | Value | URL |
|---|---|---|
| Manual solid-state (Liverpool, authors' estimate) | 10-20 compositions/week per undergraduate researcher | https://pmc.ncbi.nlm.nih.gov/articles/PMC10866347/ |
| PXRD prep + measurement | 40 human vs 168 robot samples/week | https://pubs.rsc.org/en/content/articlehtml/2024/sc/d3sc06206f |
| A-Lab press claim | 100-200 samples/day; 50-100x a human; 8 furnaces; ~10 people a little over a year to build | https://newscenter.lbl.gov/2023/04/17/meet-the-autonomous-lab-of-the-future/ |
| A-Lab realized (AlabOS paper) | >2,500 samples in ~1 year; peak 149 submitted in a day | https://arxiv.org/html/2405.13930v1 |
| Semi-automated solid-state | 328 min/iteration, ~105 min human (secondary; original study unidentified) | https://escholarship.org/content/qt1v056667/qt1v056667.pdf |

### Autonomous-lab capex
| Item | Value | URL |
|---|---|---|
| Samsung ASTRAL | ~120,000 USD startup (press figure, robotics only); up to 24 materials per 72 h; 224 reactions / 35 targets | https://mse.engin.umich.edu/about/news/better-battery-manufacturing-robotic-lab-vets-new-reaction-design-strategy |
| Other SDLs (Lo et al. review; none are powder labs) | 50 USD to 40M USD | https://pubs.rsc.org/en/content/articlehtml/2024/dd/d3dd00223c |
| A-Lab capex / opex | NOT PUBLISHED | - |

## C. Not found
- Any dollar cost per sample or per experiment for solid-state synthesis
- Any techno-economic analysis of a self-driving lab
- A-Lab, TRI, Kebotix, Lila, Periodic Labs, Polybot capex
- UK XRD fee schedules (quote-only), UK postdoc scales
- Itemized grant budgets (DOE/NSF/ARPA-E)
- A review tabulating prediction-to-synthesis hit rates
- To read manually: arXiv 2607.01713 "Predicting Novel Stable Materials for Experimental Synthesis"
