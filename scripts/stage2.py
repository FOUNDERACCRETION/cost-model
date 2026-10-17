"""Stage 2: tornado, Monte Carlo with named scenarios, kill-condition check, marginal returns, break-evens.

Run: uv run python scripts/stage2.py [--draws N]
Writes results/stage2.md, results/tornado.csv, results/monte_carlo_draws.csv, and regenerates the blocks of
README.md between <!-- generated:NAME:begin --> and <!-- generated:NAME:end --> markers, so every number in
those blocks comes from params/parameters.yaml and data/.
"""

import argparse
import collections
import csv
import json
import math
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import analysis as an  # noqa: E402
from src.funnel import funnel, synthesis_cost_per_attempt
from src.sampling import recipes_for_success  # noqa: E402
from src.params import load, records, resolve  # noqa: E402

LEVEL_NAMES = {
    "dft_confirmed_stable": "Level 1: per DFT-confirmed stable",
    "experimentally_validated": "Level 2: per validated material",
    "validated_new": "Level 3: per validated new material (lower-bound quantity; see README)",
}
SHORT = {"dft_confirmed_stable": "L1", "experimentally_validated": "L2", "validated_new": "L3"}
WORLDVIEW = {"optimistic_alab": "optimistic (A-Lab)", "middle_prein": "middle (Prein)",
             "pessimistic_leeman": "pessimistic (Leeman)"}
READING_SHORT = {"optimistic_alab": "A-Lab", "middle_prein": "Prein", "pessimistic_leeman": "Leeman"}
# Analysis criteria (not model parameters): what counts as "compute matters" and "materially different".
COMPUTE_SHARE = 0.10
SPREAD = 1.10
MATERIAL = 0.10
OVERLAP_REPS = 60
THRESHOLD_DRAWS = 1500  # draws behind the threshold distribution in Section 5.5  # resampling replicates behind the overlap reference range in Section 5.7
ORDER_SURVIVES = 0.95
MATERIAL_MAJORITY = 0.50
TOP_SHARE = 0.80


def money(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    if math.isinf(x):
        return "unbounded"
    return f"${x:,.0f}" if abs(x) >= 100 else f"${x:,.2f}"


def pct(x, digits=0):
    """Format a probability. A value short of certainty never prints as 100%, and one above zero
    never prints as 0%: rounding either way would assert something the simulation did not find.
    Such a value gains digits until it is distinguishable, up to four decimal places."""
    if x is None or math.isnan(x):
        return "n/a"
    d = digits
    while d < 4 and ((x < 1.0 and round(100 * x, d) >= 100) or (x > 0.0 and round(100 * x, d) <= 0)):
        d += 1
    return f"{100 * x:.{d}f}%"


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


# ---------------------------------------------------------------- sections


def daf_section(doc, p):
    e = an.enrichment(doc, p)
    pool, gen, wbm = e["pool"], e["gen"], e["wbm"]
    rows = [
        ["WBM (Matbench Discovery, reported)", pct(wbm["prevalence"], 1), "", f"{wbm['daf_reported']:.2f}×", ""],
        ["ion-exchange pool (Szymanski & Bartel)", pct(pool["prevalence"], 1), pct(pool["purity"], 1),
         f"**{pool['daf_measured']:.2f}×**", f"{pool['daf_matbench_rates_at_this_prevalence']:.2f}×"],
        ["MatterGen pool (Szymanski & Bartel)", pct(gen["prevalence"], 1), pct(gen["purity"], 1),
         f"**{gen['daf_measured']:.2f}×**", f"{gen['daf_matbench_rates_at_this_prevalence']:.2f}×"],
    ]
    ml = an.funnel(p)["pipelines"]["B"]["mlip"]
    mlc = an.funnel(p)["pipelines"]["C"]["mlip"]
    return f"""### Named finding: CHGNet's discovery acceleration factor is {pool['daf_measured']:.2f}× on a realistic ion-exchange pool, against {wbm['daf_reported']:.2f}× on WBM

The discovery acceleration factor (DAF) is the ratio of the filter's precision to the pool's prevalence: how many
times more often a filter-passed candidate is stable than a random one. Matbench Discovery defines it exactly so
("Formally the DAF is the ratio of the precision to the prevalence"). On Szymanski & Bartel's pools it is the
measured post-filter purity divided by the measured unfiltered stable fraction. That is the same quantity on both
sides, so the comparison needs no assumption about which classifier rate transfers.

{md_table(["Pool", "Stable fraction", "Purity after CHGNet", "DAF", "DAF if Matbench rates held at this prevalence"], rows)}

On the ion-exchange pool CHGNet's enrichment is {pool['daf_measured']:.2f}×. On MatterGen's pool it is
{gen['daf_measured']:.2f}×: the filter barely enriches at all. DAF depends on prevalence (its ceiling is
1 / prevalence), so the last column applies Matbench's recall and false-positive rate at each pool's own
prevalence. That makes the like-for-like comparison {pool['daf_measured']:.2f}× against
{pool['daf_matbench_rates_at_this_prevalence']:.2f}×, a larger gap than against the reported
{wbm['daf_reported']:.2f}×.

**Mechanism (rests on an assumption).** If Matbench's recall ({p['mlip_tpr']:.2f}) transfers to these pools,
the measured purity implies a false-positive rate of {ml['implied_fpr']:.2f} on the ion-exchange pool
({mlc['implied_fpr']:.2f} on MatterGen's), against {ml['matbench_fpr']:.2f} on WBM. The other attribution is
that Matbench's false-positive rate transfers and recall collapses. That would need recall of
{ml['recall_implied_by_purity_and_matbench_fpr']:.2f} and
{mlc['recall_implied_by_purity_and_matbench_fpr']:.2f}, which are implausible. The DAF result above does not
depend on this attribution.

**Why the gap: two explanations, one unresolved.**

1. *Distribution shift is weak as an explanation.* WBM was "generated via chemical similarity-based elemental
   substitution of MP source structures" over five rounds (Matbench Discovery, section 2.1.2). That is the same
   construction as Szymanski & Bartel's data-driven ion exchange. If anything, Matbench's unique-prototype subset
   removes structures whose protostructure matches MP, while ion exchange only reuses MP prototypes (0% novel
   prototypes). So the WBM test set is not the more conservative pool.
2. *The stability criteria differ, an unresolved competing explanation.* Matbench labels a structure stable if
   it is "on or below the convex hull of the MP training set" (MP v2022.10.28). It explicitly rejects using the
   joint MP + WBM hull, and it notes that only about 20k of the about 33k WBM structures below the MP hull remain
   on the joint hull. Szymanski & Bartel compute ΔE_d ≤ 0 against phase diagrams that "included all entries from
   MP (as of June 2025) as well as the entries generated from each AI model or baseline approach". That is a
   newer MP and a hull that also contains the other generated candidates, close to the joint-hull formulation
   Matbench rejected. The two criteria agree on the threshold (on or below the hull) but not on the hull. A
   stricter hull lowers both prevalence and the share of passed candidates that count as stable, so part of the
   gap may be definitional rather than a weakness of the filter. Public data can resolve this: recompute CHGNet's
   DAF on WBM against the joint MP + WBM hull. Until then the DAF gap is a measured fact, but its cause is open.
"""


def distributions_section(doc):
    mc = doc["monte_carlo"]
    recs = records(doc)
    rows = []
    for name, spec in mc["distributions"].items():
        rec = recs[name]
        if spec["type"] in ("triangular", "log_triangular"):
            params = f"{rec['low']:g} / {rec['base']:g} / {rec['high']:g}"
        elif spec["type"] in ("log_uniform", "uniform"):
            params = f"{rec['low']:g} to {rec['high']:g}"
        elif spec["type"] == "beta_counts":
            params = f"{spec['k']} of {spec['n']}"
        else:
            params = f"{len(spec['values'])} values, {min(spec['values']):g}–{max(spec['values']):g}"
        rows.append([f"`{name}`", spec["type"], params, spec["reason"]])
    j = mc["joint"]
    joint_rows = [["pool stability, novelty, filter purity", j["pools"]["method"], j["pools"]["reason"]],
                  ["synthesis success, novelty, wrong-verdict share",
                   "; ".join(f"{WORLDVIEW[k]}: success {v['success']['k']}/{v['success']['n']}, novelty "
                             f"{v['novelty']['k']}/{v['novelty']['n']}, wrong verdict "
                             + (f"{v['wrong_verdict']['k']}/{v['wrong_verdict']['n']}" if v['wrong_verdict']['type'] == 'beta_counts'
                                else f"uniform {v['wrong_verdict']['low']}–{v['wrong_verdict']['high']}")
                             for k, v in j["worldview"]["readings"].items()) + f". {j['worldview']['weights_reason']}",
                   j["worldview"]["reason"]],
                  ["recipes per target", j["recipes"]["method"], j["recipes"]["reason"]]]
    return ("**Sampled parameters** (all others held at base; triangular parameters are low / mode / high = the "
            "record's low / base / high):\n\n"
            + md_table(["Parameter", "Distribution", "Parameters", "Why"], rows)
            + "\n\n**Joint draws** (the documented correlations, not sampled independently):\n\n"
            + md_table(["Drawn together", "How", "Why"], joint_rows))


def tornado_section(tor, top=8):
    parts, top_rows = [], []
    for lvl in an.LEVELS:
        for k in an.PIPELINES:
            rows = tor[lvl][k]
            names = an.top_share(rows, TOP_SHARE)
            top_rows.append([f"{SHORT[lvl]} {k}", ", ".join(f"`{n}`" for n in names)
                             + "".join(f"; `{r['name']}` {r['status']}" for r in rows if r["status"] != "ok")])
    l1 = tor["dft_confirmed_stable"]["B"][0]
    l2 = tor["experimentally_validated"]["B"][0]
    parts.insert(0, f"**Read this tornado as a map of where the evidence is weakest, not of where the leverage is.** "
                    f"One parameter carries almost all of the one-at-a-time variance at each level: `{l1['name']}` "
                    f"({pct(l1['share'], 1)} at level 1, B) and `{l2['name']}` ({pct(l2['share'], 1)} at level 2, B). "
                    "They dominate because they have the widest ranges (3–1,000 core-h; 5–70% success), not because "
                    "the cost responds more strongly to them. For leverage per unit change, see the marginal returns, "
                    "where three synthesis levers are tied at unit elasticity. The two quantities the paper most needs "
                    "better measurements of are DFT cost per candidate on modern hardware and synthesis success on "
                    "independent campaigns.")
    parts.append(f"**Parameters that account for the top {TOP_SHARE:.0%} of variance** (one-at-a-time, "
                 "share = swing² / Σ swing²; parameters whose one end makes the inputs contradict each other, or makes "
                 "the cost unbounded, are listed after the semicolon and left out of the shares):\n\n"
                 + md_table(["Output", "Parameters"], top_rows))
    for k in an.PIPELINES:
        rows = [r for r in tor["experimentally_validated"][k] if r["status"] != "ok" or r["swing"] > 0][:top]
        parts.append(f"**Tornado, level 2, pipeline {k}** (top {top}; full tables in `results/stage2.md`):\n\n"
                     + md_table(["Parameter", "cost at low", "cost at high", "swing", "variance share"],
                                [[f"`{r['name']}`", money(r["low_cost"]), money(r["high_cost"]),
                                  money(r["swing"]) if r["status"] == "ok" else r["status"], pct(r["share"], 1)]
                                 for r in rows]))
    rows = [r for r in tor["dft_confirmed_stable"]["B"] if r["status"] != "ok" or r["swing"] > 0][:top]
    parts.append(f"**Tornado, level 1, pipeline B** (top {top}):\n\n"
                 + md_table(["Parameter", "cost at low", "cost at high", "swing", "variance share"],
                            [[f"`{r['name']}`", money(r["low_cost"]), money(r["high_cost"]),
                              money(r["swing"]) if r["status"] == "ok" else r["status"], pct(r["share"], 1)]
                             for r in rows]))
    return "\n\n".join(parts)


def tornado_full(tor):
    parts = []
    for lvl in an.LEVELS:
        for k in an.PIPELINES:
            rows = tor[lvl][k]
            acc, table = 0.0, []
            for r in rows:
                if r["status"] == "ok":
                    acc += r["share"] if not math.isnan(r["share"]) else 0
                table.append([f"`{r['name']}`", money(r["low_cost"]), money(r["high_cost"]),
                              money(r["swing"]) if r["status"] == "ok" else r["status"], pct(r["share"], 2),
                              pct(acc, 1) if r["status"] == "ok" else ""])
            parts.append(f"#### {LEVEL_NAMES[lvl]}, pipeline {k}\n\n"
                         + md_table(["Parameter", "cost at low", "cost at high", "swing", "share", "cumulative"], table))
    return "\n\n".join(parts)


def mc_section(mc, summ, scen, mc_weights, sensitivity):
    n, rej = len(mc["draws"]), mc["rejected"]
    rows = []
    for lvl in ("dft_confirmed_stable", "experimentally_validated"):
        for k in an.PIPELINES:
            q = summ[lvl][k]
            rows.append([SHORT[lvl], k, money(q[5]), money(q[50]), money(q[95])]
                        + [money(scen[s]["costs"][lvl][k]) for s in WORLDVIEW])
    lvl3 = []
    for k in an.PIPELINES:
        q = summ["validated_new"][k]
        lvl3.append(["L3", k, money(q[5]), money(q[50]), money(q[95])]
                    + [money(scen[s]["costs"]["validated_new"][k]) for s in WORLDVIEW])
    recipes = ", ".join(f"{WORLDVIEW[s]} {scen[s]['recipes']:.2f}" for s in WORLDVIEW)
    by_wv = {}
    for d in mc["draws"]:
        by_wv.setdefault(d["worldview"], []).append(d["costs"]["experimentally_validated"]["B"])
    wv_rows = [[WORLDVIEW[w], len(by_wv[w]), money(an.percentile(by_wv[w], 50)),
                money(an.percentile(by_wv[w], 5)), money(an.percentile(by_wv[w], 95))] for w in WORLDVIEW]
    return (f"{n:,} draws (seed {MC_SEED}); {rej:,} draws rejected and redrawn because their inputs contradicted "
            f"each other (MLIP purity below prevalence × recall), {pct(rej / (n + rej), 1)} of all draws. Rejection "
            "enforces the recall–purity constraint from the correlations block; it trims draws where a high recall "
            "meets a low MatterGen purity, so the accepted draws lean slightly towards lower recall for C.\n\n"
            + md_table(["Level", "Pipeline", "MC 5th pct", "MC median", "MC 95th pct", *WORLDVIEW.values()], rows)
            + f"\n\nScenario columns: each named reading with every other parameter at base, each carrying its own "
              f"recipe count ({recipes} recipes per target) --- campaign-reported where a campaign reports one, from "
              "the budget model otherwise. The stage-1 base case is the middle reading, so it matches that column.\n\n"
            + "Level 3, shown only for completeness and never as a headline. Its Monte Carlo spread is dominated by "
              "the prior on a 0-of-36 count:\n\n"
            + md_table(["Level", "Pipeline", "MC 5th pct", "MC median", "MC 95th pct", *WORLDVIEW.values()], lvl3)
            + "\n\nLevel 2, pipeline B, by worldview (the mixture is the main source of level-2 spread):\n\n"
            + md_table(["Worldview", "draws", "median", "5th pct", "95th pct"], wv_rows)
            + f"\n\n**The upper tail is an assumption, not a measurement.** The level-2 95th percentile "
              f"({money(summ['experimentally_validated']['B'][95])} for B) exists because the Leeman reading gets "
              "weight one third. It is a statement about whose re-analysis to believe. With the Leeman reading at "
              f"weight zero it falls to {money(an.reweighted(mc, {'optimistic_alab': 0.5, 'middle_prein': 0.5, 'pessimistic_leeman': 0.0}, mc_weights, 'experimentally_validated', 'B', 95))}.\n\n"
            + "**How the mixture moves with the weights** (level 2, pipeline B; same draws, importance-reweighted):\n\n"
            + md_table(["Weights: A-Lab / Prein / Leeman", "median", "95th percentile"],
                       [[" / ".join(f"{w[n]:.2f}" for n in WORLDVIEW),
                         money(an.reweighted(mc, w, mc_weights, "experimentally_validated", "B", 50)),
                         money(an.reweighted(mc, w, mc_weights, "experimentally_validated", "B", 95))]
                        for w in [mc_weights] + sensitivity]))


def kill_section(kill):
    rows = []
    for lvl in an.LEVELS:
        k = kill[lvl]
        rows.append([SHORT[lvl], pct(k["p_lt"][("B", "A")], 1), pct(k["p_lt"][("C", "B")], 1),
                     pct(k["p_lt"][("C", "A")], 1), pct(k["overlap"][("B", "A")]), pct(k["overlap"][("C", "B")]),
                     pct(k["p_material"][("B", "A")]), pct(k["p_material"][("C", "B")])])
    def verdict_for(lvl):
        k = kill[lvl]
        bits = []
        for x, y in (("B", "A"), ("C", "B")):
            p_lt = k["p_lt"][(x, y)]
            ordered = p_lt >= ORDER_SURVIVES or p_lt <= 1 - ORDER_SURVIVES
            material = k["p_material"][(x, y)] >= MATERIAL_MAJORITY
            cheaper, dearer = (x, y) if p_lt >= 0.5 else (y, x)
            if ordered and material:
                state = f"**separates**: {cheaper} is cheaper than {dearer} in {pct(max(p_lt, 1 - p_lt), 1)} of draws and they differ by more than {MATERIAL:.0%} in {pct(k['p_material'][(x, y)])}"
            elif ordered:
                state = f"**ordered but immaterial**: {cheaper} is cheaper in {pct(max(p_lt, 1 - p_lt), 1)} of draws, but they differ by more than {MATERIAL:.0%} in only {pct(k['p_material'][(x, y)])}"
            else:
                state = f"**no ordering survives**: {x} is cheaper than {y} in {pct(p_lt, 1)} of draws"
            bits.append(f"{x} vs {y} {state}")
        return "; ".join(bits)

    l1, l2 = kill["dft_confirmed_stable"], kill["experimentally_validated"]
    verdict = (
        f"**Verdict** (an ordering survives if it holds in at least {ORDER_SURVIVES:.0%} of paired draws; it is "
        f"material if the two differ by more than {MATERIAL:.0%} in at least {MATERIAL_MAJORITY:.0%} of draws).\n\n"
        f"- Level 1: {verdict_for('dft_confirmed_stable')}.\n"
        f"- Level 2: {verdict_for('experimentally_validated')}.\n"
        f"- Level 3: {verdict_for('validated_new')}.\n\n"
        "The expectation going in (level 1 separates, level 2 does not) is confirmed in a specific sense. At level 2 the "
        "ordering B < A still holds draw by draw, because the synthesis term is shared and the compute term is "
        "not, but the difference is immaterial. **The marginal distributions overlap heavily at every level, "
        f"level 1 included (B–A overlap {pct(l1['overlap'][('B', 'A')])}).** The absolute cost is dominated by "
        "uncertainty that all pipelines share: the 3–1,000 core-h DFT span at level 1, and the synthesis worldview "
        "at level 2. So the pipelines cannot be told apart by comparing their absolute cost ranges. Only the "
        "paired comparison, the same world under each pipeline, separates them, and only at level 1.")
    return (md_table(["Level", "P(B < A)", "P(C < B)", "P(C < A)", "overlap B–A", "overlap C–B",
                      f"P(B, A differ > {MATERIAL:.0%})", f"P(C, B differ > {MATERIAL:.0%})"], rows)
            + "\n\nP(x < y) is paired: both pipelines see the same drawn world. "
              f"P(differ > {MATERIAL:.0%}) is paired and symmetric: the dearer of the pair exceeds the cheaper by "
              f"more than {MATERIAL:.0%} in that draw, the same denominator convention as the DFT threshold sweep. "
              "Overlap is the overlap coefficient of the two marginal cost distributions on a "
              f"{60}-bin log10-cost histogram whose bins are normalised probabilities, not densities; 100% = "
              "identical. See results/overlap_bin_sensitivity.csv for its bin-count dependence.\n\n" + verdict)


def returns_section(p, mc_ret):
    base = an.log_elasticities(p)
    groups = {n: lv["group"] for n, lv in an.levers().items()}
    synth = [n for n in groups if groups[n] == "synthesis"]
    comp = [n for n in groups if groups[n] == "compute"]
    rows = []
    for name in synth + comp:
        rows.append([("tied, synthesis" if name in synth else "compute"), name,
                     *(f"{base[name][k]['return'] + 0.0:.3f}" for k in an.PIPELINES),
                     *(f"{mc_ret[name][k]['median']:.3f} ({mc_ret[name][k]['p5']:.3f}–{mc_ret[name][k]['p95']:.3f})"
                       for k in an.PIPELINES)])
    synth_min = {k: min(base[n][k]["return"] for n in synth) for k in an.PIPELINES}
    comp_max = {k: max(base[n][k]["return"] for n in comp) for k in an.PIPELINES}
    ratio = {k: synth_min[k] / comp_max[k] for k in an.PIPELINES}
    mc_ratio = {k: min(mc_ret[n][k]["median"] for n in synth) / max(mc_ret[n][k]["median"] for n in comp)
                for k in an.PIPELINES}
    return ("Return = % fall in cost per validated material per 1% PROPORTIONAL improvement in the lever: the log-elasticity "
            "d ln(cost) / d ln(lever) at the evaluation point, signed so that a positive number means the improvement "
            "lowers cost. It is scale-free, so levers in different units compare directly.\n\n"
            + md_table(["Group", "Lever", "A base", "B base", "C base", "A MC median (5–95%)", "B MC median (5–95%)",
                        "C MC median (5–95%)"], rows)
            + "\n\n**The synthesis levers are tied at unit elasticity; they are not ranked.** Level-2 synthesis cost is "
              "recipes × cost per attempt / success, so each of the three has elasticity one by "
              "construction. Success is exactly 1 because it also divides the compute term. Recipes and cost per "
              "attempt equal the synthesis share of level-2 cost ("
            + ", ".join(f"{base['recipes per target'][k]['return']:.3f} for {k}" for k in an.PIPELINES)
            + "). The gap between them is the compute share, not a difference in leverage. `tests/test_stage2.py` "
              "asserts this structure.\n\n"
            + "**The finding is the magnitude gap.** A 1% improvement on the synthesis side lowers cost per validated "
              "material by at least "
            + ", ".join(f"{synth_min[k]:.2f}% ({k})" for k in an.PIPELINES)
            + ". The best computational lever lowers it by at most "
            + ", ".join(f"{comp_max[k]:.3f}% ({k})" for k in an.PIPELINES)
            + ". That is a ratio of "
            + ", ".join(f"{ratio[k]:.0f}× ({k})" for k in an.PIPELINES)
            + " at the base point, and "
            + ", ".join(f"{mc_ratio[k]:.0f}× ({k})" for k in an.PIPELINES)
            + f" at the Monte Carlo medians. Proportionally, synthesis is worth "
              f"{min(min(ratio.values()), min(mc_ratio.values())):.0f}–{max(max(ratio.values()), max(mc_ratio.values())):.0f} "
              "times compute, depending on the pipeline and the evaluation point.")


def spot_section(doc, p, mc_ret):
    sp = an.spot_switch(doc, p)
    base = sp["change"]
    under = all(abs(base[k]) < 0.01 for k in an.PIPELINES)
    r_lo, r_hi = compute_ratio_range(p, mc_ret)
    size = ("by less than one percent" if under else
            f"by {min(abs(v) for v in base.values()):.1%}–{max(abs(v) for v in base.values()):.1%}")
    return (f"**The only free lever moves cost per validated material {size}.** Switching compute from "
            f"on-demand to spot prices is available today at no research cost: {sp['cpu_discount']:.0%} off CPU and "
            f"{sp['gpu_discount']:.0%} off A100 time. It changes level-2 cost per validated material by "
            + ", ".join(f"{base[k]:+.2%} ({k})" for k in an.PIPELINES)
            + " at the base point, with Monte Carlo medians of "
            + ", ".join(f"{mc_ret['spot'][k]['median']:+.2%} ({k})" for k in an.PIPELINES)
            + f". So the only lever whose cost is known (zero) moves the result {size}"
              + ("" if under else f" (under one percent only for {', '.join(k for k in an.PIPELINES if abs(base[k]) < 0.01)})")
              + f". The levers worth {r_lo:.0f}–{r_hi:.0f} times more per percentage point are synthesis success, recipes per target and "
              "cost per attempt, and improving any of them requires synthesis research whose cost nobody has measured.")


def compute_ratio_range(p, mc_ret):
    """Range of (weakest synthesis lever) / (strongest compute lever) over pipelines, at base and MC medians."""
    base = an.log_elasticities(p)
    groups = {n: lv["group"] for n, lv in an.levers().items()}
    synth = [n for n in groups if groups[n] == "synthesis"]
    comp = [n for n in groups if groups[n] == "compute"]
    ratios = []
    for k in an.PIPELINES:
        ratios.append(min(base[n][k]["return"] for n in synth) / max(base[n][k]["return"] for n in comp))
        ratios.append(min(mc_ret[n][k]["median"] for n in synth) / max(mc_ret[n][k]["median"] for n in comp))
    return min(ratios), max(ratios)


def headline_section(doc, p, mc, scen, mc_ret, tor):
    wv = doc["monte_carlo"]["joint"]["worldview"]
    readings = wv["readings"]
    lvl = "experimentally_validated"
    med, rows = {}, []
    for name, rd in readings.items():
        draws = [d for d in mc["draws"] if d["worldview"] == name]
        med[name] = {k: an.percentile([d["costs"][lvl][k] for d in draws], 50) for k in an.PIPELINES}
        cells = []
        for k in an.PIPELINES:
            xs = [d["costs"][lvl][k] for d in draws]
            cells.append(f"**{money(med[name][k])}** ({money(an.percentile(xs, 5))}–{money(an.percentile(xs, 95))})")
        rows.append([WORLDVIEW[name], rd["source"], rd["standing"],
                     f"{rd['success']['k']} of {rd['success']['n']}", *cells])
    lo_name, mid_name, hi_name = "optimistic_alab", "middle_prein", "pessimistic_leeman"
    # The names rank how optimistic each reading is about what was MADE, not about cost. Since the
    # middle reading reports one recipe per target it is the cheapest of the three, so the spread is
    # max over min across all three readings, not pessimistic over optimistic.
    cheap_name = min(readings, key=lambda n: med[n][b_]) if (b_ := "B") else lo_name
    dear_name = max(readings, key=lambda n: med[n]["B"])
    factor = {k: max(med[n][k] for n in readings) / min(med[n][k] for n in readings) for k in an.PIPELINES}
    within = {name: max(med[name].values()) / min(med[name].values()) for name in readings}
    r_lo, r_hi = compute_ratio_range(p, mc_ret)
    spot = an.spot_switch(doc, p)["change"]
    s_lo, s_hi = min(abs(v) for v in spot.values()), max(abs(v) for v in spot.values())
    b = "B"
    top2 = {k: tor[lvl][k][0] for k in an.PIPELINES}
    top2_name = {r["name"] for r in top2.values()}
    top2_share = min(r["share"] for r in top2.values())
    return (
        "**Headline: cost per experimentally validated material depends on which reading of the synthesis evidence "
        "is right, not on the pipeline.** Each row below is the Monte Carlo conditional on one reading: median, and "
        f"90% interval in brackets ({len(mc['draws']):,} draws in total, about a third per reading).\n\n"
        + md_table(["Reading", "Source", "Standing", "Targets made (success)", "Level 2, A", "Level 2, B", "Level 2, C"], rows)
        + f"\n\nCost per experimentally validated material ranges from about {money(med[cheap_name][b])} under the "
          f"{WORLDVIEW[cheap_name]} reading to about {money(med[dear_name][b])} under the {WORLDVIEW[dear_name]} one "
          f"(pipeline B), with {WORLDVIEW[lo_name]} at {money(med[lo_name][b])}. NOTE the ordering: the reading named "
          "for the most optimistic view of what was synthesised is not the cheapest, because it reached its success "
          "rate with 6.19 recipes per target against the middle reading's one. Across the three readings that is a "
          "factor of "
          + ", ".join(f"{factor[k]:.0f}× ({k})" for k in an.PIPELINES)
          + ". Within any one reading, pipeline choice moves the median by at most "
          + ", ".join(f"{within[n]:.2f}× ({READING_SHORT[n]})" for n in readings)
          + ". The spread is driven jointly by synthesis success and recipes per target, which arrive together with "
            "each reading along with its wrong-verdict share. Recipes are the campaign-reported count wherever a "
            "campaign reports one, and fall back to the budget model only where none does. In the one-at-a-time "
            f"tornado, `{', '.join(sorted(top2_name))}` carries at least {pct(top2_share, 1)} of level-2 variance in "
            "every pipeline.\n\n"
          + f"**The factor of about {statistics.median(factor.values()):.0f} across the readings is not "
            "measurement uncertainty.** A-Lab and Leeman et al. read the same experiment, the A-Lab campaign, "
            "and disagree about what was made. Prein et al. is a separate, smaller campaign. "
            "No reanalysis of existing data closes this gap; resolving it requires new synthesis data: independent "
            "campaigns with phase identification that both sides accept.\n\n"
          + f"**No compute-side improvement closes a gap of this size.** The best compute lever is {r_lo:.0f} to "
            f"{r_hi:.0f} times weaker per proportional point than the synthesis levers (marginal returns below) --- a "
            "single-digit-to-low-double-digit margin at base verification cost, which inverts at the top of the DFT "
            "span, and in neither case approaches the factor above. The only free compute "
            f"lever, moving from on-demand to spot prices, changes the result by {s_lo:.1%} to {s_hi:.1%}.\n\n"
          + f"**Where a single number is unavoidable** (an abstract, a title slide), quote the Prein-reading median "
            f"with the spread beside it, never alone: \"about {money(med[mid_name][b])} per validated material, "
            f"rising to {money(med[lo_name][b])} and {money(med[dear_name][b])} under the other two readings of the "
            "synthesis evidence\". The Prein reading is the middle one on success, not the best-established and not "
            "a conservative choice on cost: it rests on an arXiv preprint with 24 targets and is the cheapest of the "
            "three, while the other two readings are peer-reviewed (Nature; PRX Energy).\n\n"
          + f"The deterministic base case follows the Prein reading throughout --- its success rate and its one "
            f"recipe per target --- and gives {money(an.costs(p)[lvl][b])} for B, against the point scenario's "
            f"{money(scen[mid_name]['costs'][lvl][b])}; the two differ only in the parameters the scenario also "
            "moves. An equal-weight mixture of the three readings is reported under Monte Carlo below. Its median "
            "and tail depend on weights nobody has measured, so it is not a headline."
    )


def breakeven_section(doc, p):
    recs = records(doc)
    fc = an.fixed_cost_payback(doc, p)
    rows, v_num, v_now = [], [], []
    for lvl_name in ("low", "base", "high"):
        q = {**p, "dft_cost_per_candidate": recs["dft.cost_per_candidate"][lvl_name]}
        t = an.attempt_cost_thresholds(q, COMPUTE_SHARE, SPREAD)
        v_num.append(t["attempt_for_compute_share"])
        v_now.append(t["attempt_usd"])
        rows.append([f"{recs['dft.cost_per_candidate'][lvl_name]:g} core-h ({lvl_name})", money(t["attempt_usd"]),
                     *(money(t["attempt_for_compute_share"][k]) for k in an.PIPELINES), money(t["attempt_for_spread"])])
    parity_b = an.purity_for_parity(p, "B")
    parity_a = an.purity_for_parity(p, "A")
    return (
        "**1. Screening scale at which the MLIP filter's fixed cost pays for itself: a non-result.** No such scale "
        "exists: there is no batch size at which the filter fails to pay for itself. B's extra fixed cost over A is "
        f"loading CHGNet once ({recs['mlip.chgnet.model_load_s']['base']:.2f} s, first-hand) plus relaxing the "
        f"reference phases with it ({p['reference_phases']:g} at base; the count is still missing), "
        f"{fc['extra_fixed_core_h']:.2g} core-h in all. The filter saves {fc['saving_core_h_per_candidate']:.1f} core-h "
        f"({money(fc['saving_usd_per_candidate'])}) on every MP-novel candidate, so the first candidate repays it "
        f"{1 / fc['payback_candidates']:,.0f} times over. The informative quantity is the per-candidate saving: any "
        f"other fixed cost X core-h, such as fine-tuning, pays back after X / {fc['saving_core_h_per_candidate']:.1f} "
        "candidates.\n\n"
        f"**2. Synthesis cost per attempt below which compute starts to matter for level 2.** Compute 'matters' here "
        f"means it is at least {COMPUTE_SHARE:.0%} of a pipeline's level-2 cost, or the level-2 spread reaches "
        f"{SPREAD:.2f}×.\n\n"
        + md_table(["DFT cost", "attempt cost now", f"A: compute ≥ {COMPUTE_SHARE:.0%} below",
                    f"B: compute ≥ {COMPUTE_SHARE:.0%} below", f"C: compute ≥ {COMPUTE_SHARE:.0%} below",
                    f"spread ≥ {SPREAD:.2f}× below"], rows)
        + "\n\nAt today's attempt cost, compute is at least " + f"{COMPUTE_SHARE:.0%}" + " of level 2 only where the "
          "threshold in its row exceeds the attempt cost now: " + "; ".join(
              f"{r[0]}: " + (", ".join(k for k, v in zip(an.PIPELINES, r[2:5]) if v_num[i][k] > v_now[i]) or "none")
              for i, r in enumerate(rows))
          + "."
        + f"\n\n**3. MLIP purity at which C becomes competitive.** C matches B at level 1 when CHGNet's purity on "
          f"MatterGen's pool reaches {pct(parity_b['purity'], 1)}, {parity_b['ratio_to_measured']:.1f}× the "
          f"measured {pct(parity_b['measured'], 1)}. Equivalently, enrichment on that pool would need to be "
          f"{parity_b['purity'] / p['gen_frac_stable']:.1f}× instead of {p['gen_filter_purity'] / p['gen_frac_stable']:.2f}×. "
          f"C matches A (no filter, ion-exchange pool) at {pct(parity_a['purity'], 1)}, "
          f"{parity_a['ratio_to_measured']:.1f}× the measured value. Parity at level 1 implies parity at level 2, "
          "because the synthesis term is shared. The purity cannot fall below "
          f"{pct(parity_b['floor'], 2)} (prevalence × recall).")


# ---------------------------------------------------------------- stage-1 blocks (base case, cost basis, DFT span)

FA_VARIANTS = (("`bench`: direct costs only", "bench", False),
               ("`funder`, fees outside the indirect-cost base (**default**)", "funder", False),
               ("`funder`, fees inside the indirect-cost base", "funder", True))


def _l2(res):
    return [res["pipelines"][k]["outputs"]["experimentally_validated"] for k in an.PIPELINES]


def stage1_numbers(doc, p):
    """Every stage-1 number quoted in prose: base case, attempt cost, cost bases, DFT span, multipliers."""
    recs = records(doc)
    res = funnel(p)
    out = {k: res["pipelines"][k]["outputs"] for k in an.PIPELINES}
    att = res["unit_costs"]["synthesis_attempt"]
    l2 = _l2(res)
    bases = []
    for label, cb, fees in FA_VARIANTS:
        r = funnel({**p, "synth_cost_basis": cb, "fa_on_service_fees": fees})
        a = r["unit_costs"]["synthesis_attempt"]
        v = [o["usd_per"] for o in _l2(r)]
        bases.append({"label": label, "attempt": a["usd"], "indirect": a["parts"]["indirect (F&A)"], "l2": v,
                      "spread": max(v) / min(v)})
    span = []
    for lvl in ("low", "base", "high"):
        dft = recs["dft.cost_per_candidate"][lvl]
        r = funnel({**p, "dft_cost_basis": "span", "dft_cost_per_candidate": dft})
        l1 = [r["pipelines"][k]["outputs"]["dft_confirmed_stable"]["usd_per"] for k in an.PIPELINES]
        o2 = _l2(r)
        v2 = [o["usd_per"] for o in o2]
        share = [o["synthesis_usd_per"] / o["usd_per"] for o in o2]
        span.append({"level": lvl, "dft": dft, "l1": l1, "l2": v2, "spread": max(v2) / min(v2),
                     "share_lo": min(share), "share_hi": max(share)})
    mult = {t: an.multiplier_for_level2_spread(p, t) for t in (1.5, 2.0)}
    l1 = {k: out[k]["dft_confirmed_stable"]["usd_per"] for k in an.PIPELINES}
    return {"out": out, "att": att, "l2": l2, "bases": bases, "span": span, "mult": mult, "l1": l1,
            "rate": p["synth_indirect_rate"], "rate_rec": recs["synth.indirect_rate"]}


def basecase_section(s1):
    out = s1["out"]
    rows = [["1. per DFT-confirmed stable material", *(money(out[k]["dft_confirmed_stable"]["usd_per"]) for k in an.PIPELINES)],
            ["2. per experimentally validated material", *(money(o["usd_per"]) for o in s1["l2"])],
            ["of which compute", *(money(o["compute_usd_per"]) for o in s1["l2"])],
            ["of which synthesis", *(money(o["synthesis_usd_per"]) for o in s1["l2"])]]
    return md_table(["Output", "A: DFT only", "B: CHGNet → DFT", "C: MatterGen → CHGNet → DFT"], rows)


def costbasis_section(s1):
    rows = [[b["label"], money(b["attempt"]), money(b["indirect"]), " / ".join(money(v) for v in b["l2"]),
             f"{b['spread']:.2f}×"] for b in s1["bases"]]
    lo, hi = s1["bases"][0]["l2"][0], s1["bases"][2]["l2"][0]
    return (md_table(["Basis", "$ per attempt", "of which indirect cost", "Level 2: A / B / C", "Spread"], rows)
            + f"\n\nBetween `bench` and fees-inside-base the choice moves level 2 by {hi / lo - 1:.0%} "
              f"({money(lo)} against {money(hi)} for A), but not the spread.")


def dftspan_section(s1):
    names = {"low": "(our measurement)", "base": "(geometric midpoint)", "high": "(MP 2012, upper)"}
    rows = [[f"{r['dft']:g} {names[r['level']]}", " / ".join(money(v) for v in r["l1"]),
             " / ".join(money(v) for v in r["l2"]), f"{r['spread']:.2f}×",
             (f"{r['share_lo']:.0%}" if round(r['share_lo'], 2) == round(r['share_hi'], 2)
              else f"{r['share_lo']:.0%}–{r['share_hi']:.0%}")] for r in s1["span"]]
    return md_table(["DFT core-h per candidate", "Level 1: A / B / C", "Level 2: A / B / C", "Level 2 spread",
                     "Synthesis share of level 2"], rows)


def attempt_section(s1):
    parts = s1["att"]["parts"]
    rr = s1["rate_rec"]
    return (f"A-Lab tried about six recipes per target (353 for 57), so each target is charged six attempts, and "
            f"targets that fail still pay for all their attempts. At base an attempt costs {money(s1['att']['usd'])}. "
            f"XRD ({money(parts['xrd'])}) and furnace ({money(parts['furnace'])}) are the largest items, then labour "
            f"({money(parts['labour'])}), tuition ({money(parts['tuition'])}) and indirect cost "
            f"({money(parts['indirect (F&A)'])}, at the {rr['base']:.0%} effective indirect cost recovery rate). "
            f"Precursors are {money(parts['precursors'])}.")


def level3_section(s1):
    v = [s1["out"][k]["validated_new"]["usd_per"] for k in an.PIPELINES]
    return (f"At base, the lower bounds are about {money(round(statistics.median(v), -3))} for each of A, B and C ("
            + ", ".join(f"{k} ≥ {money(x)}" for k, x in zip(an.PIPELINES, v)) + ").")


def multiplier_section(s1, p):
    rows = []
    for t, r in s1["mult"].items():
        rows.append([f"{t:g}×", f"{r['multiplier']:.2f}", pct(r["filtered_success"]),
                     pct(p["synth_success_unconditional"])])
    r2 = s1["mult"][2.0]
    return (md_table(["Level-2 spread", "Multiplier needed", "Success in B and C", "Success in A"], rows)
            + f"\n\nFor pipeline choice to double the cost per validated material, an MLIP pre-filter would have to "
              f"roughly double synthesis success, from {pct(p['synth_success_unconditional'])} to "
              f"{pct(r2['filtered_success'])}.")


def dft_threshold_sweep(p, points=(3, 10, 30, 54.5, 100, 200, 300, 500, 1000),
                        targets=(0.05, 0.10, 0.20)):
    """Vary DFT cost per candidate DIRECTLY and report paired pipeline gaps.

    This is not the same object as the DFT-span table, which varies the span's low endpoint
    and recomputes a geometric-midpoint base: that is a sensitivity to the base-selection
    convention. Here DFT cost is the independent variable, so the question answered is
    "at what verification cost does the choice of pipeline start to matter?" with synthesis
    success, recipes and attempt cost held shared across pipelines throughout.

    Comparators are relative to B, the cheapest pipeline throughout the swept range: (C - B)/B is
    the generative-pool decision, (A - B)/B is the MLIP-filter decision.

    DENOMINATOR CONVENTION. Each comparator is the gap of the dearer pipeline over the cheaper
    one, computed by analysis._ratio_gap, which is the same function the Monte Carlo materiality
    statistic uses. The two are therefore the same quantity measured two ways, deterministically
    here and across draws there, and a crossing in this table and a share of material draws in
    Section 5.6 may be compared directly. Measuring the gap the other way round would give a
    smaller number for the same difference -- A exceeding B by 10% is B falling short of A by
    9.09% -- so the convention has to be stated rather than inferred. `_ratio_gap` is symmetric,
    so where B is cheapest, as it is at every point swept here, these equal (C - B)/B and
    (A - B)/B exactly; the sign is carried by naming which pipeline is dearer, not by the formula.
    """
    def gaps(d):
        r = funnel({**p, "dft_cost_per_candidate": d})["pipelines"]
        o = {k: r[k]["outputs"]["experimentally_validated"] for k in ("A", "B", "C")}
        cb = o["B"]["usd_per"]
        return {"dft": d,
                "CB": an._ratio_gap(o["C"]["usd_per"], cb),
                "AB": an._ratio_gap(o["A"]["usd_per"], cb),
                "b_cheapest": cb <= min(o[k]["usd_per"] for k in ("A", "B", "C")),
                "b_compute_share": o["B"]["compute_usd_per"] / cb}

    rows = [gaps(d) for d in points]

    def crossing(key, target, lo=1.0, hi=20000.0):
        """DFT cost at which the comparator first reaches target. None if never within range."""
        if gaps(hi)[key] < target:
            return None
        for _ in range(80):
            mid = (lo + hi) / 2
            if gaps(mid)[key] < target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    cross = {key: {t: crossing(key, t) for t in targets} for key in ("CB", "AB")}
    return {"rows": rows, "crossings": cross, "targets": targets}


def threshold_coefficients(p, probe=(10.0, 1000.0), check=(3.0, 30.0, 54.5, 200.0, 500.0, 2000.0),
                           targets=(0.05, 0.10, 0.20)):
    """Unrounded coefficients of c0_i(d) = alpha_i d + beta_i, with residuals and root comparison.

    Section 5.5 prints these to three or four figures. The claim that the relation is affine to
    machine precision is a claim about THESE values, not about the printed ones: substituting the
    rounded coefficients into the closed form moves d* by a fraction of a core-hour, which is why
    the printed d* and the model's numerical root agree to the displayed digits but not exactly.
    This function is the archive for the unrounded values, so a reader can reproduce either.

    alpha and beta are recovered from two probe points, so by construction the relation passes
    through both; the residuals at `check` are the actual test of affinity, and `check` extends
    past the swept range so the fit is not only validated where it was fitted.

    For each target tau the closed form

        d*(tau) = (tau*b + (1+tau)*beta_B - beta_C) / (alpha_C - (1+tau)*alpha_B)

    is reported next to the model's bisected root. A positive denominator is necessary but NOT
    sufficient for a usable crossing: the solution must also be nonnegative and inside the
    physically meaningful domain d >= 0. A negative d* with a positive denominator means the gap
    already exceeds tau at zero DFT cost, so there is no crossing to report, and the formula
    returns a number that must be discarded rather than quoted. `usable` records that test.
    """
    def c0(d):
        r = funnel({**p, "dft_cost_per_candidate": d})["pipelines"]
        out = {}
        for key in ("A", "B", "C"):
            pl = r[key]
            o = pl["outputs"]["experimentally_validated"]
            verdicts = next(s["surviving"] for s in pl["stages"] if s["stage"] == "DFT check")
            out[key] = o["compute_usd_per"] * o["count"] / verdicts
        return out

    lo, hi = probe
    a, b = c0(lo), c0(hi)
    alpha = {k: (b[k] - a[k]) / (hi - lo) for k in ("A", "B", "C")}
    beta = {k: a[k] - alpha[k] * lo for k in ("A", "B", "C")}

    residuals = []
    for d in check:
        act = c0(d)
        for k in ("A", "B", "C"):
            pred = alpha[k] * d + beta[k]
            residuals.append({"dft_core_h": d, "pipeline": k, "predicted_usd": pred,
                              "model_usd": act[k], "abs_usd": pred - act[k],
                              "relative": (pred - act[k]) / act[k] if act[k] else 0.0})
    worst = max(abs(r["relative"]) for r in residuals)

    bill = p["synth_recipes_per_target"] * synthesis_cost_per_attempt(p)["usd"]
    sweep = dft_threshold_sweep(p, points=(54.5,), targets=targets)
    roots = {}
    for tau in targets:
        den = alpha["C"] - (1 + tau) * alpha["B"]
        closed = ((tau * bill + (1 + tau) * beta["B"] - beta["C"]) / den) if den else None
        solved = sweep["crossings"]["CB"][tau]
        roots[tau] = {
            "closed_form": closed,
            "numerical_root": solved,
            "denominator": den,
            "usable": bool(den > 0 and closed is not None and closed >= 0),
            "relative_gap": (abs(closed - solved) / solved) if (closed and solved) else None,
        }
    # Rounding cost: the same roots recomputed from the coefficients as printed in Section 5.5.
    shown = {"alpha": {k: round(alpha[k], 3) for k in alpha},
             "beta": {"A": round(beta["A"], 4), "B": round(beta["B"], 4), "C": round(beta["C"], 3)}}
    rounded_roots = {}
    for tau in targets:
        den = shown["alpha"]["C"] - (1 + tau) * shown["alpha"]["B"]
        rounded_roots[tau] = (((tau * bill + (1 + tau) * shown["beta"]["B"] - shown["beta"]["C"]) / den)
                              if den else None)
    return {"probe_points_core_h": list(probe), "synthesis_bill_usd": bill,
            "alpha_usd_per_core_h": alpha, "beta_usd": beta, "as_printed": shown,
            "residuals": residuals, "worst_relative_residual": worst,
            "roots": roots, "roots_from_printed_coefficients": rounded_roots,
            "alpha_ratio_C_over_B": alpha["C"] / alpha["B"]}


def upstream_per_target(p, dft=None):
    """c0_i: upstream compute expenditure per candidate reaching synthesis, by pipeline.

    This is the quantity the pipelines differ in. Everything downstream of the DFT gate -- recipes
    per target, cost per attempt, synthesis success -- is shared across pipelines in the base
    model, which is the assumption Section 5.5 calls the primary threat to validity.
    """
    q = p if dft is None else {**p, "dft_cost_per_candidate": dft}
    r = funnel(q)["pipelines"]
    out = {}
    for k in ("A", "B", "C"):
        pl = r[k]
        o = pl["outputs"]["experimentally_validated"]
        verdicts = next(s["surviving"] for s in pl["stages"] if s["stage"] == "DFT check")
        out[k] = o["compute_usd_per"] * o["count"] / verdicts
    return out


def synthesis_decision_boundaries(p, points=(3, 10, 30, 54.5, 100, 200, 500, 1000),
                                  material=MATERIAL):
    """How large a pipeline-specific synthesis difference would overturn the cost ordering?

    The base model assumes synthesis success S, recipes per target r and cost per attempt a do not
    depend on how a candidate was found, which makes level-2 cost (c0_i + ra)/S and leaves the
    pipelines differing only through c0. Relaxing that assumption gives the general ratio

        C_i/C_j = [(c0_i + r_i a_i) / (c0_j + r_j a_j)] * (S_j / S_i)

    and the question a reader who rejects the shared-synthesis assumption actually has is not
    "might it fail" but "how far would it have to fail to matter". Each boundary below is the
    value of one relaxed quantity at which two pipelines cost the same, with the others held
    shared. They are break-even solves on the model, not measurements: no source gives any of
    these differences, so every boundary is a hypothetical and is labelled as one.

    success_ratio[(i, j)]  S_i/S_j at which C_i = C_j, with r and a shared. From the ratio above,
      this is just (c0_i + ra)/(c0_j + ra): pipeline i must convert its candidates into materials
      this many times more often to pay for its extra compute.

    extra_recipes[(i, j)]  how many MORE recipes per target pipeline j would have to run, with S
      and a shared, before its cost advantage over i disappears: (c0_i - c0_j)/a. Reported also as
      a share of the baseline recipe count, which is what makes it interpretable.

    attempt_ratio[(i, j)]  a_j/a_i at which C_i = C_j with S and r shared.
    """
    a = synthesis_cost_per_attempt(p)["usd"]
    r = p["synth_recipes_per_target"]
    s_base = p["synth_success_unconditional"]
    bill = r * a
    rows = []
    for d in points:
        c0 = upstream_per_target(p, d)
        row = {"dft": d, "c0": dict(c0), "bill": bill}
        for i, j in (("C", "B"), ("A", "B"), ("C", "A")):
            q_i, q_j = c0[i] + bill, c0[j] + bill
            row[f"success_{i}{j}"] = q_i / q_j
            row[f"recipes_{i}{j}"] = (c0[i] - c0[j]) / a
            row[f"recipes_share_{i}{j}"] = (c0[i] - c0[j]) / a / r
            row[f"attempt_{i}{j}"] = (q_i - c0[j]) / bill if bill else float("nan")
            # PARITY is not MATERIALITY. Parity is where the two cost the same; a slightly larger
            # difference reverses the ranking while leaving them nearly equal. The paper's own
            # materiality standard is a 10% gap on the max/min convention, which needs a much
            # larger difference. Both are reported because they answer different questions, and
            # revision 13 conflated them.
            lo, hi = (q_i / q_j) / (1 + material), (q_i / q_j) * (1 + material)
            row[f"success_{i}{j}_mat_lo"] = lo      # below this, i costs >10% more than j
            row[f"success_{i}{j}_mat_hi"] = hi      # above this, i costs >10% less than j
            # extra recipes in j that make j cost (1+material) times i
            row[f"recipes_{i}{j}_mat"] = ((1 + material) * q_i - c0[j]) / a - r
            row[f"recipes_share_{i}{j}_mat"] = (((1 + material) * q_i - c0[j]) / a - r) / r
            # An algebraic boundary is not automatically a feasible probability: the ratio is
            # usable only while the implied success RATE stays within [0, 1]. The admissible
            # ratio ceiling is 1/S, so a boundary above it cannot be reached by any real
            # synthesis campaign at this baseline, however the algebra reads.
            row[f"feasible_{i}{j}"] = s_base * (q_i / q_j) <= 1.0
            row[f"feasible_{i}{j}_mat_hi"] = s_base * hi <= 1.0
            row[f"implied_S_{i}{j}"] = s_base * (q_i / q_j)
        rows.append(row)
    return {"rows": rows, "attempt_usd": a, "recipes": r, "bill": bill,
            "s_base": s_base, "max_feasible_ratio": 1.0 / s_base}


def boundary_sensitivity(p, dft=54.5):
    """The two boundaries at base, under the inputs the paper grades as least secure.

    Purity and compute price are what set c0, so they are what move the boundaries. Each variant
    changes one input and re-solves; the point is whether the boundary stays small enough that the
    shared-synthesis assumption remains the binding one.
    """
    a = synthesis_cost_per_attempt(p)["usd"]
    r = p["synth_recipes_per_target"]
    # Generative purity cannot be pushed far below its measured 3.8%: the filter's pass fraction
    # is prevalence x recall / purity, and at the generative pool's 3.0% prevalence and recall
    # 0.76 a purity under about 2.3% implies a pass fraction above one. funnel() raises on it, so
    # the downward variant is the largest the model admits rather than an arbitrary halving.
    variants = [
        ("base", p),
        ("generative purity at pool purity, 15.2%", {**p, "gen_filter_purity": p["pool_filter_purity"]}),
        ("generative purity at 2.4%, near the feasibility floor",
         {**p, "gen_filter_purity": 0.024}),
        ("compute price 10x", {**p, "price_per_core_hour": p["price_per_core_hour"] * 10}),
        ("compute price 100x", {**p, "price_per_core_hour": p["price_per_core_hour"] * 100}),
        ("DFT cost at the span top, 1,000 core-h", p),
    ]
    out = []
    for name, q in variants:
        d = 1000.0 if "span top" in name else dft
        c0 = upstream_per_target(q, d)
        bill = r * synthesis_cost_per_attempt(q)["usd"]
        ratio = (c0["C"] + bill) / (c0["B"] + bill)
        s_base = q["synth_success_unconditional"]
        out.append({
            "variant": name,
            "success_CB": ratio,
            "implied_S_C": s_base * ratio,
            "feasible": s_base * ratio <= 1.0,
            "recipes_AB": (c0["A"] - c0["B"]) / a,
            "recipes_share_AB": (c0["A"] - c0["B"]) / a / r,
        })
    return out


def threshold_distribution(doc, n=2000, seed=None, targets=(0.05, 0.10, 0.20)):
    """The DFT-cost crossing solved separately inside each Monte Carlo draw.

    Section 5.5 reports a crossing computed with every other parameter at base. That is one number
    from one parameter set, and it is NOT the same object as the share of draws whose verification
    cost exceeds it: the crossing itself moves draw to draw, because it depends on the synthesis
    expenditure r*a and on the compute coefficients, all of which are drawn. A reviewer asked for
    the moving threshold rather than the single value, so this solves

        d*(tau) = (tau*b + (1+tau)*beta_B - beta_C) / (alpha_C - (1+tau)*alpha_B)

    inside each draw, using that draw's own b, alpha and beta. The relation is affine in d, so the
    coefficients are recovered exactly from two evaluations per draw rather than by bisection.

    Returns the distribution of d* per target, and the share of draws for which no crossing exists
    in the domain -- either the denominator is nonpositive, or the solution is negative, meaning
    the gap already exceeds tau at zero verification cost.
    """
    from src.sampling import sampler
    import random as _r

    rng = _r.Random(doc["monte_carlo"]["seed"] if seed is None else seed)
    draw = sampler(doc)
    out = {t: [] for t in targets}
    unusable = {t: 0 for t in targets}
    drawn = 0
    while drawn < n:
        q, _info = draw(rng)
        try:
            c_lo = upstream_per_target(q, 10.0)
            c_hi = upstream_per_target(q, 1000.0)
            bill = q["synth_recipes_per_target"] * synthesis_cost_per_attempt(q)["usd"]
        except ValueError:
            continue
        drawn += 1
        alpha = {k: (c_hi[k] - c_lo[k]) / 990.0 for k in ("A", "B", "C")}
        beta = {k: c_lo[k] - alpha[k] * 10.0 for k in ("A", "B", "C")}
        for tau in targets:
            den = alpha["C"] - (1 + tau) * alpha["B"]
            if den <= 0:
                unusable[tau] += 1
                continue
            d = (tau * bill + (1 + tau) * beta["B"] - beta["C"]) / den
            if d < 0:
                unusable[tau] += 1
            else:
                out[tau].append(d)
    res = {"n": drawn, "targets": list(targets), "unusable": unusable, "quantiles": {}}
    for tau in targets:
        v = sorted(out[tau])
        if not v:
            res["quantiles"][tau] = None
            continue
        def q_(f):
            return v[min(len(v) - 1, max(0, int(round(f * (len(v) - 1)))))]
        res["quantiles"][tau] = {"p5": q_(0.05), "p25": q_(0.25), "p50": q_(0.50),
                                 "p75": q_(0.75), "p95": q_(0.95), "n": len(v)}
    return res


def joint_boundary_region(p, ratios=(0.90, 0.95, 1.00, 1.05, 1.10, 1.20), material=MATERIAL):
    """The joint condition on a success-ratio by recipe-ratio grid, for C against B.

    The one-at-a-time boundaries of Section 5.6 are interpretable but are not a joint robustness
    region: combinations of smaller differences can cross the materiality threshold before either
    individual boundary is reached. This evaluates the full ratio

        C_C/C_B = [(c0_C + r_C a)/(c0_B + r a)] * (S_B/S_C)

    over a grid of (S_C/S_B, r_C/r_B), and reports the gap at each node together with whether the
    implied success rate stays a probability at the baseline rate.
    """
    a = synthesis_cost_per_attempt(p)["usd"]
    r = p["synth_recipes_per_target"]
    s_base = p["synth_success_unconditional"]
    c0 = upstream_per_target(p)
    grid = []
    for s_ratio in ratios:
        row = []
        for r_ratio in ratios:
            q_c = c0["C"] + r * r_ratio * a
            q_b = c0["B"] + r * a
            gap = an._ratio_gap(q_c / s_ratio, q_b)
            row.append({"s_ratio": s_ratio, "r_ratio": r_ratio, "gap": gap,
                        "material": gap > material,
                        "feasible": s_base * s_ratio <= 1.0})
        grid.append(row)
    return {"ratios": list(ratios), "grid": grid, "material": material}


def chemistry_sweep_of_w(p, cells):
    """Level-1 cost across the chemistry-resolved range of the cross-functional flip rate.

    The flip rate w is not one number: it varies by chemical family. A companion audit of the
    same GNoME release, holding element count fixed, finds disjoint composition cells running from
    4.0% to 30.7%. Level 1 is defined per cross-functionally robust prediction, so it carries a
    1/(1 - w) factor and inherits that spread directly; level 2 does not, because w cancels there.

    `cells` is a list of (label, rate) read from the parameter file, so the range is sourced in one
    place rather than typed into this function.
    """
    rows = []
    for label, w in cells:
        r = funnel({**p, "dft_wrong_verdict_frac": w})
        l1 = {x: r["pipelines"][x]["outputs"]["dft_confirmed_stable"]["usd_per"] for x in an.PIPELINES}
        l2 = {x: r["pipelines"][x]["outputs"]["experimentally_validated"]["usd_per"] for x in an.PIPELINES}
        rows.append({"label": label, "w": w, "l1": l1, "l2": l2})
    lo, hi = min(rows, key=lambda r: r["w"]), max(rows, key=lambda r: r["w"])
    return {"rows": rows,
            "l1_ratio": hi["l1"]["B"] / lo["l1"]["B"],
            "l2_ratio": max(r["l2"]["B"] for r in rows) / min(r["l2"]["B"] for r in rows),
            "lo": lo, "hi": hi}


def identification_tier_spread(doc):
    """How the reading spread moves when phase identification is priced at each reading's own tier.

    The three readings differ in how strictly they judge that a target phase was made, and a
    stricter determination costs more per sample. The model charges ONE identification tier to all
    three, which is internally inconsistent: it adopts a strict reading's low success count while
    paying the lenient reading's identification bill.

    No source prices a refinement-grade phase determination, so we do not invent one. Instead we
    bound the effect using the three tiers the fee schedules already supply -- self-use, internal
    service and external service -- and report the reading spread under the tier assignment that
    widens it most, the one that narrows it most, and the uniform tier the model actually uses.
    The assignment is an assumption either way; the bound is not.
    """
    import copy

    rec = next(r for r in doc["parameters"] if r["name"] == "synth.xrd_cost_per_sample")
    tiers = {"self_use": rec["low"], "internal": rec["base"], "external": rec["high"]}
    lvl = "experimentally_validated"

    def at(tier_usd):
        d2 = copy.deepcopy(doc)
        next(r for r in d2["parameters"] if r["name"] == "synth.xrd_cost_per_sample")["base"] = tier_usd
        return {n: v["costs"][lvl]["B"] for n, v in an.scenarios(d2).items()}

    by_tier = {name: at(usd) for name, usd in tiers.items()}
    uniform = by_tier["internal"]
    cheap, dear = min(uniform, key=uniform.get), max(uniform, key=uniform.get)
    # Widest: the dearest reading pays the dearest tier, the cheapest reading the cheapest tier.
    widest = by_tier["external"][dear] / by_tier["self_use"][cheap]
    # Narrowest: the reverse assignment.
    narrowest = by_tier["self_use"][dear] / by_tier["external"][cheap]
    return {"tiers": tiers, "by_tier": by_tier, "uniform_factor": max(uniform.values()) / min(uniform.values()),
            "widest_factor": widest, "narrowest_factor": narrowest,
            "level_move_up": by_tier["external"][cheap] / uniform[cheap] - 1,
            "level_move_down": by_tier["self_use"][cheap] / uniform[cheap] - 1,
            "cheapest_reading": cheap, "dearest_reading": dear}


def boundaries_section(p):
    """Section 5.8: how far the shared-synthesis assumption has to fail before it matters."""
    b = synthesis_decision_boundaries(p)
    rows = [[f"{r['dft']:,.1f}".rstrip("0").rstrip("."),
             f"{r['success_CB']:.3f}x", f"{(r['success_CB'] - 1):.1%}",
             f"{r['success_CB_mat_lo']:.3f}-{r['success_CB_mat_hi']:.3f}",
             f"{r['recipes_share_AB']:.2%}", f"{r['recipes_share_AB_mat']:.2%}"] for r in b["rows"]]
    table = md_table(["DFT core-h per candidate", "S_C/S_B for C-B parity", "i.e. C better by",
                      f"S_C/S_B keeping C-B within {MATERIAL:.0%}",
                      "Extra recipes in B for B-A parity", f"and for B {MATERIAL:.0%} dearer than A"],
                     rows)
    srows = [[v["variant"], f"{v['success_CB']:.3f}x",
              f"{v['implied_S_C']:.1%}" + ("" if v["feasible"] else " (infeasible)"),
              f"{v['recipes_share_AB']:.2%}"] for v in boundary_sensitivity(p)]
    stable = md_table(["Variant", "S_C/S_B for parity", "implied S_C",
                       "Extra recipes, share of baseline"], srows)
    note = ("\n\nPARITY IS NOT MATERIALITY. The parity columns say where two pipelines cost the same, so a "
            "slightly larger difference reverses their ranking while leaving them nearly equal in cost. The "
            f"materiality columns say where the gap reaches {MATERIAL:.0%}, the standard used everywhere else in "
            "these results, and they require a much larger difference. The success columns compare C against B; "
            "the recipe columns compare B against A. They are different pairs and different units, and are not "
            "interchangeable measures of one assumption failing.\n\nAll are break-even solves on the model with "
            "every other quantity held shared, not measurements: no source reports a pipeline-specific synthesis "
            "difference, so each figure is the size a hypothetical difference would have to reach.\n\n")
    return table + note + stable


def key_numbers(doc, p, s1, mc, summ, scen, kill, mc_ret, tor):
    """Formatted numbers the paper draft quotes, written to results/key_numbers.json (the draft's single source)."""
    P = an.PIPELINES
    l1, l2 = s1["l1"], [o["usd_per"] for o in s1["l2"]]
    k = {}
    # Evidence-grade census. Generated because 4.1 and Limitation 9 state these counts, and an
    # earlier version of the manuscript claimed three parameters were graded `missing` when the
    # parameter file had one -- a drift that rereading never caught because nothing checked it.
    # Span-to-grade examples quoted in 4.1. Generated because the sentence previously asserted a
    # grade the record does not carry -- it called dft.cost_per_candidate `published` when it is
    # `derived` -- and nothing checked the claim against the file it describes.
    _r = records(doc)
    for _n, _tag in (("synth.success_unconditional", "success"),
                     ("synth.xrd_cost_per_sample", "xrd"),
                     ("dft.cost_per_candidate", "dft")):
        _rec = _r[_n]
        k[f"span_ratio_{_tag}"] = f"{float(_rec['high']) / float(_rec['low']):.0f}"
        k[f"span_grade_{_tag}"] = str(_rec.get("evidence_grade"))
    _grades = collections.Counter(r.get("evidence_grade") for r in records(doc).values())
    k["grade_total"] = f"{sum(_grades.values()):,}"
    for _g, _n in _grades.items():
        k[f"grade_{_g}"] = f"{_n:,}"
    for i, x in enumerate(P):
        k[f"l1_{x}"] = money(l1[x])
        k[f"l2_{x}"] = money(l2[i])
        k[f"l2_compute_{x}"] = money(s1["l2"][i]["compute_usd_per"])
        k[f"l2_synthesis_{x}"] = money(s1["l2"][i]["synthesis_usd_per"])
        k[f"l3_{x}"] = money(s1["out"][x]["validated_new"]["usd_per"])
    k["l1_ratio_A_B"] = f"{l1['A'] / l1['B']:.2f}"
    k["l1_B_cheaper_pct"] = f"{1 - l1['B'] / l1['A']:.0%}"
    k["l1_ratio_C_B"] = f"{l1['C'] / l1['B']:.1f}"
    # The source prints the generative pool's filtered stability as a RANGE spanning two models and
    # does not assign either endpoint in its main text. Run the full model at both ends rather than
    # approximating the ratio by purity alone: the conclusion about materiality is not the same at
    # the two ends, so quoting one endpoint hides a sign change.
    for tag, purity in (("lo", 0.038), ("hi", 0.088)):
        rr = funnel({**p, "gen_filter_purity": purity})
        o1 = {x: rr["pipelines"][x]["outputs"]["dft_confirmed_stable"]["usd_per"] for x in P}
        o2 = {x: rr["pipelines"][x]["outputs"]["experimentally_validated"]["usd_per"] for x in P}
        k[f"genrange_{tag}_purity"] = f"{purity:.1%}"
        k[f"genrange_{tag}_l1_C"] = money(o1["C"])
        k[f"genrange_{tag}_l1_ratio"] = f"{o1['C'] / o1['B']:.2f}"
        k[f"genrange_{tag}_l2_C"] = money(o2["C"])
        k[f"genrange_{tag}_l2_gap"] = f"{an._ratio_gap(o2['C'], o2['B']):.1%}"
        k[f"genrange_{tag}_l2_material"] = "yes" if an._ratio_gap(o2["C"], o2["B"]) > MATERIAL else "no"
    base_span = s1["span"][1]
    k["l2_spread_base"] = f"{base_span['spread']:.2f}"
    k["l2_spread_base_pct"] = f"{base_span['spread'] - 1:.0%}"
    k["l2_spread_high"] = f"{s1['span'][2]['spread']:.2f}"
    for r in s1["span"]:
        n = r["level"]
        k[f"span_{n}_l1"] = " / ".join(money(v) for v in r["l1"])
        k[f"span_{n}_l2"] = " / ".join(money(v) for v in r["l2"])
        k[f"span_{n}_spread"] = f"{r['spread']:.2f}"
        k[f"span_{n}_share"] = (f"{r['share_lo']:.0%}" if round(r['share_lo'], 2) == round(r['share_hi'], 2)
                                else f"{r['share_lo']:.0%}–{r['share_hi']:.0%}")
    comp_share = [o["compute_usd_per"] / o["usd_per"] for o in s1["l2"]]
    for r in s1["span"]:
        for i, x in enumerate(P):
            k[f"span_{r['level']}_l1_{x}"] = money(r["l1"][i])
            k[f"span_{r['level']}_l2_{x}"] = money(r["l2"][i])
        k[f"span_{r['level']}_share_lo"] = f"{r['share_lo']:.0%}"
        k[f"span_{r['level']}_share_hi"] = f"{r['share_hi']:.0%}"
    k["compute_share_lo"], k["compute_share_hi"] = f"{min(comp_share):.0%}", f"{max(comp_share):.0%}"
    k["synthesis_share_base"] = k["span_base_share"]
    parts = s1["att"]["parts"]
    k["attempt"] = money(s1["att"]["usd"])
    # Every component, not a subset: 3.5 prints the full breakdown, and the two that were missing
    # here (crucible, other consumables) were the two the audit could not check.
    for name in ("xrd", "furnace", "labour", "tuition", "precursors"):
        k[f"attempt_{name}"] = money(parts[name])
    k["attempt_crucible"] = money(parts["crucible"])
    k["attempt_other_consumables"] = money(parts["other consumables"])
    k["attempt_indirect"] = money(parts["indirect (F&A)"])
    # The base the indirect rate is applied over, and the term it replaced. 4.5 quotes both.
    _fa_base = s1["att"]["usd"] - parts["indirect (F&A)"]
    k["attempt_fa_base"] = money(_fa_base)
    k["attempt_fa_base_2dp"] = f"${_fa_base:,.2f}"   # 4.5 prints the unrounded base
    _mtdc_parts = synthesis_cost_per_attempt({**p, "indirect_base": "mtdc"})["parts"]
    k["attempt_indirect_mtdc"] = money(_mtdc_parts["indirect (F&A)"])
    k["indirect_rate"] = f"{s1['rate']:.0%}"
    for b, tag in zip(s1["bases"], ("bench", "funder", "funder_fees_in")):
        k[f"basis_{tag}_attempt"] = money(b["attempt"])
        k[f"basis_{tag}_l2"] = " / ".join(money(v) for v in b["l2"])
    for b, tag in zip(s1["bases"], ("bench", "funder", "funder_fees_in")):
        for i, x in enumerate(P):
            k[f"basis_{tag}_l2_{x}"] = money(b["l2"][i])
    for name in ("xrd", "furnace", "labour", "tuition"):
        k[f"attempt_{name}_r"] = f"${parts[name]:,.0f}"
    k["attempt_indirect_r"] = f"${parts['indirect (F&A)']:,.0f}"
    rr = s1["rate_rec"]
    k["indirect_rate_high"], k["indirect_rate_low"] = f"{rr['high']:.0%}", f"{rr['low']:.0%}"
    # Three distinct variants. These were conflated before 2026-10-11: "at_negotiated" used the
    # record's high value, which the same repair had changed from 0.58 to 0.45, so a row labelled
    # 58% was reporting 45%. They are now computed and named separately.
    hi = funnel({**p, "synth_indirect_rate": rr["high"]})           # 45%, top of the EFFECTIVE range
    neg = funnel({**p, "synth_indirect_rate": 0.58})                # 58%, the NEGOTIATED average
    mtdc = funnel({**p, "indirect_base": "mtdc"})                   # 42% on the narrowed base
    for tag, run in (("high_effective", hi), ("negotiated", neg), ("mtdc", mtdc)):
        ll = [o["usd_per"] for o in _l2(run)]
        k[f"attempt_at_{tag}"] = money(run["unit_costs"]["synthesis_attempt"]["usd"])
        k[f"l2_B_at_{tag}"] = money(ll[1])
        k[f"{tag}_l2_rise_pct"] = f"{ll[1] / l2[1] - 1:.0%}"
        for i, x in enumerate(P):
            k[f"l2_{x}_at_{tag}"] = money(ll[i])
    k["basis_move_pct"] = f"{s1['bases'][2]['l2'][0] / s1['bases'][0]['l2'][0] - 1:.0%}"
    # Chemistry-resolved flip rate: a range on level 1 only, since w cancels from level 2.
    _wrec = records(doc)["dft.wrong_verdict_chemistry_cells"]
    _wsweep = chemistry_sweep_of_w(p, [("lowest cell", _wrec["low"]),
                                       ("companion global rate", _wrec["base"]),
                                       ("stage-1 base", p["dft_wrong_verdict_frac"]),
                                       ("highest cell", _wrec["high"])])
    for row in _wsweep["rows"]:
        tag = row["label"].replace(" ", "_").replace("-", "_")
        k[f"wchem_{tag}_rate"] = f"{row['w']:.1%}"
        k[f"wchem_{tag}_l1_B"] = money(row["l1"]["B"])
    k["wchem_lo_rate"] = f"{_wsweep['lo']['w']:.1%}"
    k["wchem_hi_rate"] = f"{_wsweep['hi']['w']:.1%}"
    k["wchem_l1_ratio"] = f"{_wsweep['l1_ratio']:.2f}"
    k["wchem_l1_spread_pct"] = f"{_wsweep['l1_ratio'] - 1:.0%}"
    k["wchem_l2_ratio"] = f"{_wsweep['l2_ratio']:.2f}"
    k["wchem_spread_pp"] = f"{(_wsweep['hi']['w'] - _wsweep['lo']['w']) * 100:.1f}"
    # A.2's joint boundary grid: 36 cells, every one of them transcribed by hand into the appendix
    # and none of them previously audited. Emitting each cell puts the whole table under the check.
    _jbr = joint_boundary_region(p)
    for _row in _jbr["grid"]:
        for _c in _row:
            _tag = f"{_c['s_ratio']:.2f}_{_c['r_ratio']:.2f}".replace(".", "p")
            _g = _c["gap"] * 100
            k[f"jbr_{_tag}"] = f"{_g:.0f}%" if _c["material"] else f"{_g:.1f}%"
    k["jbr_material_cells"] = f"{sum(c['material'] for r in _jbr['grid'] for c in r)}"
    # What the MLIP relaxations actually cost, as a share of pipeline B's level-1 compute. 5.2's
    # argument -- that the level-1 ratio between pipelines approaches their purity ratio whenever
    # DFT dominates the compute term -- rests on this being negligible, and the figure the section
    # quoted for it was wrong by more than an order of magnitude on every denominator.
    _l1_B = s1["l1"]["B"]
    _dft_only_B = (p["dft_cost_per_candidate"] * p["price_per_core_hour"]
                   / p["pool_filter_purity"] / (1 - p["dft_wrong_verdict_frac"]))
    k["mlip_usd_per_robust_B"] = f"${_l1_B - _dft_only_B:.4f}"
    k["mlip_share_of_B_l1"] = f"{(_l1_B - _dft_only_B) / _l1_B:.2%}"
    # Upstream compute per candidate reaching synthesis, which 5.4 quotes for pipeline A when it
    # walks the level-2 equation by hand.
    for x, v in upstream_per_target(p).items():
        k[f"c0_{x}"] = f"${v:,.2f}"
    # Generation's share of the generative pipeline's compute spend. 5.3 asserts it is negligible;
    # that assertion is the reason generation cost is not a lever anywhere in the paper.
    _c = funnel(p)["pipelines"]["C"]["outputs"]["experimentally_validated"]
    k["gen_share_of_C_compute"] = (
        f"{_c['gpu_h_per'] * p['price_per_gpu_hour'] / _c['compute_usd_per']:.1%}")
    # What the budget-model fallback WOULD have charged the pessimistic reading, which 5.7 quotes
    # as the size of the error avoided. Computed, not remembered.
    _rec_pes = doc["monte_carlo"]["joint"]["worldview"]["readings"]["pessimistic_leeman"]
    _s_pes = _rec_pes["success"]["k"] / _rec_pes["success"]["n"]
    _r_reported = float(_rec_pes["recipes"])
    _r_derived = recipes_for_success(_s_pes, records(doc)["synth.recipe_budget"]["base"])
    _q = {**p, "synth_success_unconditional": _s_pes}
    _cost = lambda rr: an.costs({**_q, "synth_recipes_per_target": rr})["experimentally_validated"]["B"]
    k["leeman_fallback_recipes"] = f"{_r_derived:.2f}"
    k["leeman_fallback_extra_recipes"] = f"{_r_derived - _r_reported:.2f}"
    k["leeman_fallback_inflation"] = f"{_cost(_r_derived) / _cost(_r_reported) - 1:.0%}"
    # S1's discovery acceleration factors, including the prevalence-adjusted ones. S1 printed 4.05
    # for the ion-exchange pool where the generator gives 4.01, with 5.05 (the generative pool's
    # value) sitting in the adjacent cell -- a transposition that nothing checked.
    _daf = an.enrichment(doc, p)
    k["daf_wbm_reported"] = f"{_daf['wbm']['daf_reported']:.2f}"
    for _src, _tag in (("pool", "pool"), ("gen", "gen")):
        k[f"daf_{_tag}_measured"] = f"{_daf[_src]['daf_measured']:.2f}"
        k[f"daf_{_tag}_adjusted"] = f"{_daf[_src]['daf_matbench_rates_at_this_prevalence']:.2f}"
    idt = identification_tier_spread(doc)
    k["idtier_self_use"] = money(idt["tiers"]["self_use"])
    k["idtier_internal"] = money(idt["tiers"]["internal"])
    k["idtier_external"] = money(idt["tiers"]["external"])
    k["idtier_uniform_factor"] = f"{idt['uniform_factor']:.0f}"
    k["idtier_widest_factor"] = f"{idt['widest_factor']:.0f}"
    k["idtier_narrowest_factor"] = f"{idt['narrowest_factor']:.0f}"
    k["idtier_level_up_pct"] = f"{idt['level_move_up']:.0%}"
    k["idtier_level_down_pct"] = f"{idt['level_move_down']:.0%}"
    # Extreme-to-extreme across every overhead variant the paper tabulates: direct-only is the
    # cheapest and the negotiated rate the dearest, so the span is the full range of the 4.5 table.
    #
    # Per pipeline, not just A. Section 4.5 used to quote pipeline A's 51% and then hand-type "53%
    # and 43% for B and C"; B is 53.51%, which rounds to 54, so the hand-typed figure was a
    # truncation. The same sentence's "37% move" and the following "20% below the default" were
    # also A's, unattributed, in a passage that names all three pipelines. All nine are generated
    # here so none of them can be typed.
    for _i, _nm in enumerate("ABC"):
        _variants = [s1["bases"][0]["l2"][_i], _l2(mtdc)[_i]["usd_per"], s1["bases"][2]["l2"][_i],
                     _l2(hi)[_i]["usd_per"], _l2(neg)[_i]["usd_per"]]
        _direct_only, _narrowed, _default = _variants[0], _variants[1], _variants[2]
        k[f"basis_extreme_pct_{_nm}"] = f"{max(_variants) / min(_variants) - 1:.0%}"
        k[f"basis_direct_to_default_pct_{_nm}"] = f"{_default / _direct_only - 1:.0%}"
        # stated as "below the default", so the default is the denominator here by construction
        k[f"basis_narrowed_below_default_pct_{_nm}"] = f"{1 - _narrowed / _default:.0%}"
    # Limitation 4 quoted A's spread with no pipeline named, so the range is generated for it: a
    # limitation should state the whole spread rather than one pipeline's corner of it.
    _ext = [float(k[f"basis_extreme_pct_{_n}"].rstrip("%")) for _n in "ABC"]
    k["basis_extreme_range"] = f"{min(_ext):.0f}% to {max(_ext):.0f}%"

    sw = dft_threshold_sweep(p)
    # The crossings depend on synthesis expenditure per target, not on DFT cost alone, so we
    # report them under the accounting variants the paper already carries. If a threshold were
    # an artefact of one overhead convention this is where it would show.
    for tag, q in (("direct", {**p, "synth_cost_basis": "bench"}),
                   ("mtdc", {**p, "indirect_base": "mtdc"}),
                   ("default", p),
                   ("negotiated", {**p, "synth_indirect_rate": 0.58})):
        sv = dft_threshold_sweep(q, points=(54.5,))
        k[f"xacct_{tag}_attempt"] = money(synthesis_cost_per_attempt(q)["usd"])
        for key, label in (("CB", "gen"), ("AB", "filter")):
            v = sv["crossings"][key][0.10]
            k[f"xacct_{tag}_{label}10"] = "beyond 20,000" if v is None else f"{v:,.0f}"
    for r in sw["rows"]:
        tag = f"{r['dft']:g}".replace(".", "p")
        k[f"sweep_CB_{tag}"] = f"{r['CB']:.1%}"
        k[f"sweep_AB_{tag}"] = f"{r['AB']:.1%}"
        k[f"sweep_bshare_{tag}"] = f"{r['b_compute_share']:.1%}"
    for key, label in (("CB", "gen"), ("AB", "filter")):
        for tgt, val in sw["crossings"][key].items():
            nm = f"cross_{label}_{int(tgt * 100)}pct"
            k[nm] = "never within 20,000 core-h" if val is None else f"{val:,.0f}"
    k["sweep_AB_max"] = f"{max(r['AB'] for r in sw['rows']):.1%}"
    # Section 5.8 decision boundaries: how far shared synthesis has to fail to matter.
    bd = synthesis_decision_boundaries(p)
    at_base = next(r for r in bd["rows"] if abs(r["dft"] - 54.5) < 0.6)
    at_top = next(r for r in bd["rows"] if r["dft"] >= 1000)
    k["bound_success_CB"] = f"{at_base['success_CB']:.3f}"
    k["bound_success_CB_pct"] = f"{at_base['success_CB'] - 1:.1%}"
    k["bound_success_CB_top"] = f"{at_top['success_CB']:.2f}"
    k["bound_success_CB_top_pct"] = f"{at_top['success_CB'] - 1:.0%}"
    k["bound_recipes_AB"] = f"{at_base['recipes_AB']:.3f}"
    k["bound_recipes_AB_share"] = f"{at_base['recipes_share_AB']:.2%}"
    k["bound_recipes_AB_top_share"] = f"{at_top['recipes_share_AB']:.1%}"
    k["bound_attempt_CB_pct"] = f"{at_base['attempt_CB'] - 1:.1%}"
    bs = {v["variant"]: v for v in boundary_sensitivity(p)}
    k["bound_success_CB_price100"] = f"{bs['compute price 100x']['success_CB']:.2f}"
    k["bound_recipes_AB_price100_share"] = f"{bs['compute price 100x']['recipes_share_AB']:.0%}"
    # At pool purity the ratio is NOT exactly 1: alpha matches but beta does not, because C pays a
    # generation cost B never pays. Revision 13 printed "exactly 1.000" from a rounded display.
    pool_ratio = bs["generative purity at pool purity, 15.2%"]["success_CB"]
    k["bound_success_CB_at_pool_purity"] = f"{pool_ratio:.6f}"
    k["bound_success_CB_at_pool_purity_excess"] = f"{pool_ratio - 1:.4%}"
    _tcb = threshold_coefficients(p)["beta_usd"]
    k["bound_beta_gap_CB"] = money(_tcb["C"] - _tcb["B"])
    # Parity expressed in percentage points of success, not relative percent: different units.
    S = p["synth_success_unconditional"]
    k["bound_success_S_base_pct"] = f"{S:.2%}"
    k["bound_success_S_parity_pct"] = f"{S * at_base['success_CB']:.2%}"
    k["bound_max_feasible_ratio"] = f"{bd['max_feasible_ratio']:.3f}"
    # Materiality at 5%, 10% and 20%: the 10% line is a convention, not a decision criterion.
    for m in (0.05, 0.20):
        rb = synthesis_decision_boundaries(p, points=(54.5,), material=m)["rows"][0]
        tag = f"{int(m * 100)}"
        k[f"bound_mat{tag}_lo"] = f"{rb['success_CB_mat_lo']:.3f}"
        k[f"bound_mat{tag}_hi"] = f"{rb['success_CB_mat_hi']:.3f}"
        k[f"bound_mat{tag}_recipes_share"] = f"{rb['recipes_share_AB_mat']:.1%}"
    # The crossing solved inside each draw, so the threshold carries uncertainty rather than being
    # a single number from a single parameter set.
    td = threshold_distribution(doc, n=THRESHOLD_DRAWS)
    k["thrdist_draws"] = f"{td['n']:,}"
    for m in (0.05, 0.10, 0.20):
        q = td["quantiles"][m]
        tag = f"{int(m * 100)}"
        k[f"thrdist{tag}_median"] = f"{q['p50']:,.0f}"
        k[f"thrdist{tag}_p5"] = f"{q['p5']:,.0f}"
        k[f"thrdist{tag}_p95"] = f"{q['p95']:,.0f}"
        k[f"thrdist{tag}_p25"] = f"{q['p25']:,.0f}"
    k["thrdist_no_crossing_10"] = f"{td['unusable'][0.10]}"

    def sig2(x):
        """Two significant figures, which is the precision the inputs support."""
        from math import floor, log10
        if not x:
            return "0"
        e = floor(log10(abs(x)))
        return f"{round(x, -(e - 1)):,.0f}"

    # The paper prints level-2 costs and the DFT span rounded to two significant figures, because
    # the inputs are uncertain by orders of magnitude and dollar-level precision is false. Generate
    # the rounded renderings so the audit still guards what is printed.
    def money2sf(x):
        from math import floor, log10
        if not x:
            return "$0"
        e = floor(log10(abs(x)))
        return f"${round(x, -(e - 1)):,.0f}"

    for i, x in enumerate(P):
        k[f"l2_{x}_2sf"] = money2sf(l2[i])
        k[f"l1_{x}_2sf"] = f"${l1[x]:,.0f}"
    k["l2_all_2sf"] = " / ".join(money2sf(v) for v in l2)
    k["l1_all_2sf"] = " / ".join(f"${l1[x]:,.0f}" for x in P)
    for r_ in s1["span"]:
        n_ = r_["level"]
        k[f"span_{n_}_l2_2sf"] = " / ".join(money2sf(v) for v in r_["l2"])
        k[f"span_{n_}_l1_2sf"] = " / ".join(f"${v:,.0f}" for v in r_["l1"])
    # The paper prints crossings rounded; generate the rounded form so the audit still guards it.
    for key, label in (("CB", "gen"), ("AB", "filter")):
        for tgt in (0.05, 0.10, 0.20):
            v = sw["crossings"][key][tgt]
            k[f"cross_{label}_{int(tgt * 100)}pct_2sf"] = "beyond the tested range" if v is None else sig2(v)
    k["bound_implied_S_price100"] = f"{bs['compute price 100x']['implied_S_C']:.1%}"
    k["bound_price100_feasible"] = "yes" if bs["compute price 100x"]["feasible"] else "no"
    k["bound_all_table_rows_feasible"] = ("yes" if all(r["feasible_CB"] and r["feasible_CB_mat_hi"]
                                                       for r in bd["rows"]) else "no")
    # Feasibility depends on which reading sets the baseline success rate.
    _recs = records(doc)["synth.success_unconditional"]
    k["bound_max_ratio_optimistic"] = f"{1.0 / _recs['high']:.3f}"
    k["bound_max_ratio_pessimistic"] = f"{1.0 / _recs['low']:.1f}"
    k["bound_top_mat_hi"] = f"{at_top['success_CB_mat_hi']:.3f}"
    k["bound_top_mat_hi_implied_optimistic"] = f"{_recs['high'] * at_top['success_CB_mat_hi']:.1%}"
    k["bound_success_parity_pp"] = f"{(S * at_base['success_CB'] - S) * 100:.2f}"
    # The 10% materiality band, which parity does not give.
    k["bound_mat_lo"] = f"{at_base['success_CB_mat_lo']:.3f}"
    k["bound_mat_hi"] = f"{at_base['success_CB_mat_hi']:.3f}"
    # Both endpoints are stated relative to equal success (ratio 1), signed, because the band no
    # longer straddles 1: at a base synthesis bill of one recipe per target the compute gap alone
    # exceeds 10%, so even equal synthesis performance leaves C materially dearer. An earlier
    # formulation reported the lower endpoint as "C worse by", which silently changes meaning when
    # the endpoint rises above 1.
    for end in ("lo", "hi"):
        v = at_base[f"success_CB_mat_{end}"]
        k[f"bound_mat_{end}_pct"] = f"{abs(v - 1):.1%}"
        k[f"bound_mat_{end}_dir"] = "above" if v >= 1.0 else "below"
    k["bound_mat_band_contains_equal_success"] = (
        "yes" if at_base["success_CB_mat_lo"] <= 1.0 <= at_base["success_CB_mat_hi"] else "no")
    k["bound_recipes_AB_mat"] = f"{at_base['recipes_AB_mat']:.3f}"
    k["bound_recipes_AB_mat_share"] = f"{at_base['recipes_share_AB_mat']:.2%}"
    k["bound_recipes_AB_mat_top_share"] = f"{at_top['recipes_share_AB_mat']:.2%}"
    k["bound_recipes_AB_mat_lo_share"] = f"{min(x['recipes_share_AB_mat'] for x in bd['rows']):.2%}"
    # Every row of the Section 5.6 table, so the new section is audited like the rest of the paper.
    for row in bd["rows"]:
        tag = f"{row['dft']:g}".replace(".", "p")
        k[f"bdrow_{tag}_success"] = f"{row['success_CB']:.3f}"
        k[f"bdrow_{tag}_success_pct"] = f"{row['success_CB'] - 1:.1%}"
        k[f"bdrow_{tag}_recipes"] = f"{row['recipes_AB']:.3f}"
        k[f"bdrow_{tag}_recipes_share"] = f"{row['recipes_share_AB']:.2%}"
        k[f"bdrow_{tag}_mat_lo"] = f"{row['success_CB_mat_lo']:.3f}"
        k[f"bdrow_{tag}_mat_hi"] = f"{row['success_CB_mat_hi']:.3f}"
        k[f"bdrow_{tag}_recipes_mat_share"] = f"{row['recipes_share_AB_mat']:.2%}"
    for name, v in bs.items():
        tag = (name.split(",")[0].replace(" ", "_").replace("%", "pct")
               .replace("1,000", "1000").lower())
        k[f"bdsens_{tag}_success"] = f"{v['success_CB']:.3f}"
        k[f"bdsens_{tag}_recipes_share"] = f"{v['recipes_share_AB']:.2%}"
        k[f"bdsens_{tag}_implied_S"] = f"{v['implied_S_C']:.1%}"
        k[f"bdsens_{tag}_feasible"] = "yes" if v["feasible"] else "no"
    k["sweep_b_cheapest_everywhere"] = "yes" if all(r["b_cheapest"] for r in sw["rows"]) else "no"
    # Threshold-equation archive: unrounded coefficients, residuals, root comparison.
    tc = threshold_coefficients(p)
    for x in ("A", "B", "C"):
        k[f"thr_alpha_{x}"] = f"{tc['alpha_usd_per_core_h'][x]:.3f}"
        k[f"thr_alpha_{x}_full"] = f"{tc['alpha_usd_per_core_h'][x]:.10f}"
        k[f"thr_beta_{x}_full"] = f"{tc['beta_usd'][x]:.10f}"
    k["thr_beta_A"] = f"{tc['beta_usd']['A']:.4f}"
    k["thr_beta_B"] = f"{tc['beta_usd']['B']:.4f}"
    k["thr_beta_C"] = f"{tc['beta_usd']['C']:.3f}"
    k["thr_alpha_ratio_C_B"] = f"{tc['alpha_ratio_C_over_B']:.1f}"
    k["thr_worst_residual"] = f"{tc['worst_relative_residual']:.1e}"
    k["thr_residual_check_max_core_h"] = f"{max(r['dft_core_h'] for r in tc['residuals']):,.0f}"
    k["thr_synthesis_bill"] = money(tc["synthesis_bill_usd"])
    r10 = tc["roots"][0.10]
    k["thr_closed_10"] = f"{r10['closed_form']:.1f}"
    k["thr_numerical_10"] = f"{r10['numerical_root']:.1f}"
    k["thr_root_relgap_10"] = f"{r10['relative_gap']:.0e}"
    k["thr_denominator_10"] = f"{r10['denominator']:.3f}"
    # How much of the 10% crossing the d-independent terms account for. Near zero means the
    # crossing is near-proportional to the synthesis bill; it is a property of these parameters,
    # not an identity, so it is generated rather than asserted.
    _num10 = 0.10 * tc["synthesis_bill_usd"] + 1.10 * tc["beta_usd"]["B"] - tc["beta_usd"]["C"]
    k["thr_intercept_share_10"] = f"{abs(1.10 * tc['beta_usd']['B'] - tc['beta_usd']['C']) / _num10:.1%}"
    k["thr_printed_coeff_root_10"] = f"{tc['roots_from_printed_coefficients'][0.10]:.1f}"
    k["thr_printed_coeff_shift_10"] = f"{abs(tc['roots_from_printed_coefficients'][0.10] - r10['closed_form']):.2f}"
    # Monte Carlo and readings
    lvl = "experimentally_validated"
    med = {}
    for name in WORLDVIEW:
        xs = {x: [d["costs"][lvl][x] for d in mc["draws"] if d["worldview"] == name] for x in P}
        med[name] = {x: an.percentile(xs[x], 50) for x in P}
        k[f"reading_{name}_B"] = money(med[name]["B"])
        k[f"reading_{name}_B_interval"] = f"{money(an.percentile(xs['B'], 5))}–{money(an.percentile(xs['B'], 95))}"
    # Max over min across readings, NOT pessimistic/optimistic: the readings are named for how
    # optimistic their success reading is, and since the middle reading reports one recipe per
    # target it is now the cheapest, so "optimistic" is no longer the lower bound on cost.
    factor = {x: max(med[w][x] for w in WORLDVIEW) / min(med[w][x] for w in WORLDVIEW) for x in P}
    k["reading_factor_B"] = f"{factor['B']:.0f}"
    k["reading_factor_median"] = f"{statistics.median(factor.values()):.0f}"
    k["within_reading_max"] = f"{max(max(m.values()) / min(m.values()) for m in med.values()):.2f}"
    # Per-reading pipeline spread. These are reported individually because they are not alike: the
    # compute term is a fixed number of dollars while the synthesis bill is not, so pipeline choice
    # matters most under the reading whose synthesis bill is smallest.
    for name in WORLDVIEW:
        k[f"within_{name}_spread"] = f"{max(med[name].values()) / min(med[name].values()):.2f}"
    for lv, tag in (("dft_confirmed_stable", "l1"), ("experimentally_validated", "l2"), ("validated_new", "l3")):
        kk = kill[lv]
        k[f"kill_{tag}_p_B_lt_A"] = pct(kk["p_lt"][("B", "A")], 1)
        k[f"kill_{tag}_material_BA"] = pct(kk["p_material"][("B", "A")])
        k[f"kill_{tag}_material_BA_1dp"] = pct(kk["p_material"][("B", "A")], 1)
        # The superseded directional convention, kept so the size of the correction is visible.
        k[f"kill_{tag}_material_BA_directional"] = pct(kk["p_material_directional"][("B", "A")], 1)
        k[f"kill_{tag}_overlap_BA"] = pct(kk["overlap"][("B", "A")])
    # An overlap coefficient means nothing without the sparsity floor: what two samples from the
    # SAME distribution score at this bin count. At the floor the marginals are indistinguishable.
    for lv, tag in (("dft_confirmed_stable", "l1"), ("experimentally_validated", "l2")):
        ref = an.overlap_reference(mc, lv, bins=60, reps=OVERLAP_REPS)
        meas = kill[lv]["overlap"][("B", "A")]
        k[f"overlap_{tag}_ref_median"] = pct(ref["p50"])
        k[f"overlap_{tag}_ref_min"] = f"{ref['min']:.1%}"
        k[f"overlap_{tag}_ref_max"] = f"{ref['max']:.1%}"
        k[f"overlap_{tag}_ref_reps"] = str(ref["reps"])
        k[f"overlap_{tag}_vs_ref"] = ("below" if meas < ref["min"]
                                      else "above" if meas > ref["max"] else "inside")
    # Bin-count sensitivity of the overlap coefficient (Section 5.6 reports the 60-bin value).
    osens = an.overlap_sensitivity(mc)
    k["overlap_bin_counts"] = ", ".join(str(n) for n in osens)
    for lv, tag in (("dft_confirmed_stable", "l1"), ("experimentally_validated", "l2")):
        vals = [osens[n][lv][("B", "A")] for n in osens]
        k[f"overlap_{tag}_BA_range"] = f"{min(vals):.0%}–{max(vals):.0%}"
        k[f"overlap_{tag}_BA_span_pp"] = f"{(max(vals) - min(vals)) * 100:.1f}"
    # How the deterministic crossings of Section 5.5 relate to the material-draw shares of 5.6.
    # They are the same comparator on the same pair, but one is NOT the prior mass above the other:
    # the crossing itself moves draw to draw with attempt cost, recipes and success, so draws can be
    # material below the deterministic crossing and immaterial above it. Stating this is the point.
    dfts = [d["dft_cost"] for d in mc["draws"]]
    k["mc_dft_prior_max"] = f"{max(dfts):,.0f}"
    # The crossings come from the sweep rather than being written in: hardcoding them lets the
    # prior-mass comparison below drift silently when a parameter change moves the crossing.
    _cross = {"filter": sw["crossings"]["AB"][MATERIAL], "gen": sw["crossings"]["CB"][MATERIAL]}
    for pair, label in ((("A", "B"), "filter"), (("C", "B"), "gen")):
        crossing = _cross[label] if _cross[label] is not None else float("inf")
        mat = [d for d in mc["draws"]
               if an._ratio_gap(d["costs"][lvl][pair[0]], d["costs"][lvl][pair[1]]) > MATERIAL]
        non = [d["dft_cost"] for d in mc["draws"]
               if an._ratio_gap(d["costs"][lvl][pair[0]], d["costs"][lvl][pair[1]]) <= MATERIAL]
        md = sorted(d["dft_cost"] for d in mat)
        k[f"xp_{label}_material_share"] = pct(len(mat) / len(mc["draws"]), 1)
        k[f"xp_{label}_prior_above_crossing"] = pct(sum(x > crossing for x in dfts) / len(dfts), 1)
        k[f"xp_{label}_material_dft_min"] = f"{md[0]:,.0f}" if md else "n/a"
        k[f"xp_{label}_material_dft_median"] = f"{md[len(md) // 2]:,.0f}" if md else "n/a"
        k[f"xp_{label}_material_dft_max"] = f"{md[-1]:,.0f}" if md else "n/a"
        k[f"xp_{label}_immaterial_dft_max"] = f"{max(non):,.0f}" if non else "n/a"
    k["mc_draws"] = f"{len(mc['draws']):,}"
    k["mc_l2_B_p95"] = money(summ[lvl]["B"][95])
    k["mc_l2_B_p95_thousands"] = f"${summ[lvl]['B'][95] / 1000:,.0f},000"
    w = doc["monte_carlo"]["joint"]["worldview"]["weights"]
    k["mc_l2_B_p95_no_leeman"] = money(an.reweighted(
        mc, {"optimistic_alab": 0.5, "middle_prein": 0.5, "pessimistic_leeman": 0.0}, w, lvl, "B", 95))
    r_lo, r_hi = compute_ratio_range(p, mc_ret)
    k["returns_ratio_lo"], k["returns_ratio_hi"] = f"{r_lo:.0f}", f"{r_hi:.0f}"
    base_el = an.log_elasticities(p)
    for x in P:
        k[f"el_recipes_{x}"] = f"{base_el['recipes per target'][x]['return']:.3f}"
        k[f"el_attempt_{x}"] = f"{base_el['cost per synthesis attempt'][x]['return']:.3f}"
        k[f"el_success_{x}"] = f"{base_el['synthesis success rate'][x]['return']:.3f}"
        comp = max(base_el[n][x]["return"] for n, lv_ in an.levers().items() if lv_["group"] == "compute")
        k[f"el_compute_{x}"] = f"{comp:.3f}"
        # How many times more a synthesis lever moves level-2 cost than the best compute lever.
        # This is a ratio of cost shares, so it is generated rather than divided by hand in prose.
        k[f"el_ratio_{x}"] = f"{base_el['recipes per target'][x]['return'] / comp:.0f}"
        # The same ratio at the Monte Carlo medians, which 5.8 quotes beside the deterministic one.
        # Generated rather than divided by hand off the rounded table: the two estimands differ and
        # hand-division from three-decimal displays is where transcription errors start.
        _mr = mc_ret["recipes per target"][x]["median"]
        _mc_comp = max(mc_ret[n][x]["median"] for n, lv_ in an.levers().items() if lv_["group"] == "compute")
        k[f"el_mc_ratio_{x}"] = f"{_mr / _mc_comp:.0f}"
    sp = an.spot_switch(doc, p)
    k["spot_lo"] = f"{min(abs(v) for v in sp['change'].values()):.1%}"
    k["spot_hi"] = f"{max(abs(v) for v in sp['change'].values()):.1%}"
    k["spot_cpu_discount"] = f"{sp['cpu_discount']:.0%}"
    t1 = tor["dft_confirmed_stable"]["B"][0]
    t2 = tor[lvl]["B"][0]
    k["tornado_l1_share"], k["tornado_l2_share"] = pct(t1["share"], 1), pct(t2["share"], 1)
    fc = an.fixed_cost_payback(doc, p)
    k["fixed_extra_core_h"] = f"{fc['extra_fixed_core_h']:.2g}"
    k["fixed_saving_core_h"] = f"{fc['saving_core_h_per_candidate']:.1f}"
    t = an.attempt_cost_thresholds(p, COMPUTE_SHARE, SPREAD)
    k["threshold_lo"] = money(min(t["attempt_for_compute_share"].values()))
    k["threshold_hi"] = money(max(t["attempt_for_compute_share"].values()))
    # Per pipeline, because 5.9 names all three and only the extremes were generated.
    for i, x in enumerate(P):
        k[f"threshold_{x}"] = money(t["attempt_for_compute_share"][x])
        # Compute's share of level-2 cost, read off the level-2 decomposition rather than rebuilt.
        k[f"compute_share_{x}"] = f"{s1['l2'][i]['compute_usd_per'] / s1['l2'][i]['usd_per']:.1%}"
    par = an.purity_for_parity(p, "B")
    k["parity_purity"], k["parity_ratio"] = pct(par["purity"], 1), f"{par['ratio_to_measured']:.1f}"
    k["mult_2x_success_from"] = pct(p["synth_success_unconditional"])
    k["mult_2x_success_to"] = pct(s1["mult"][2.0]["filtered_success"])
    return k


def replace_block(text, name, body):
    pattern = re.compile(rf"(<!-- generated:{name}:begin -->\n).*?(<!-- generated:{name}:end -->)", re.S)
    if not pattern.search(text):
        raise ValueError(f"README has no generated:{name} block")
    return pattern.sub(lambda m: m.group(1) + body.strip() + "\n" + m.group(2), text)


MC_SEED = None


def main():
    global MC_SEED
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int)
    ap.add_argument("--no-readme", action="store_true")
    args = ap.parse_args()

    doc = load()
    p = resolve(doc)
    MC_SEED = doc["monte_carlo"]["seed"]
    tor = an.tornado(doc)
    mc = an.monte_carlo(doc, n=args.draws)
    summ = an.summarise(mc)
    scen = an.scenarios(doc)
    kill = an.kill_condition(mc, material=MATERIAL)
    mc_ret = an.returns_summary(mc)

    sections = {
        "headline": headline_section(doc, p, mc, scen, mc_ret, tor),
        "spot": spot_section(doc, p, mc_ret),
        "daf": daf_section(doc, p),
        "tornado": tornado_section(tor),
        "distributions": distributions_section(doc),
        "montecarlo": mc_section(mc, summ, scen, doc["monte_carlo"]["joint"]["worldview"]["weights"],
                                 doc["monte_carlo"]["joint"]["worldview"]["weight_sensitivity"]),
        "kill": kill_section(kill),
        "returns": returns_section(p, mc_ret),
        "breakevens": breakeven_section(doc, p),
        "boundaries": boundaries_section(p),
    }
    s1 = stage1_numbers(doc, p)
    sections.update({
        "basecase": basecase_section(s1),
        "costbasis": costbasis_section(s1),
        "dftspan": dftspan_section(s1),
        "attempt": attempt_section(s1),
        "level3": level3_section(s1),
        "multiplier": multiplier_section(s1, p),
    })

    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    report = ["# Stage 2 results", "", "Generated by `scripts/stage2.py` from `params/parameters.yaml` and `data/`.", ""]
    for title, key in (("Headline figures", "headline"), ("The only free lever", "spot"),
                       ("Discovery acceleration factor", "daf"), ("Marginal returns", "returns"),
                       ("Kill-condition check", "kill"), ("Monte Carlo and named scenarios", "montecarlo"),
                       ("Distributions", "distributions"), ("Break-evens", "breakevens"),
                       ("Synthesis decision boundaries", "boundaries"),
                       ("Tornado (summary)", "tornado")):
        report += [f"## {title}", "", sections[key], ""]
    report += ["## Tornado (full)", "", tornado_full(tor), ""]
    (out_dir / "stage2.md").write_text("\n".join(report))
    # The reconstruction package (manifests + hand-checkable worksheet) is part of the build, so
    # it cannot fall behind the parameter file.
    import subprocess
    subprocess.run([sys.executable, str(ROOT / "scripts" / "manifest.py")],
                   cwd=ROOT, check=True, capture_output=True)
    keys = key_numbers(doc, p, s1, mc, summ, scen, kill, mc_ret, tor)
    (out_dir / "key_numbers.json").write_text(json.dumps(keys, indent=1, ensure_ascii=False) + "\n")

    # Archives behind two claims the paper makes to limited precision: the affine threshold
    # coefficients (Section 5.5) and the bin-count dependence of the overlap coefficient (5.6).
    tc = threshold_coefficients(p)
    tc["roots"] = {str(t): v for t, v in tc["roots"].items()}
    tc["roots_from_printed_coefficients"] = {str(t): v for t, v in tc["roots_from_printed_coefficients"].items()}
    (out_dir / "threshold_coefficients.json").write_text(json.dumps(tc, indent=1) + "\n")
    osens = an.overlap_sensitivity(mc)
    with open(out_dir / "overlap_bin_sensitivity.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["# overlap coefficient vs bin count; bins hold normalised probabilities, not densities"])
        w.writerow(["bins", "level", "pair", "overlap"])
        for n in osens:
            for lv in an.LEVELS:
                for pr, v in osens[n][lv].items():
                    w.writerow([n, lv, f"{pr[0]} vs {pr[1]}", f"{v:.6f}"])

    with open(out_dir / "tornado.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["level", "pipeline", "parameter", "cost_at_low", "cost_at_high", "swing", "variance_share", "status"])
        for lvl in an.LEVELS:
            for k in an.PIPELINES:
                for r in tor[lvl][k]:
                    w.writerow([lvl, k, r["name"], r["low_cost"], r["high_cost"], r["swing"], r["share"], r["status"]])
    # Per-draw output is large and regenerable (same seed), so it is git-ignored; the summary is committed.
    with open(out_dir / "monte_carlo_draws.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["draw", "worldview", "dft_core_h", *(f"{SHORT[l]}_{k}" for l in an.LEVELS for k in an.PIPELINES)])
        for i, d in enumerate(mc["draws"]):
            w.writerow([i, d["worldview"], d["dft_cost"], *(d["costs"][l][k] for l in an.LEVELS for k in an.PIPELINES)])
    qs = (5, 25, 50, 75, 95)
    with open(out_dir / "monte_carlo_summary.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["# seed", MC_SEED, "draws", len(mc["draws"]), "rejected", mc["rejected"],
                    "regenerate", "uv run python scripts/stage2.py"])
        w.writerow(["worldview", "level", "pipeline", "n", *(f"p{q}" for q in qs), "mean"])
        groups = {"all (equal weights)": mc["draws"]}
        for name in WORLDVIEW:
            groups[name] = [d for d in mc["draws"] if d["worldview"] == name]
        for g, ds in groups.items():
            for lvl in an.LEVELS:
                for k in an.PIPELINES:
                    xs = [d["costs"][lvl][k] for d in ds]
                    w.writerow([g, lvl, k, len(xs), *(an.percentile(xs, q) for q in qs), sum(xs) / len(xs)])

    if not args.no_readme:
        readme = ROOT / "README.md"
        text = readme.read_text()
        for key, body in sections.items():
            text = replace_block(text, key, body)
        readme.write_text(text)

    print("\n\n".join(f"== {k}\n{v}" for k, v in sections.items()))


if __name__ == "__main__":
    main()
